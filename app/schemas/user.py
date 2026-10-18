from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID
from app.db.model import UserRole

class UserCreate(BaseModel):
    """Что клиент присылает при регистрации."""
    email: EmailStr
    password: str
    name: str
    surname: str
    role: UserRole = UserRole.CLIENT
    phone: str | None = None

    # Дополнительные поля для профилей (опционально)
    company_name: str | None = None  # Только для PARTNER
    address: str | None = None  # Только для PARTNER

class UserRead(BaseModel):
    """Что мы отдаем клиенту (без пароля!)."""
    id: UUID
    email: EmailStr
    name: str
    surname: str
    role: UserRole

    # Говорим Pydantic, что можно читать данные из ORM-объекта
    model_config = ConfigDict(from_attributes=True,
                              # Эта строчка говорит: "если поля нет в ORM-объекте, не падай, а ставь None"
                              populate_by_name=True
                              )