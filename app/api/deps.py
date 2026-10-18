from typing import AsyncGenerator
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.connection import AsyncSessionLocal
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_token
from app.db.crud.user import UserCRUD
from app.db.model import User

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

# Эта строчка нужна для кнопки Authorize в Swagger
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db),
) -> User:
    """Достает текущего пользователя из токена."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = UUID(user_id_str)

    except Exception:
        raise credentials_exception

    user = await UserCRUD().get_by_id(db, user_id)
    if user is None:
        raise credentials_exception

    return user

