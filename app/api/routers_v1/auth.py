from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.core.security import hash_password, verify_password, create_access_token
from app.db.crud.user import UserCRUD
from app.db.model import User
from app.schemas.user import UserCreate, UserRead
from app.schemas.token import Token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Регистрация. Пароль хешируется перед сохранением."""
    crud = UserCRUD()

    if await crud.get_by_email(db, data.email):
        raise HTTPException(status_code=409, detail="Email already registered")

    # Хешируем пароль!
    hashed = hash_password(data.password)

    user = await crud.create(
        db,
        email=data.email,
        password=hashed,  # Передаем хеш, а не чистый пароль
        name=data.name,
        surname=data.surname,
        role=data.role,
        phone=data.phone,
        company_name = data.company_name,
        address = data.address
    )
    return user


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Логин. Возвращает JWT."""
    crud = UserCRUD()
    user = await crud.get_by_email(db, form_data.username)  # Swagger шлет email в поле username

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_access_token(subject=str(user.id))
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Защищенный эндпоинт. Вернет данные только при наличии токена."""
    return current_user