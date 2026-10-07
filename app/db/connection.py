import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()


def _env(name: str) -> str:
    """Читает переменную окружения или падает с понятной ошибкой."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Переменная {name!r} не задана. Проверь файл .env (см. .env.example)."
        )
    return value


DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{_env('DB_USER')}:{_env('DB_PASSWORD')}"
    f"@{_env('DB_HOST')}:{_env('DB_PORT')}/{_env('DB_NAME')}"
)

engine = create_engine(DATABASE_URL,
                       echo=False,
                       future=True,
                       pool_pre_ping=True)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def get_db():
    """Сессия БД. Для FastAPI (Depends) и для скриптов (with SessionLocal())."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()