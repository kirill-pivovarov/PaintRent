from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi.security import OAuth2PasswordBearer

from app.settings import get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

engine = create_async_engine(
    get_settings().db_url,
    echo=False,
    pool_pre_ping=True,
)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Зависимость (Dependency) для получения сессии БД.
    FastAPI вызывает её перед каждым запросом.
    """

    async with AsyncSessionLocal() as session:
        try:
            # Отдаем сессию в эндпоинт (код после yield выполнится только после завершения эндпоинта)
            yield session
            # Если запрос прошел без ошибок — сохраняем изменения (коммит)
            await session.commit()
        except Exception:
            await session.rollback()
            raise



