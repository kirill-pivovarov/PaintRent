from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

# Инициализируем хэшер с помощью Argon2 или Bcrypt
password_hash = PasswordHash((BcryptHasher(),))


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)