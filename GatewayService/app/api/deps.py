from typing import AsyncGenerator
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from pydantic import BaseModel

from app.db.connection import AsyncSessionLocal
from app.core.security import decode_token
from app.db.model import UserRole


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Зависимость для получения сессии БД."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


security = HTTPBearer()


class CurrentUser(BaseModel):
    """
    Pydantic-схема для данных из токена.
    Мы НЕ используем ORM-модель User, чтобы не лезть в БД.
    """
    id: UUID
    role: UserRole


async def get_current_user(
        token: str = Depends(security),
) -> CurrentUser:
    """Достает ID и роль пользователя прямо из токена."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id_str: str = payload.get("sub")
        role_str: str = payload.get("role")  # Достаем роль из токена!

        if user_id_str is None or role_str is None:
            raise credentials_exception

        return CurrentUser(
            id=UUID(user_id_str),
            role=UserRole(role_str)
        )
    except Exception:
        raise credentials_exception


def require_role(*roles: UserRole):
    """Фабрика зависимостей: пропускает только пользователей с одной из указанных ролей."""

    async def role_checker(
            current_user: CurrentUser = Depends(get_current_user)
    ) -> CurrentUser:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to perform this action"
            )
        return current_user

    return role_checker