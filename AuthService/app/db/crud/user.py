from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from app.db.model import User, RefreshToken
from app.schemas import UserRead, UserCreate, UserUpdate
from app.services.security import hash_password, verify_password

async def get_user_by_id(session: AsyncSession, user_id: str) -> UserRead | None:
    result = await session.get(User, user_id)
    if result:
        return UserRead.model_validate(result)
    return None

async def get_user_by_email(session: AsyncSession, email: str) -> UserRead | None:
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        return UserRead.model_validate(user)
    return None

async def get_user_by_refresh_token_hash(session: AsyncSession, token_hash: str) -> User | None:
    stmt = select(User).join(User.tokens).where(RefreshToken.token_hash == token_hash)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def create_user(session: AsyncSession, user_create: UserCreate) -> User:
    new_user = User(
        email=user_create.email,
        password_hash=hash_password(user_create.password.get_secret_value()),
        role=user_create.role
    )
    session.add(new_user)
    await session.flush()
    await session.refresh(new_user)
    return new_user

async def update_user(session: AsyncSession, user_id: str, user_update: UserUpdate) -> UserRead | None:
    password_update_condition = (
        user_update.new_password is not None and
        user_update.old_password is not None and
        verify_password(user_update.old_password.get_secret_value(), (await get_user_by_id(session, user_id)).password_hash)
    )

    stmt = update(User).where(User.id == user_id).values(
        email=user_update.email,
        password_hash=hash_password(user_update.new_password.get_secret_value()) if password_update_condition else None,
        role=user_update.role
    ).execution_options(synchronize_session="fetch")
    await session.execute(stmt)
    await session.flush()
    return await get_user_by_id(session, user_id)

async def delete_user(session: AsyncSession, user_id: str) -> bool:
    stmt = delete(User).where(User.id == user_id)
    result = await session.execute(stmt)
    await session.flush()
    return result.rowcount > 0

