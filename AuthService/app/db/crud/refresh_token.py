from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from app.db.model import RefreshToken
from app.schemas import RefreshTokenRead, RefreshTokenCreate, RefreshTokenUpdate

async def get_refresh_token_by_id(session: AsyncSession, token_id: str) -> RefreshTokenRead | None:
    result = await session.get(RefreshToken, token_id)
    if result:
        return RefreshTokenRead.model_validate(result)
    return None

async def get_refresh_token_by_token_hash(session: AsyncSession, token_hash: str) -> RefreshTokenRead | None:
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    result = await session.execute(stmt)
    refresh_token = result.scalar_one_or_none()
    if refresh_token:
        return RefreshTokenRead.model_validate(refresh_token)
    return None

async def get_tokens_by_session_id(session: AsyncSession, session_id: UUID) -> list[RefreshTokenRead]:
    stmt = select(RefreshToken).where(RefreshToken.session_id == session_id)
    result = await session.execute(stmt)
    rows = result.scalars().all()
    tokens = [RefreshTokenRead.model_validate(row) for row in rows]
    return tokens

async def revoke_all_tokens(session: AsyncSession, user_id: UUID):
    stmt = update(RefreshToken)\
        .where(RefreshToken.user_id == user_id)\
        .values(is_revoked=True)\
        .execution_options(synchronize_session="fetch")
    await session.execute(stmt)
    await session.commit()

async def revoke_token(session: AsyncSession, token_id: UUID):
    stmt = update(RefreshToken)\
        .where(RefreshToken.id == token_id)\
        .values(is_revoked=True)\
        .execution_options(synchronize_session="fetch")
    await session.execute(stmt)
    await session.flush()

async def create_refresh_token(session: AsyncSession, refresh_token_create: RefreshTokenCreate) -> RefreshTokenRead:
    new_refresh_token = RefreshToken(
        user_id=refresh_token_create.user_id,
        token_hash=refresh_token_create.token_hash,
        session_id=refresh_token_create.session_id,
        expires_at=refresh_token_create.expires_at
    )
    session.add(new_refresh_token)
    await session.flush()
    await session.refresh(new_refresh_token)
    return RefreshTokenRead.model_validate(new_refresh_token)

async def delete_old_refresh_tokens(session: AsyncSession, period_days: int):
    stmt = delete(RefreshToken).where(RefreshToken.expires_at + timedelta(days=period_days) < datetime.now(timezone.utc))
    await session.execute(stmt)
    await session.flush()