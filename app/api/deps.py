from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.connection import AsyncSessionLocal

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
