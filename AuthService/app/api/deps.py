import json
from datetime import datetime, timezone

from jose import JWTError, ExpiredSignatureError
from pydantic import ValidationError
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status, Request

from app.settings import get_settings
from app.db import UserRole, User
from app.schemas import JWTPayload, LogInForm
from app.services.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_jwt_payload(
    token=Depends(oauth2_scheme)
) -> JWTPayload:
    try:
        return decode_token(token)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is expired.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def parse_login_data(request: Request) -> LogInForm:
    """
    Универсальный парсер:
    - Читает чистый JSON (если шлет клиент или Postman)
    - Читает Form Data (если запрос идет из модального окна Swagger)
    """
    content_type = request.headers.get("content-type", "")

    # 1. Сценарий: пришел JSON от реального клиента
    if "application/json" in content_type:
        try:
            body = await request.json()
            return LogInForm.model_validate(body)
        except (json.JSONDecodeError, ValidationError) as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Невалидный JSON: {str(e)}"
            )

    # 2. Сценарий: пришла форма OAuth2 из модального окна Swagger
    elif "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        # В форме Swagger email лежит в поле username
        email = form.get("username")
        password = form.get("password")

        if not email or not password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Поля 'username' (email) и 'password' обязательны"
            )

        try:
            # Преобразуем форму в нашу родную схему UserLogin!
            return LogInForm(email=email, password=password)
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.errors()
            )

    # 3. Неизвестный формат
    else:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Ожидается Content-Type: application/json или application/x-www-form-urlencoded"
        )

def require_role(*allowed_roles: UserRole):
    """
    Фабрика зависимостей: проверяет, что текущий пользователь обладает одной из разрешенных ролей.
    """
    async def role_checker(jwt_payload: JWTPayload = Depends(get_jwt_payload)) -> JWTPayload:
        if jwt_payload.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для доступа к этому разделу"
            )
        return jwt_payload

    return role_checker