from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import get_db, init_db
from models import Seller, Product, Transaction, Review, ViewHistory, Report, CURRENCIES, LANGUAGES, MAIN_CATEGORIES
from config import Config
import os
import uuid
import random
import string
import time
import io
import zipfile
import shutil
import tempfile
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import uvicorn

# === БИБЛИОТЕКИ ДЛЯ ИИ-ПРОВЕРКИ ЧЕКОВ (EASYOCR) ===
try:
    import easyocr
    from PIL import Image
    # Инициализируем читатель один раз при старте (Русский + Английский)
    reader = easyocr.Reader(['ru', 'en'], gpu=False) 
    OCR_AVAILABLE = True
    print("✅ AI Check Ready: EasyOCR loaded successfully.")
except ImportError:
    OCR_AVAILABLE = False
    print("⚠️ WARNING: easyocr or PIL not installed. Run: pip install easyocr pillow")

# === НАСТРОЙКИ БЕЗОПАСНОСТИ ===
FOUNDER_USERNAME = "Development_and_founder"
ALLOWED_ADMINS = ["Development_and_founder"]
SUSPICIOUS_THRESHOLD = 3  # Количество жалоб для статуса "Сомнительный"

ALLOWED_EXTENSIONS = {".py", ".exe", ".zip", ".pdf", ".js", ".txt", ".json", ".html", ".css", ".md"}
ALLOWED_IMAGES = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_VIDEOS = {".mp4", ".mov", ".avi"}
BRAND_KEYWORDS = ["official", "brand", "corp", "ltd", "inc", "lab", "studio", "games"]

MAX_DOWNLOADS_PER_PURCHASE = 5
LICENSE_SERVER_URL = "https://your-platform.com/api/verify-license"

init_db()
app = FastAPI(title="AI Validated Platform - Secure Core")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# === УРОВЕНЬ 1: ЗАЩИЩЕННОЕ ХРАНИЛИЩЕ ===
os.makedirs("_protected_uploads", exist_ok=True)
os.makedirs("_protected_uploads/screenshots", exist_ok=True)
os.makedirs("_protected_uploads/videos", exist_ok=True)
os.makedirs("uploads/checks", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

active_payment_codes = {}
active_sessions = {}

def get_current_user(request: Request, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions: return None
    return db.query(Seller).filter(Seller.username == active_sessions[session_id]).first()

def is_admin(user):
    return user and user.username in ALLOWED_ADMINS

def is_password_strong(password: str, username: str) -> bool:
    if len(password) < 8 or password.lower() == username.lower(): return False
    weak = ["123456", "password", "qwerty", "111111", "admin"]
    if password.lower() in weak: return False
    return True

def detect_brand(username: str, title: str) -> bool:
    text = (username + " " + title).lower()
    return any(kw in text for kw in BRAND_KEYWORDS)

def generate_payment_code():
    return str(random.randint(1000, 9999))

def ai_classify_product(title: str, description: str, filename: str) -> dict:
    text = (title + " " + description + " " + filename).lower()
    main_cat, sub_cat = "Other", "General"
    if any(x in text for x in ["python", "script", "bot", "telegram", "api", "code", "dev", "web", "html", "css", "js"]):
        main_cat = "Programming"
        if "python" in text: sub_cat = "Python"
        elif "bot" in text: sub_cat = "Bots"
        elif "web" in text: sub_cat = "Web Dev"
        elif "ai" in text: sub_cat = "AI & ML"
        else: sub_cat = "Scripts"
    elif any(x in text for x in ["chemistry", "physics", "atom", "astronomy", "space", "star", "biology", "math"]):
        main_cat = "Science"
        if "chem" in text: sub_cat = "Chemistry"
        elif "phys" in text: sub_cat = "Physics"
        elif "astro" in text: sub_cat = "Astronomy"
        else: sub_cat = "Biology"
    elif any(x in text for x in ["course", "lesson", "tutorial", "guide", "learn", "education"]):
        main_cat = "Education"
        sub_cat = "Courses" if "course" in text else "Guides"
    elif any(x in text for x in ["game", "play", "mod", "asset"]):
        main_cat = "Games"
        sub_cat = "Mods" if "mod" in text else "PC Games"

    if len(description) < 10: 
        return {"status": "failed", "reason": "Описание слишком короткое.", "main": main_cat, "sub": sub_cat, "review": False}
    return {"status": "passed", "reason": "OK", "main": main_cat, "sub": sub_cat, "review": detect_brand("", title)}

# === ИИ-ПРОВЕРКА ЧЕКОВ ===
def analyze_receipt_ai(image_bytes: bytes, expected_amount: float, expected_code: str) -> dict:
    if not OCR_AVAILABLE:
        return {"valid": True, "reason": "OCR not installed, skipping check."}

    try:
        image = Image.open(io.BytesIO(image_bytes))
        results = reader.readtext(image_bytes, detail=0)
        full_text = " ".join(results)
        full_text_lower = full_text.lower()
        
        # 1. Проверка кода
        if expected_code not in full_text:
            return {"valid": False, "reason": f"❌ Код оплаты '{expected_code}' не найден в чеке."}

        # 2. Проверка суммы
        numbers = re.findall(r'\d+[.,]?\d*', full_text.replace(' ', ''))
        amount_found = False
        for num_str in numbers:
            try:
                val = float(num_str.replace(',', '.'))
                if abs(val - expected_amount) < 2.0:
                    amount_found = True
                    break
            except ValueError:
                continue
        if not amount_found:
            return {"valid": False, "reason": f"❌ Сумма {expected_amount} не найдена в чеке."}

        # 3. Проверка статуса
        success_words = ["успешно", "executed", "completed", "success", "перевод выполнен", "оплата прошла", "done"]
        fail_words = ["ошибка", "failed", "error", "rejected", "declined", "отказ"]
        
        if any(word in full_text_lower for word in fail_words):
            return {"valid": False, "reason": "❌ Обнаружена ошибка перевода."}
        if not any(word in full_text_lower for word in success_words):
            return {"valid": False, "reason": "⚠️ Статус перевода не ясен."}

        return {"valid": True, "reason": "✅ Чек проверен ИИ."}
    except Exception as e:
        return {"valid": False, "reason": f"❌ Ошибка анализа: {str(e)}"}

# === МАРШРУТЫ ===

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.is_verified == True, Product.requires_manual_review == False).order_by(Product.created_at.desc()).limit(6).all()
    current_user = get_current_user(request, db)
    return templates.TemplateResponse("index.html", {"request": request, "products": products, "current_user": current_user, "founder_name": FOUNDER_USERNAME})

@app.get("/catalog", response_class=HTMLResponse)
async def catalog(request: Request, sort: str = Query("newest"), db: Session = Depends(get_db)):
    query = db.query(Product).filter(Product.is_verified == True, Product.requires_manual_review == False)
    if sort == "price_asc": query = query.order_by(Product.price.asc())
    elif sort == "price_desc": query = query.order_by(Product.price.desc())
    elif sort == "popular": query = query.order_by(Product.download_count.desc())
    else: query = query.order_by(Product.created_at.desc())
    
    all_products = query.all()
    catalog_data = {cat: {"subcategories": {}, "products": []} for cat in MAIN_CATEGORIES}
    for p in all_products:
        main = p.main_category if p.main_category in MAIN_CATEGORIES else "Other"
        sub = p.sub_category
        if main not in catalog_data: main = "Other"
        if sub not in catalog_data[main]["subcategories"]: catalog_data[main]["subcategories"][sub] = []
        catalog_data[main]["subcategories"][sub].append(p)
        
    current_user = get_current_user(request, db)
    return templates.TemplateResponse("catalog.html", {
        "request": request, "catalog_data": catalog_data, "main_categories": MAIN_CATEGORIES,
        "current_user": current_user, "founder_name": FOUNDER_USERNAME, "current_sort": sort
    })

@app.get("/seller/{username}", response_class=HTMLResponse)
async def seller_profile(username: str, request: Request, db: Session = Depends(get_db)):
    seller = db.query(Seller).filter(Seller.username == username).first()
    if not seller: raise HTTPException(404)
    products = db.query(Product).filter(Product.seller_id == seller.id, Product.is_verified == True).all()
    current_user = get_current_user(request, db)
    is_admin = current_user and (current_user.username == FOUNDER_USERNAME or current_user.id == seller.id)
    
    # Подсчет жалоб
    reports_count = db.query(Report).filter(Report.target_seller_id == seller.id).count()
    is_suspicious = reports_count >= SUSPICIOUS_THRESHOLD
    
    return templates.TemplateResponse("seller_profile.html", {
        "request": request, "seller": seller, "products": products, 
        "current_user": current_user, "is_admin": is_admin,
        "reports_count": reports_count, "is_suspicious": is_suspicious
    })

@app.get("/legal", response_class=HTMLResponse)
async def legal_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    return templates.TemplateResponse("legal.html", {"request": request, "current_user": current_user, "founder_name": FOUNDER_USERNAME})

@app.get("/rules", response_class=HTMLResponse)
async def rules_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    return templates.TemplateResponse("rules.html", {"request": request, "current_user": current_user, "founder_name": FOUNDER_USERNAME})

@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    return templates.TemplateResponse("about.html", {"request": request, "current_user": current_user, "founder_name": FOUNDER_USERNAME})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request): return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register_submit(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing = db.query(Seller).filter((Seller.username == username) | (Seller.email == email)).first()
    if existing: return templates.TemplateResponse("register.html", {"request": request, "error": "Занято"})
    if not is_password_strong(password, username): return templates.TemplateResponse("register.html", {"request": request, "error": "Слабый пароль"})
    seller = Seller(username=username, email=email, password_hash=password, is_early_adopter=True)
    if detect_brand(username, ""): seller.is_brand = True; seller.is_verified_buyer = False
    elif username == FOUNDER_USERNAME: seller.is_founder = True; seller.is_verified_buyer = True
    db.add(seller); db.commit()
    session_id = str(uuid.uuid4()); active_sessions[session_id] = username
    resp = RedirectResponse(url="/dashboard", status_code=303); resp.set_cookie("session_id", session_id, max_age=86400*7)
    return resp

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request): return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login_submit(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    seller = db.query(Seller).filter(Seller.username == username).first()
    if not seller or seller.password_hash != password: return templates.TemplateResponse("login.html", {"request": request, "error": "Ошибка"})
    if seller.is_banned: return templates.TemplateResponse("login.html", {"request": request, "error": "🚫 Ваш аккаунт заблокирован администрацией."})
    seller.last_login = datetime.now(timezone.utc); db.commit()
    session_id = str(uuid.uuid4()); active_sessions[session_id] = username
    resp = RedirectResponse(url="/dashboard", status_code=303); resp.set_cookie("session_id", session_id, max_age=86400*7)
    return resp

@app.get("/logout")
async def logout(request: Request):
    sid = request.cookies.get("session_id")
    if sid in active_sessions: del active_sessions[sid]
    resp = RedirectResponse(url="/", status_code=303); resp.delete_cookie("session_id")
    return resp

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/login")
    products = db.query(Product).filter(Product.seller_id == user.id).all()
    pending_sales_count = db.query(Transaction).filter(Transaction.seller_id == user.id, Transaction.status == "verification").count()
    return templates.TemplateResponse("dashboard.html", {
        "request": request, "current_user": user, "products": products, 
        "founder_name": FOUNDER_USERNAME, "pending_sales_count": pending_sales_count
    })

@app.get("/dashboard/sales", response_class=HTMLResponse)
async def my_sales(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/login")
    sales = db.query(Transaction).filter(Transaction.seller_id == user.id).order_by(Transaction.created_at.desc()).all()
    return templates.TemplateResponse("sales_dashboard.html", {
        "request": request, "current_user": user, "items": sales, "mode": "sales", "founder_name": FOUNDER_USERNAME
    })

@app.get("/dashboard/purchases", response_class=HTMLResponse)
async def my_purchases(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/login")
    purchases = db.query(Transaction).filter(Transaction.buyer_id == user.id).order_by(Transaction.created_at.desc()).all()
    return templates.TemplateResponse("sales_dashboard.html", {
        "request": request, "current_user": user, "items": purchases, "mode": "purchases", "founder_name": FOUNDER_USERNAME
    })

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/login")
    return templates.TemplateResponse("settings.html", {"request": request, "current_user": user, "currencies": CURRENCIES, "languages": LANGUAGES, "founder_name": FOUNDER_USERNAME})

@app.post("/settings")
async def update_settings(request: Request, currency: str = Form(...), language: str = Form("ru"), payout_requisites: str = Form(""), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/login")
    user.currency = currency
    user.language = language
    user.payout_requisites = payout_requisites
    db.commit()
    return RedirectResponse(url="/settings?success=1", status_code=303)

@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/login")
    return templates.TemplateResponse("upload.html", {"request": request, "current_user": user, "founder_name": FOUNDER_USERNAME})

@app.post("/upload")
async def upload_product(request: Request, title: str = Form(...), description: str = Form(...), price: float = Form(...), file: UploadFile = File(...), screenshots: List[UploadFile] = File(...), video: Optional[UploadFile] = File(None), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/login")
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS: return templates.TemplateResponse("upload.html", {"request": request, "current_user": user, "error": f"Неверный формат ({file_ext})", "founder_name": FOUNDER_USERNAME})
    ai_result = ai_classify_product(title, description, file.filename)
    if ai_result['status'] == 'failed': return templates.TemplateResponse("upload.html", {"request": request, "current_user": user, "error": f"❌ ИИ: {ai_result['reason']}", "founder_name": FOUNDER_USERNAME})
    try:
        ts = datetime.now(timezone.utc).timestamp()
        file_path = f"_protected_uploads/{ts}_{file.filename}"
        with open(file_path, "wb") as f: f.write(await file.read())
        
        saved_screenshots = []
        for img in screenshots:
            if img.filename and os.path.splitext(img.filename)[1].lower() in ALLOWED_IMAGES:
                path = f"uploads/screenshots/{ts}_{img.filename}"
                with open(path, "wb") as f: f.write(await img.read())
                saved_screenshots.append(path)
        video_path = None
        if video and video.filename and os.path.splitext(video.filename)[1].lower() in ALLOWED_VIDEOS:
            path = f"uploads/videos/{ts}_{video.filename}"
            with open(path, "wb") as f: f.write(await video.read())
            video_path = path
            
        prod = Product(seller_id=user.id, title=title, description=description, main_category=ai_result['main'], sub_category=ai_result['sub'], price=price, file_path=file_path, screenshots=saved_screenshots, demo_video_path=video_path, is_verified=not ai_result['review'], requires_manual_review=ai_result['review'], ai_check_status='passed')
        db.add(prod)
        if user.points == 0: user.points += Config.POINTS_FOR_UPLOAD
        db.commit()
        return RedirectResponse(url="/dashboard?success=1", status_code=303)
    except Exception as e: return templates.TemplateResponse("upload.html", {"request": request, "current_user": user, "error": str(e), "founder_name": FOUNDER_USERNAME})

# === НОВЫЕ МАРШРУТЫ ДЛЯ РЕДАКТИРОВАНИЯ (ЧТОБЫ РАБОТАЛ КАРАНДАШ) ===
@app.get("/product/{pid}/edit", response_class=HTMLResponse)
async def edit_product_page(pid: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: 
        return RedirectResponse(url="/login")
    
    product = db.query(Product).filter(Product.id == pid).first()
    # Проверка: товар должен существовать И принадлежать пользователю
    if not product or product.seller_id != user.id:
        raise HTTPException(404, "Товар не найден или вы не владелец")
    
    return templates.TemplateResponse("product_edit.html", {
        "request": request, 
        "product": product, 
        "current_user": user, 
        "founder_name": FOUNDER_USERNAME
    })

@app.post("/product/{pid}/edit")
async def edit_product_submit(
    pid: int, 
    request: Request, 
    title: str = Form(...), 
    description: str = Form(...), 
    price: float = Form(...), 
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user: 
        return RedirectResponse(url="/login")
    
    product = db.query(Product).filter(Product.id == pid).first()
    if not product or product.seller_id != user.id:
        raise HTTPException(404, "Товар не найден")
    
    # Обновляем данные
    product.title = title
    product.description = description
    product.price = price
    
    db.commit()
    
    # Редирект обратно в кабинет с сообщением об успехе
    return RedirectResponse(url="/dashboard?msg=updated", status_code=303)
# ==========================================================

@app.get("/product/{pid}", response_class=HTMLResponse)
async def product_detail(pid: int, request: Request, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == pid).first()
    if not p: raise HTTPException(404)
    user = get_current_user(request, db)
    
    # ИСПРАВЛЕНИЕ: Не считаем просмотр, если пользователь - автор товара
    if user and user.id != p.seller_id:
        vh = ViewHistory(user_id=user.id, product_id=p.id)
        db.add(vh)
        db.commit()
    
    reviews = db.query(Review).filter(Review.product_id == pid).order_by(Review.created_at.desc()).all()
    can_review = False
    can_report = False
    
    if user and user.id != p.seller_id:
        purchase = db.query(Transaction).filter(Transaction.buyer_id == user.id, Transaction.product_id == pid, Transaction.status == "completed").first()
        if purchase:
            can_review = True
            can_report = True
            
    return templates.TemplateResponse("product_detail.html", {
        "request": request, "product": p, "seller": p.seller, 
        "current_user": user, "founder_name": FOUNDER_USERNAME,
        "reviews": reviews, "can_review": can_review, "can_report": can_report
    })

@app.post("/product/{pid}/review")
async def add_review(pid: int, request: Request, rating: int = Form(...), comment: str = Form(""), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/login", status_code=303)
    product = db.query(Product).filter(Product.id == pid).first()
    if not product: raise HTTPException(404)
    if user.id == product.seller_id:
        return RedirectResponse(url=f"/product/{pid}?error=author_cannot_review", status_code=303)
    purchase = db.query(Transaction).filter(Transaction.buyer_id == user.id, Transaction.product_id == pid, Transaction.status == "completed").first()
    if not purchase:
        return RedirectResponse(url=f"/product/{pid}?error=only_buyers", status_code=303)

    review = Review(product_id=pid, buyer_id=user.id, rating=rating, comment=comment)
    db.add(review)
    
    all_reviews = db.query(Review).filter(Review.product_id == pid).all()
    if all_reviews:
        product.product_rating = round(sum(r.rating for r in all_reviews) / len(all_reviews), 1)
        product.review_count = len(all_reviews)
    
    seller = product.seller
    all_seller_reviews = db.query(Review).join(Product).filter(Product.seller_id == seller.id).all()
    if all_seller_reviews:
        total_score = sum((r.rating / 5.0) * 10.0 for r in all_seller_reviews)
        seller.seller_rating = round(total_score / len(all_seller_reviews), 1)
        seller.rating_count = len(all_seller_reviews)
    
    db.commit()
    return RedirectResponse(url=f"/product/{pid}#reviews", status_code=303)

# === НОВЫЙ МАРШРУТ: ОТПРАВИТЬ ЖАЛОБУ ===
@app.post("/report/seller/{seller_id}")
async def submit_report(seller_id: int, request: Request, reason: str = Form(...), comment: str = Form(""), product_id: Optional[int] = Form(None), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/login", status_code=303)
    
    target_seller = db.query(Seller).filter(Seller.id == seller_id).first()
    if not target_seller: raise HTTPException(404, "Продавец не найден")
    
    if user.username != FOUNDER_USERNAME:
        purchase = db.query(Transaction).filter(
            Transaction.buyer_id == user.id,
            Transaction.seller_id == seller_id,
            Transaction.status == "completed"
        ).first()
        if not purchase:
            raise HTTPException(403, "Жалобу могут оставить только покупатели.")

    report = Report(reporter_id=user.id, target_seller_id=seller_id, product_id=product_id, reason=reason, comment=comment)
    db.add(report)
    db.commit()
    return RedirectResponse(url=f"/seller/{target_seller.username}?msg=report_sent", status_code=303)

@app.get("/buy/{pid}", response_class=HTMLResponse)
async def buy_page(pid: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/login")
    prod = db.query(Product).filter(Product.id == pid).first()
    if not prod: raise HTTPException(404)
    if user.id == prod.seller_id:
        return RedirectResponse(url=f"/secure-download/{pid}?eula=accepted", status_code=302)
    if prod.price == 0:
        return RedirectResponse(url=f"/secure-download/{pid}?eula=accepted") 
    
    seller = prod.seller
    requisites = seller.payout_requisites if seller.payout_requisites else "РЕКВИЗИТЫ НЕ УКАЗАНЫ"
    
    current_time = time.time()
    cache_key = (user.id, pid)
    
    payment_code = ""
    if cache_key in active_payment_codes:
        cached_data = active_payment_codes[cache_key]
        if current_time < cached_data["expires"]:
            payment_code = cached_data["code"]
        else:
            del active_payment_codes[cache_key]
    
    if not payment_code:
        payment_code = generate_payment_code()
        active_payment_codes[cache_key] = {"code": payment_code, "expires": current_time + 600}
    
    return templates.TemplateResponse("buy.html", {
        "request": request, "product": prod, "current_user": user,
        "payment_code": payment_code, "seller_requisites": requisites, "seller_name": seller.username
    })

@app.post("/buy/{pid}")
async def buy_submit(pid: int, request: Request, file: UploadFile = File(...), payment_code_user: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/login")
    prod = db.query(Product).filter(Product.id == pid).first()
    if not prod: raise HTTPException(404)
    if user.id == prod.seller_id:
        raise HTTPException(403, "Вы не можете купить собственный товар.")

    image_bytes = await file.read()
    ai_result = analyze_receipt_ai(image_bytes, prod.price, payment_code_user)
    
    if not ai_result["valid"]:
        return templates.TemplateResponse("buy.html", {
            "request": request, "product": prod, "current_user": user, 
            "error": ai_result["reason"], 
            "payment_code": payment_code_user,
            "seller_requisites": prod.seller.payout_requisites, 
            "seller_name": prod.seller.username
        })

    ts = datetime.now(timezone.utc).timestamp()
    ck_path = f"uploads/checks/{ts}_{file.filename}"
    with open(ck_path, "wb") as f: f.write(image_bytes)
    
    t = Transaction(product_id=prod.id, buyer_id=user.id, seller_id=prod.seller_id, amount=prod.price, screenshot_path=ck_path, status="verification", payment_method="p2p")
    db.add(t); db.commit()
    return RedirectResponse(url="/dashboard/purchases?msg=check_sent", status_code=303)

@app.post("/sales/confirm/{tid}")
async def confirm_sale(tid: int, request: Request, db: Session = Depends(get_db)):
    seller = get_current_user(request, db)
    if not seller: return RedirectResponse(url="/login")
    t = db.query(Transaction).filter(Transaction.id == tid).first()
    if not t or t.seller_id != seller.id: raise HTTPException(403)
    if t.buyer_id == seller.id:
        raise HTTPException(403, "Нельзя подтверждать покупку у самого себя.")
    t.status = "completed"; t.paid_at = datetime.now(timezone.utc)
    seller.balance += t.amount; seller.total_earned += t.amount
    db.commit()
    return RedirectResponse(url="/dashboard/sales", status_code=303)

@app.get("/secure-download/{product_id}")
async def secure_download(product_id: int, request: Request, db: Session = Depends(get_db), eula: str = Query("")):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=403, detail="Требуется вход в систему")
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product: raise HTTPException(404, "Товар не найден")
    
    is_free = (product.price == 0)
    is_owner = (product.seller_id == user.id)
    purchase = None
    
    # Показываем EULA только если пользователь НЕ является владельцем
    if eula != "accepted" and not is_owner:
        html_content = f"""
        <!DOCTYPE html>
        <html><head><title>Security Check</title>
        <style>
            body{{font-family:sans-serif;background:#1a1a2e;color:#fff;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;}}
            .box{{background:#16213e;padding:40px;border-radius:12px;max-width:500px;text-align:center;border:1px solid #e94560;}}
            h2{{color:#e94560;}}
            .btn{{display:inline-block;margin-top:20px;padding:12px 24px;background:#e94560;color:white;text-decoration:none;border-radius:6px;font-weight:bold;}}
        </style></head><body>
        <div class='box'>
            <h2>⚠️ Юридическое предупреждение</h2>
            <p>Скачивая этот файл, вы соглашаетесь с тем, что:</p>
            <ul style='text-align:left;font-size:0.9rem;color:#ccc;'>
                <li>Файл содержит персональный водяной знак ({user.username}).</li>
                <li>Передача файла третьим лицам запрещена.</li>
                <li>При утечке ваш аккаунт будет заблокирован.</li>
            </ul>
            <a href='/secure-download/{product_id}?eula=accepted' class='btn'>Я принимаю условия и хочу скачать</a>
            <br><br><a href='/product/{product_id}' style='color:#888;'>Отмена</a>
        </div></body></html>
        """
        return HTMLResponse(content=html_content, status_code=403)

    if not is_free and not is_owner:
        purchase = db.query(Transaction).filter(
            Transaction.buyer_id == user.id,
            Transaction.product_id == product_id,
            Transaction.status == "completed"
        ).first()
        if not purchase:
            raise HTTPException(status_code=403, detail="Вы не покупали этот товар.")

    # === ГЛАВНОЕ ИЗМЕНЕНИЕ: НЕ НАКРУЧИВАЕМ СЧЕТЧИКИ ДЛЯ АВТОРА ===
    if not is_owner:
        if product.download_count > 5000:
             raise HTTPException(403, "Лимит глобальных скачиваний исчерпан.")
        product.download_count += 1
        db.commit()
    # Если владелец - просто пропускаем увеличение счетчика

    file_path = product.file_path
    if not os.path.exists(file_path):
        raise HTTPException(404, "Файл не найден на сервере")

    _, ext = os.path.splitext(file_path)
    filename = os.path.basename(file_path)
    unique_hash = uuid.uuid4().hex
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    watermark_text = f"""
# ================================================================================
# LICENSED COPY - AI VALIDATED PLATFORM
# ================================================================================
# Licensee: {user.username} (ID: {user.id})
# Email: {user.email}
# Purchase Date: {timestamp}
# Transaction ID: {purchase.id if purchase else 'OWNER_ACCESS'}
# Unique Watermark Hash: {unique_hash}
# 
# WARNING: Distribution is strictly prohibited.
# ================================================================================
"""

    license_check_code = f"""
import urllib.request
import sys
import json

def verify_license():
    try:
        req = urllib.request.Request("{LICENSE_SERVER_URL}", data=json.dumps({{"hash": "{unique_hash}", "user": "{user.id}"}}).encode(), headers={{'Content-Type': 'application/json'}})
        response = urllib.request.urlopen(req, timeout=5)
        data = json.loads(response.read())
        if not data.get('valid'):
            print("ERROR: License verification failed.")
            sys.exit(1)
    except Exception as e:
        pass

verify_license()
"""

    try:
        # Обработка текстовых файлов и скриптов
        if ext.lower() in ['.py', '.js', '.txt', '.md', '.json', '.html', '.css']:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            modified_content = watermark_text + "\n"
            if ext.lower() == '.py':
                modified_content += license_check_code + "\n\n" + content
            else:
                modified_content += content
            
            return Response(
                content=modified_content, 
                media_type="application/octet-stream",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'}
            )

        # Обработка ZIP архивов
        elif ext.lower() == '.zip':
            temp_dir = tempfile.mkdtemp()
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                license_file = os.path.join(temp_dir, "LICENSE_USER.txt")
                with open(license_file, 'w', encoding='utf-8') as f:
                    f.write(watermark_text)
                
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file.lower() in ['readme.txt', 'readme.md', 'info.txt']:
                            r_path = os.path.join(root, file)
                            with open(r_path, 'a', encoding='utf-8', errors='ignore') as f:
                                f.write(f"\n\n--- Licensed to {user.username} ({unique_hash}) ---\n")
                        
                        if file.lower().endswith('.py'):
                            f_path = os.path.join(root, file)
                            with open(f_path, 'r', encoding='utf-8', errors='ignore') as src:
                                py_content = src.read()
                            with open(f_path, 'w', encoding='utf-8') as dst:
                                dst.write(watermark_text + "\n" + license_check_code + "\n\n" + py_content)

                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                    for foldername, subfolders, filenames in os.walk(temp_dir):
                        for filename in filenames:
                            filepath = os.path.join(foldername, filename)
                            arcname = os.path.relpath(filepath, temp_dir)
                            new_zip.write(filepath, arcname)
                
                zip_buffer.seek(0)
                return Response(
                    content=zip_buffer.getvalue(),
                    media_type="application/x-zip-compressed",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'}
                )
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

        # Для бинарных файлов
        else:
            safe_filename = f"{os.path.splitext(filename)[0]}_licensed_{user.id}{ext}"
            return FileResponse(path=file_path, filename=safe_filename, media_type='application/octet-stream')

    except Exception as e:
        raise HTTPException(500, f"Error processing file: {str(e)}")

@app.post("/product/{product_id}/delete")
async def delete_product(product_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/login")
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product or product.seller_id != user.id: raise HTTPException(404)
    try:
        if os.path.exists(product.file_path): os.remove(product.file_path)
        for img in product.screenshots:
            if os.path.exists(img): os.remove(img)
        if product.demo_video_path and os.path.exists(product.demo_video_path): os.remove(product.demo_video_path)
    except: pass
    db.delete(product); db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/download/{product_id}")
async def legacy_download(product_id: int, request: Request):
    return RedirectResponse(url=f"/secure-download/{product_id}", status_code=302)

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not is_admin(user): raise HTTPException(status_code=403, detail="Доступ запрещен.")
    
    total_users = db.query(Seller).count()
    total_sales = db.query(Transaction).filter(Transaction.status == "completed").count()
    pending_reviews = db.query(Product).filter(Product.requires_manual_review == True).all()
    all_users = db.query(Seller).all()
    
    new_reports_count = db.query(Report).filter(Report.created_at > datetime.now(timezone.utc) - timedelta(days=7)).count()
    
    stats = {"users": total_users, "sales": total_sales, "pending": len(pending_reviews), "reports": new_reports_count}
    
    return templates.TemplateResponse("admin.html", {
        "request": request, "user": user, "stats": stats, 
        "pending_reviews": pending_reviews, "users": all_users, "founder_name": FOUNDER_USERNAME
    })

@app.get("/admin/reports", response_class=HTMLResponse)
async def admin_reports(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not is_admin(user): raise HTTPException(403, "Доступ запрещен")
    
    reports = db.query(Report).order_by(Report.created_at.desc()).all()
    
    suspicious_map = {}
    for r in reports:
        if r.target_seller_id not in suspicious_map:
            suspicious_map[r.target_seller_id] = {"count": 0, "seller": r.target_seller}
        suspicious_map[r.target_seller_id]["count"] += 1
        
    return templates.TemplateResponse("admin_reports.html", {
        "request": request, "user": user, "reports": reports, 
        "suspicious_map": suspicious_map, "founder_name": FOUNDER_USERNAME
    })

@app.post("/admin/ban-user/{uid}")
async def ban_and_delete_user(uid: int, request: Request, db: Session = Depends(get_db)):
    admin = get_current_user(request, db)
    if not is_admin(admin): raise HTTPException(403)
    
    target_user = db.query(Seller).filter(Seller.id == uid).first()
    if not target_user: raise HTTPException(404)
    if target_user.username == FOUNDER_USERNAME: raise HTTPException(403, "Нельзя банить Основателя!")

    user_products = db.query(Product).filter(Product.seller_id == uid).all()
    for product in user_products:
        try:
            if os.path.exists(product.file_path): os.remove(product.file_path)
            for img_path in product.screenshots:
                if os.path.exists(img_path): os.remove(img_path)
            if product.demo_video_path and os.path.exists(product.demo_video_path): os.remove(product.demo_video_path)
        except: pass
        db.delete(product)
    
    target_user.is_banned = True
    sessions_to_remove = [k for k, v in active_sessions.items() if v == target_user.username]
    for k in sessions_to_remove: del active_sessions[k]
    
    db.commit()
    return RedirectResponse(url="/admin?msg=user_banned", status_code=303)

@app.post("/admin/approve/{pid}")
async def admin_approve(pid: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not is_admin(user): raise HTTPException(403)
    prod = db.query(Product).filter(Product.id == pid).first()
    if prod: prod.is_verified = True; prod.requires_manual_review = False; db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/toggle-verified/{uid}")
async def toggle_ver(uid: int, request: Request, db: Session = Depends(get_db)):
    u = get_current_user(request, db)
    if not is_admin(u): raise HTTPException(403)
    target = db.query(Seller).filter(Seller.id == uid).first()
    if target: target.is_verified_buyer = not target.is_verified_buyer; db.commit()
    return RedirectResponse(url="/admin", status_code=303)

if __name__ == "__main__":
    import os
    # Берем порт из переменных среды (HF использует 7860) или ставим 8000 локально
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)