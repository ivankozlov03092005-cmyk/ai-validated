from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# === НАСТРОЙКА ПОДКЛЮЧЕНИЯ К SUPABASE ===
DATABASE_URL = "postgresql://postgres.qsehuwqsawmnfdsajkxv:uctF5JHMiseuQrU;@aws-1-eu-west-1.pooler.supabase.com:6543/postgres"

# Создаем движок с настройками для стабильной работы через пулер
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # Автоматически проверяет соединение перед запросом
    pool_size=5,             # Размер пула соединений
    max_overflow=10,         # Максимум дополнительных соединений
    connect_args={"connect_timeout": 5}, # Таймаут подключения (5 секунд)
    echo=False               # Поставь True, если хочешь видеть SQL-запросы в логах для отладки
)

# Фабрика сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

# Зависимость для получения сессии БД в маршрутах FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Функция инициализации (создания таблиц)
def init_db():
    # Эта функция создаст все таблицы в облачной базе при первом запуске приложения
    # Она вызывается в main.py
    Base.metadata.create_all(bind=engine)