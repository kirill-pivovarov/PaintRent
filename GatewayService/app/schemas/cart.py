from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import List
from app.schemas.painting import PaintingRead

class CartItemRead(BaseModel):
    """Позиция в корзине (сразу с информацией о картине)."""
    id: UUID
    painting_id: UUID
    painting: PaintingRead # Вложенный объект картины (чтобы фронт видел название и цену)

    model_config = ConfigDict(from_attributes=True)

class CartRead(BaseModel):
    """Сама корзина."""
    id: UUID
    user_id: UUID
    items: List[CartItemRead] = [] # Список позиций

    model_config = ConfigDict(from_attributes=True)