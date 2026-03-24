// static/i18n.js

const translations = {
    ru: { 
        nav_home: "Главная", nav_catalog: "Каталог", nav_upload: "Загрузить", nav_dashboard: "Кабинет", nav_settings: "Настройки", nav_logout: "Выход", nav_admin: "Админка",
        hero_title: "Платформа проверенных AI-инструментов", hero_desc: "Загружай, скачивай и используй инструменты с гарантией безопасности.", 
        hero_btn_upload: "⬆️ Загрузить товар", hero_btn_catalog: "📦 Смотреть каталог",
        stat_sellers: "Разработчиков", stat_products: "Инструментов", stat_checks: "Проверок", stat_free: "Сейчас бесплатно",
        footer_copy: "© 2025 AI Validated Platform. Все права защищены.",
        dash_title: "Личный кабинет", dash_points: "Баллов", dash_items: "Товаров", dash_reg_date: "Дата регистрации",
        dash_early_title: "Вы — ранний участник!", dash_early_desc: "Ваш пожизненный тариф после 2029: ",
        dash_my_products: "Ваши товары", dash_btn_new: "⬆️ Загрузить новый", dash_no_products: "У вас пока нет товаров",
        dash_upload_first: "Загрузить первый", dash_verified: "Проверен", dash_pending: "На проверке",
        upload_title: "Загрузить товар", upload_req_title: "Требования к товару", 
        upload_req_1: "Файл должен быть безопасным (проверка VirusTotal)", upload_req_2: "Описание без спама", 
        upload_req_3: "Товар должен быть вашим авторским", upload_req_4: "Максимальный размер: 50 МБ",
        upload_free_info: "Сейчас размещение БЕСПЛАТНО! Вы получите +10 баллов за загрузку.",
        form_title: "Название товара", form_desc: "Описание", form_price: "Цена товара (в рублях/баллах)", form_price_hint: "Укажите 0, если товар бесплатный",
        form_file: "Файл", form_file_drop: "Перетащите файл или нажмите для выбора", form_file_supported: "Поддерживаются: .py, .exe, .zip, .pdf, .js",
        upload_btn: "🚀 Загрузить на проверку",
        login_title: "Вход", login_desc: "Войдите в свой аккаунт", login_user: "Имя пользователя", login_pass: "Пароль", login_btn: "🔑 Войти",
        login_no_acc: "Нет аккаунта?", login_reg_link: "Зарегистрироваться",
        reg_title: "Регистрация", reg_desc: "Создайте аккаунт для загрузки товаров", reg_email: "Email", reg_pass_hint: "Минимум 8 символов",
        reg_btn: "🚀 Зарегистрироваться", reg_has_acc: "Уже есть аккаунт?", reg_login_link: "Войти",
        settings_title: "Настройки аккаунта", settings_currency: "💱 Валюта", settings_lang: "🌐 Язык интерфейса",
        settings_save: "💾 Сохранить изменения", settings_saved: "✅ Настройки сохранены!",
        settings_info_title: "ℹ️ Информация", settings_balance: "Баланс", settings_earned: "Заработано всего",
        catalog_title: "Каталог товаров", catalog_desc: "Проверенные AI-инструменты от разработчиков",
        btn_buy: "Купить", btn_download: "Скачать", btn_details: "Подробнее",
        admin_title: "Панель Основателя", admin_users: "Пользователей", admin_sales: "Продаж", admin_disputes: "Споров",
        admin_disputes_active: "Активные споры (Требуют решения)", admin_no_disputes: "Споров нет.",
        admin_users_mgmt: "Управление пользователями", admin_col_nick: "Ник", admin_col_balance: "Баланс", admin_col_status: "Статус", admin_col_action: "Действие",
        admin_btn_toggle: "Сменить Verified", admin_btn_resolve: "⚖️ Решить в пользу покупателя"
    },
    en: { 
        nav_home: "Home", nav_catalog: "Catalog", nav_upload: "Upload", nav_dashboard: "Dashboard", nav_settings: "Settings", nav_logout: "Logout", nav_admin: "Admin",
        hero_title: "Validated AI Tools Platform", hero_desc: "Upload, download and use tools with safety guarantee.", 
        hero_btn_upload: "⬆️ Upload Product", hero_btn_catalog: "📦 View Catalog",
        stat_sellers: "Developers", stat_products: "Tools", stat_checks: "Checks", stat_free: "Free Now",
        footer_copy: "© 2025 AI Validated Platform. All rights reserved.",
        dash_title: "Dashboard", dash_points: "Points", dash_items: "Items", dash_reg_date: "Registration Date",
        dash_early_title: "You are an Early Adopter!", dash_early_desc: "Your lifetime rate after 2029: ",
        dash_my_products: "Your Products", dash_btn_new: "⬆️ Upload New", dash_no_products: "No products yet",
        dash_upload_first: "Upload First", dash_verified: "Verified", dash_pending: "Pending",
        upload_title: "Upload Product", upload_req_title: "Requirements", 
        upload_req_1: "File must be safe (VirusTotal check)", upload_req_2: "No spam in description", 
        upload_req_3: "Must be your original work", upload_req_4: "Max size: 50 MB",
        upload_free_info: "Listing is FREE now! Get +10 points for upload.",
        form_title: "Product Title", form_desc: "Description", form_price: "Price (RUB/Points)", form_price_hint: "Set 0 for free",
        form_file: "File", form_file_drop: "Drag file or click to select", form_file_supported: "Supported: .py, .exe, .zip, .pdf, .js",
        upload_btn: "🚀 Upload for Review",
        login_title: "Login", login_desc: "Sign in to your account", login_user: "Username", login_pass: "Password", login_btn: "🔑 Sign In",
        login_no_acc: "No account?", login_reg_link: "Register",
        reg_title: "Register", reg_desc: "Create account to upload products", reg_email: "Email", reg_pass_hint: "Min 8 characters",
        reg_btn: "🚀 Register", reg_has_acc: "Already have an account?", reg_login_link: "Login",
        settings_title: "Account Settings", settings_currency: "💱 Currency", settings_lang: "🌐 Interface Language",
        settings_save: "💾 Save Changes", settings_saved: "✅ Settings Saved!",
        settings_info_title: "ℹ️ Info", settings_balance: "Balance", settings_earned: "Total Earned",
        catalog_title: "Product Catalog", catalog_desc: "Verified AI tools from developers",
        btn_buy: "Buy", btn_download: "Download", btn_details: "Details",
        admin_title: "Founder Panel", admin_users: "Users", admin_sales: "Sales", admin_disputes: "Disputes",
        admin_disputes_active: "Active Disputes", admin_no_disputes: "No disputes.",
        admin_users_mgmt: "User Management", admin_col_nick: "Nick", admin_col_balance: "Balance", admin_col_status: "Status", admin_col_action: "Action",
        admin_btn_toggle: "Toggle Verified", admin_btn_resolve: "⚖️ Resolve for Buyer"
    },
    es: { nav_home: "Inicio", nav_catalog: "Catálogo", nav_upload: "Subir", nav_dashboard: "Panel", nav_settings: "Ajustes", nav_logout: "Salir", nav_admin: "Admin", hero_title: "Plataforma de Herramientas IA", upload_btn: "🚀 Subir", login_btn: "Entrar", reg_btn: "Registrarse" },
    de: { nav_home: "Startseite", nav_catalog: "Katalog", nav_upload: "Hochladen", nav_dashboard: "Armaturenbrett", nav_settings: "Einstellungen", nav_logout: "Ausloggen", nav_admin: "Admin", hero_title: "KI-Tools Plattform", upload_btn: "🚀 Hochladen", login_btn: "Anmelden", reg_btn: "Registrieren" },
    fr: { nav_home: "Accueil", nav_catalog: "Catalogue", nav_upload: "Télécharger", nav_dashboard: "Tableau de bord", nav_settings: "Paramètres", nav_logout: "Déconnexion", nav_admin: "Admin", hero_title: "Plateforme d'outils IA", upload_btn: "🚀 Télécharger", login_btn: "Se connecter", reg_btn: "S'inscrire" },
    zh: { nav_home: "首页", nav_catalog: "目录", nav_upload: "上传", nav_dashboard: "仪表板", nav_settings: "设置", nav_logout: "登出", nav_admin: "管理", hero_title: "验证的 AI 工具平台", upload_btn: "🚀 上传", login_btn: "登录", reg_btn: "注册" },
    ja: { nav_home: "ホーム", nav_catalog: "カタログ", nav_upload: "アップロード", nav_dashboard: "ダッシュボード", nav_settings: "設定", nav_logout: "ログアウト", nav_admin: "管理", hero_title: "検証済み AI ツール", upload_btn: "🚀 アップロード", login_btn: "ログイン", reg_btn: "登録" },
    ko: { nav_home: "홈", nav_catalog: "카탈로그", nav_upload: "업로드", nav_dashboard: "대시보드", nav_settings: "설정", nav_logout: "로그아웃", nav_admin: "관리", hero_title: "검증된 AI 도구", upload_btn: "🚀 업로드", login_btn: "로그인", reg_btn: "등록" },
    pt: { nav_home: "Início", nav_catalog: "Catálogo", nav_upload: "Carregar", nav_dashboard: "Painel", nav_settings: "Configurações", nav_logout: "Sair", nav_admin: "Admin", hero_title: "Plataforma de Ferramentas IA", upload_btn: "🚀 Carregar", login_btn: "Entrar", reg_btn: "Registrar" },
    it: { nav_home: "Home", nav_catalog: "Catalogo", nav_upload: "Carica", nav_dashboard: "Bacheca", nav_settings: "Impostazioni", nav_logout: "Esci", nav_admin: "Admin", hero_title: "Piattaforma Strumenti IA", upload_btn: "🚀 Carica", login_btn: "Accedi", reg_btn: "Registrati" },
    tr: { nav_home: "Ana Sayfa", nav_catalog: "Katalog", nav_upload: "Yükle", nav_dashboard: "Panel", nav_settings: "Ayarlar", nav_logout: "Çıkış", nav_admin: "Yönetici", hero_title: "Doğrulanmış AI Araçları", upload_btn: "🚀 Yükle", login_btn: "Giriş", reg_btn: "Kayıt Ol" },
    ar: { nav_home: "الرئيسية", nav_catalog: "الفهرس", nav_upload: "رفع", nav_dashboard: "لوحة القيادة", nav_settings: "إعدادات", nav_logout: "خروج", nav_admin: "إدارة", hero_title: "منصة أدوات الذكاء الاصطناعي", upload_btn: "🚀 رفع", login_btn: "دخول", reg_btn: "تسجيل" },
    hi: { nav_home: "होम", nav_catalog: "सूची", nav_upload: "अपलोड", nav_dashboard: "डैशबोर्ड", nav_settings: "सेटिंग्स", nav_logout: "लॉग आउट", nav_admin: "प्रशासन", hero_title: "सत्यापित AI टूल", upload_btn: "🚀 अपलोड", login_btn: "प्रवेश", reg_btn: "रजिस्टर" },
    kz: { nav_home: "Басты бет", nav_catalog: "Каталог", nav_upload: "Жүктеу", nav_dashboard: "Панель", nav_settings: "Баптаулар", nav_logout: "Шығу", nav_admin: "Әкімші", hero_title: "Тексерілген AI құралдары", upload_btn: "🚀 Жүктеу", login_btn: "Кіру", reg_btn: "Тіркелу" },
    ua: { nav_home: "Головна", nav_catalog: "Каталог", nav_upload: "Завантажити", nav_dashboard: "Кабінет", nav_settings: "Налаштування", nav_logout: "Вихід", nav_admin: "Адмін", hero_title: "Платформа перевірених ШІ інструментів", upload_btn: "🚀 Завантажити", login_btn: "Увійти", reg_btn: "Зареєструватися" }
};

function applyTranslation(lang) {
    const elements = document.querySelectorAll('[data-i18n]');
    elements.forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[lang] && translations[lang][key]) {
            el.textContent = translations[lang][key];
        }
    });
    localStorage.setItem('user_lang', lang);
    document.documentElement.lang = lang;
}

document.addEventListener('DOMContentLoaded', () => {
    // Пытаемся получить язык из шаблона (если переменная передана) или из памяти
    const serverLang = "{{ current_user.language if current_user else 'ru' }}";
    const savedLang = localStorage.getItem('user_lang');
    
    // Приоритет: Язык от сервера (если не 'ru' дефолтный) > Сохраненный в браузере > Русский
    let langToUse = 'ru';
    if (serverLang && serverLang !== 'ru' && serverLang.includes('{{') === false) {
        langToUse = serverLang;
    } else if (savedLang) {
        langToUse = savedLang;
    }
    
    applyTranslation(langToUse);
});