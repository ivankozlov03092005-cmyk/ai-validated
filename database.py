from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# === НАСТРОЙКА ПОДКЛЮЧЕНИЯ К SUPABASE ===
DATABASE_URL = "postgresql://postgres.qsehuwqsawmnfdsajkxv:uctF5JHMiseuQrU;@aws-1-eu-west-1.pooler.supabase.com:6543/postgres"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # Пингует базу перед каждым запросом. Если связь потеряна - пересоздает.
    pool_size=2,             # Уменьшил пул для экономии памяти на бесплатном тарифе
    max_overflow=5,
    connect_args={
        "connect_timeout": 30,  # Ждем подключения до 30 секунд (критично для waking up!)
        "sslmode": "require"
    },
    echo=False
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