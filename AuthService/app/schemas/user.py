from pydantic import BaseModel, EmailStr, SecretStr, ConfigDict
from uuid import UUID

from app.db.model import UserRole

class UserCreate(BaseModel):
    email: EmailStr
    password: SecretStr
    role: UserRole = UserRole.CLIENT


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    role: UserRole
    password_hash: str
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    old_password: SecretStr | None = None
    new_password: SecretStr | None = None
    role: UserRole | None = None


