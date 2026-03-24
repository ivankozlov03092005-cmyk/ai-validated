from datetime import datetime

class Config:
    # Твоя дата рождения
    FOUNDER_BIRTHDAY = datetime(2011, 9, 3)
    
    # Переключатель монетизации (False = всё бесплатно)
    LEGAL_PAYMENTS_ENABLED = False
    
    # Проверка: активна ли монетизация
    @staticmethod
    def is_monetization_active() -> bool:
        now = datetime.utcnow()
        age_ok = now >= Config.FOUNDER_BIRTHDAY.replace(
            year=Config.FOUNDER_BIRTHDAY.year + 18
        )
        return age_ok and Config.LEGAL_PAYMENTS_ENABLED
    
    # Тарифы (после 2029)
    PRICE_EARLY = 50      # $/мес для ранних
    PRICE_REGULAR = 200   # $/мес для новых
    
    # База данных (локальная SQLite)
    DATABASE_URL = "sqlite:///./platform.db"
    
    # Баллы (сейчас бесплатно)
    POINTS_FOR_UPLOAD = 10