import hashlib
import secrets
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.refresh_token import TokensPair
from app.db import UserRole
from app.db.deps import get_db
from app.redis.deps import get_redis, Redis
from app.api.deps import require_role, parse_login_data
from app.services.security import hash_token, create_access_token, verify_password, calculate_expire
from app.schemas import (
    UserRead,
    UserCreate, 
    RefreshTokenCreate, 
    RefreshTokenRequest, 
    SignUpForm, 
    LogInForm,
    AdminSignUpForm,
    JWTPayload,
)
from app.db import crud
from app.settings import get_settings

router = APIRouter(prefix="/api/v1/auth", tags=["v1", "auth"])

@router.post("/signup", response_model=TokensPair, status_code=status.HTTP_201_CREATED)
async def signup(
    signup_data: SignUpForm,
    db: AsyncSession = Depends(get_db),
) -> TokensPair:
    # Логика регистрации пользователя
    user = await crud.get_user_by_email(db, signup_data.email)
    if not user:
        if signup_data.role == "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create an ADMIN user through this endpoint."
            )
        user = await crud.create_user(db, UserCreate(**signup_data.model_dump()))
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
            access_token=create_access_token(JWTPayload(
                sub=user.id,
                role=user.role,
                exp=calculate_expire()
            )), 
            refresh_token=raw_refresh_token
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with such an email already exists."    
        )

@router.post("/signup/{temp_link}", response_model=TokensPair, status_code=status.HTTP_201_CREATED)
async def signup_admin(
    temp_link: str,
    signup_data: AdminSignUpForm,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> TokensPair:
    user = await crud.get_user_by_email(db, signup_data.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with such an email already exists."
        )    

    invite_key = f"admin_invite:{temp_link}"
    if not await redis.getdel(invite_key):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The link is invalid or expired.",
        )
    user = await crud.create_user(db, UserCreate(role="ADMIN", **signup_data.model_dump()))
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
        access_token=create_access_token(JWTPayload(
                sub=user.id,
                role=user.role,
                exp=calculate_expire()
        )), 
        refresh_token=raw_refresh_token
    )

    
@router.post("/login", response_model=TokensPair, status_code=status.HTTP_200_OK)
async def login(
    login_data: LogInForm,
    db = Depends(get_db),
) -> TokensPair:
    user = await crud.get_user_by_email(db, login_data.email)
    if not user or not login_data.password or not verify_password(login_data.password.get_secret_value(), user.password_hash):
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
        access_token=create_access_token(JWTPayload(
                sub=user.id,
                role=user.role,
                exp=calculate_expire()
        )),
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

    if token_db.expires_at < datetime.now(timezone.utc):
        await crud.revoke_token(db, token_db.id)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "The refresh token is expired.")


    
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
                expires_at=datetime.now(timezone.utc) + get_settings().refresh_token_ttl
            )
        )
        await crud.revoke_token(db, token_db.id)
        await crud.delete_old_refresh_tokens(db, get_settings().refresh_token_ttl * 3)
        return TokensPair(
            access_token=create_access_token(JWTPayload(
                sub=user.id,
                role=user.role,
                exp=calculate_expire()
            )),
            refresh_token=new_raw_refresh_token
        )    


@router.post("/invites/admin", summary="Сгенерировать ссылку для нового админа")
async def create_admin_invite(

    redis: Redis = Depends(get_redis),
    jwt_payload: JWTPayload = Depends(require_role(UserRole.ADMIN))
):
    # 1. Генерируем случайный одноразовый токен
    invite_token = secrets.token_urlsafe(32)
    
    # 2. Кладём в Redis с временем жизни 24 часа (86400 секунд)
    # Ключ: admin_invite:<token>, Значение: роль, которую мы дадим
    await redis.set(
        name=f"admin_invite:{invite_token}", 
        value="ADMIN", 
        ex=86400  # Сгорит через 24 часа
    )
    
    # 3. Отдаем ссылку главному админу, чтобы он отправил её коллеге
    invite_url = f"/api/v1/auth/signup/{invite_token}"
    return {"invite_url": invite_url, "expires_in_hours": 24}