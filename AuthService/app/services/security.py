from pwdlib import PasswordHash
from datetime import datetime, timezone, timedelta
from jose import jwt
import hashlib
import hmac

from app.settings import get_settings
from app.db import UserRole

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

def create_access_token(subject: str, role: UserRole) -> str:
    """Создает JWT токен. subject — это обычно ID пользователя."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=get_settings().access_token_ttl_minutes)
    # В токен кладем время жизни (exp) и ID (sub)
    to_encode = {"exp": expire, "sub": str(subject), "role": role}
    encoded_jwt = jwt.encode(to_encode, get_settings().secret_key, algorithm=get_settings().access_token_algorithm)
    return encoded_jwt

def decode_token(token: str) -> dict:
    """Расшифровывает токен. Если подпись неверна или время вышло — выбросит ошибку."""
    return jwt.decode(token, get_settings().secret_key, algorithms=[get_settings().access_token_algorithm])