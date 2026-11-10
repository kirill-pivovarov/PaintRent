import json
from datetime import datetime, timezone

from jose import JWTError, ExpiredSignatureError
from pydantic import ValidationError
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status, Request

from app.settings import get_settings
from app.db import UserRole, User
from app.schemas import JWTPayload
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
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token." + str(e),
            headers={"WWW-Authenticate": "Bearer"}
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