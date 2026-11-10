from pwdlib import PasswordHash
from datetime import datetime, timezone, timedelta
from jose import jwt
import hashlib
import hmac

from app.settings import get_settings
from app.db import UserRole
from app.schemas import JWTPayload

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

def verify_token(raw_token: str, token_hash: str) -> bool:
    current_hash = hash_token(raw_token)
    return hmac.compare_digest(current_hash, token_hash)

def calculate_expire(delta: timedelta = get_settings().access_token_ttl) -> datetime:
    return datetime.now(timezone.utc) + delta

def create_access_token(jwt_payload: JWTPayload) -> str:
    """Создает JWT токен. subject — это обычно ID пользователя."""
    to_encode = jwt_payload.model_dump(mode="json")
    encoded_jwt = jwt.encode(to_encode, get_settings().secret_key.get_secret_value(), algorithm=get_settings().access_token_algorithm)
    return encoded_jwt

def decode_token(token: str) -> JWTPayload:
    """Расшифровывает токен. Если подпись неверна или время вышло — выбросит ошибку."""
    return JWTPayload(**jwt.decode(token, get_settings().secret_key.get_secret_value(), algorithms=[get_settings().access_token_algorithm]))