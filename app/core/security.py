from datetime import datetime, timedelta, timezone
from jose import jwt
from pwdlib import PasswordHash
from app.core.config import settings

# Инициализируем хэшер с помощью Argon2 или Bcrypt
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(subject: str) -> str:
    """Создает JWT токен. subject — это обычно ID пользователя."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # В токен кладем время жизни (exp) и ID (sub)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    """Расшифровывает токен. Если подпись неверна или время вышло — выбросит ошибку."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])