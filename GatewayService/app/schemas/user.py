from pydantic import BaseModel, EmailStr, ConfigDict, Field  # @validator
from uuid import UUID
from GatewayService.app.db.model import UserRole

class UserCreate(BaseModel):
    """Что клиент присылает при регистрации."""
    email: EmailStr
    password: str
    name: str = Field(..., min_length=3, max_length=50)
    surname: str
    role: UserRole = UserRole.CLIENT

    # Дополнительные поля для профилей (опционально)
    phone: str | None = None  # Только для Client
    company_name: str | None = None  # Только для PARTNER
    address: str | None = None  # Только для PARTNER

class UserRead(BaseModel):
    """Что мы отдаем клиенту."""
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