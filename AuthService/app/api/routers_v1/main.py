import hashlib
import secrets
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.security import hash_token, create_access_token, verify_password
from app.schemas import UserCreate, UserRead, RefreshTokenCreate, TokensPair, RefreshTokenRequest
from app.db import crud
from app.settings import get_settings

router = APIRouter(prefix="/api/v1/auth", tags=["v1", "auth"])

@router.post("/signup", response_model=TokensPair, status_code=status.HTTP_201_CREATED)
async def signup(
    user_create: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> TokensPair:
    # Логика регистрации пользователя
    user = await crud.get_user_by_email(db, user_create.email)
    if not user:
        user = await crud.create_user(db, user_create)
        session_id = uuid.uuid4()
        raw_refresh_token = secrets.token_urlsafe(64)
        await crud.create_refresh_token(
            db,
            RefreshTokenCreate(
                user_id=user.id,
                session_id=session_id,
                token_hash=hash_token(raw_refresh_token),
                expires_at=datetime.now(timezone.utc) + timedelta(days=get_settings().refresh_token_ttl_days)
            )
        )

        return TokensPair(
            access_token=create_access_token(str(user.id), user.role), 
            refresh_token=raw_refresh_token
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with such an email already exists."    
        )

@router.post("/login", response_model=TokensPair, status_code=status.HTTP_200_OK)
async def login(
    user_create: UserCreate,
    db = Depends(get_db),
) -> TokensPair:
    user = await crud.get_user_by_email(db, user_create.email)

    if not user or not user_create.password or not verify_password(user_create.password.get_secret_value(), user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")


    raw_refresh_token = secrets.token_urlsafe(64)
    await crud.create_refresh_token(
        db,
        RefreshTokenCreate(
            user_id=user.id,
            session_id=uuid.uuid4(),
            token_hash=hash_token(raw_refresh_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=get_settings().refresh_token_ttl_days)
        )
    )

    return TokensPair(
        access_token=create_access_token(user.id, user.role),
        refresh_token=raw_refresh_token
    )

@router.post("/refresh", response_model=TokensPair, status_code=status.HTTP_200_OK)
async def refresh(
    raw_refresh_token: RefreshTokenRequest,
    db=Depends(get_db)
) -> TokensPair:
    """
    Обновляет access_token и refresh_token. Если refresh_token просрочен или отозван, то выбрасывает ошибку 401.
    Если приходит запрос с отозванным refresh_token и при этом в базе данных есть активные токены данной сессии, то аккаунт считается скомпрометированным.
    В таком слуае все токены данного пользователя отзываются и выбрасывается ошибка 401. Пользователю необходимо заново авторизоваться.
    """
    token_db = await crud.get_refresh_token_by_token_hash(db, hash_token(raw_refresh_token.refresh_token))
    user = await crud.get_user_by_refresh_token_hash(db, hash_token(raw_refresh_token.refresh_token))
    if not token_db:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token.")
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "The user is not signed up.")
    if token_db.is_revoked:
        session_tokens = await crud.get_tokens_by_session_id(db, token_db.session_id)
        if any((not token.is_revoked for token in session_tokens)):
            await crud.revoke_all_tokens(db, user.id)
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "A compromised session. A re-login is required.")
        else:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "The user is not loged in.")
    else:
        new_raw_refresh_token = secrets.token_urlsafe(64)
        await crud.create_refresh_token(
            db,
            RefreshTokenCreate(
                user_id=user.id,
                token_hash=hash_token(new_raw_refresh_token),
                session_id=token_db.session_id,
                expires_at=datetime.now(timezone.utc) + timedelta(days=get_settings().refresh_token_ttl_days)
            )
        )
        await crud.revoke_token(db, token_db.id)
        await crud.delete_old_refresh_tokens(db, get_settings().refresh_token_ttl_days * 3)
        return TokensPair(
            access_token=create_access_token(str(user.id), user.role),
            refresh_token=new_raw_refresh_token
        )    
    