from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field  # @validator
from uuid import UUID
from app.db.model import PaintingStatus


class PaintingBase(BaseModel):
    """Базовые поля картины."""
    title: str
    author: str
    creation_year: int = Field(..., ge=1900)
    # description
    price: Decimal = Field(..., gt=0)
    rent_price: Decimal = Field(..., gt=0)


class PaintingCreate(PaintingBase):
    """Схема для создания."""
    pass


class PaintingUpdate(BaseModel):
    """Схема для обновления.
    Все поля опциональны, тк клиент может менять только часть из них."""
    title: str | None = None
    author: str | None = None
    creation_year: int | None = None
    # description
    price: Decimal | None = None
    rent_price: Decimal | None = None

    status: PaintingStatus | None = None


class PaintingRead(PaintingBase):
    id: UUID
    partner_id: UUID
    status: PaintingStatus
    created_at: datetime

    # Позволяет Pydantic читать данные прямо из ORM-объекта SQLAlchemy
    model_config = ConfigDict(from_attributes=True)