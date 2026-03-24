from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone

# Константы
CURRENCIES = {
    "RUB": {"name": "Российский рубль", "symbol": "₽"},
    "USD": {"name": "Доллар США", "symbol": "$"},
    "EUR": {"name": "Евро", "symbol": "€"},
    "KZT": {"name": "Казахстанский тенге", "symbol": "₸"},
    "BYN": {"name": "Белорусский рубль", "symbol": "Br"},
    "CRYPTO": {"name": "USDT (Crypto)", "symbol": "₮"},
}

LANGUAGES = {
    "ru": "Русский",
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "zh": "中文",
}

MAIN_CATEGORIES = [
    "Programming", "Science", "Education", "Games", "Design", 
    "Music", "Video", "Business", "Other"
]

class Seller(Base):
    __tablename__ = "sellers"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    
    # Профиль
    currency = Column(String, default="RUB")
    language = Column(String, default="ru")
    payout_requisites = Column(Text, nullable=True)
    
    # Статусы
    is_banned = Column(Boolean, default=False)
    is_verified_buyer = Column(Boolean, default=False)
    is_brand = Column(Boolean, default=False)
    is_founder = Column(Boolean, default=False)
    is_early_adopter = Column(Boolean, default=False)
    
    # Экономика
    balance = Column(Float, default=0.0)
    total_earned = Column(Float, default=0.0)
    points = Column(Integer, default=0)
    
    # Рейтинги
    seller_rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    
    # Даты
    registered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime, nullable=True)

    # Связи
    products = relationship("Product", back_populates="seller", cascade="all, delete-orphan")
    sales = relationship("Transaction", foreign_keys="Transaction.seller_id", back_populates="seller")
    purchases = relationship("Transaction", foreign_keys="Transaction.buyer_id", back_populates="buyer")
    reviews_given = relationship("Review", foreign_keys="Review.buyer_id", back_populates="buyer")
    reports_made = relationship("Report", foreign_keys="Report.reporter_id", back_populates="reporter")
    reports_against = relationship("Report", foreign_keys="Report.target_seller_id", back_populates="target_seller")

    def get_currency_symbol(self):
        return CURRENCIES.get(self.currency, {}).get("symbol", "₽")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("sellers.id"), nullable=False)
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    main_category = Column(String, default="Other")
    sub_category = Column(String, default="General")
    
    price = Column(Float, default=0.0)
    file_path = Column(String, nullable=False)
    screenshots = Column(JSON, default=list)
    demo_video_path = Column(String, nullable=True)
    
    # Статусы проверки
    is_verified = Column(Boolean, default=False)
    requires_manual_review = Column(Boolean, default=False)
    ai_check_status = Column(String, default="pending")
    ai_check_reason = Column(String, nullable=True)
    
    # Статистика
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    product_rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    seller = relationship("Seller", back_populates="products")
    transactions = relationship("Transaction", back_populates="product")
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="product", cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("sellers.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("sellers.id"), nullable=False)
    
    amount = Column(Float, nullable=False)
    screenshot_path = Column(String, nullable=True)
    status = Column(String, default="verification") # verification, completed, rejected
    payment_method = Column(String, default="p2p")
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    paid_at = Column(DateTime, nullable=True)

    product = relationship("Product", back_populates="transactions")
    buyer = relationship("Seller", foreign_keys=[buyer_id], back_populates="purchases")
    seller = relationship("Seller", foreign_keys=[seller_id], back_populates="sales")

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("sellers.id"), nullable=False)
    
    rating = Column(Integer, nullable=False) # 1-5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    product = relationship("Product", back_populates="reviews")
    buyer = relationship("Seller", foreign_keys=[buyer_id], back_populates="reviews_given")

# === НОВЫЙ КЛАСС ДЛЯ ЖАЛОБ ===
class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("sellers.id"), nullable=False)
    target_seller_id = Column(Integer, ForeignKey("sellers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    
    reason = Column(String, nullable=False) # scam, virus, fake, rude, other
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    reporter = relationship("Seller", foreign_keys=[reporter_id], back_populates="reports_made")
    target_seller = relationship("Seller", foreign_keys=[target_seller_id], back_populates="reports_against")
    product = relationship("Product", back_populates="reports")

class ViewHistory(Base):
    __tablename__ = "view_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("sellers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    viewed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))