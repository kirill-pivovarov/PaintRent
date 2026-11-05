from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import List
from GatewayService.app.db.model import OrderStatus, OrderItemType

class OrderItemRead(BaseModel):
    """Детали одной позиции в заказе."""
    id: UUID
    painting_id: UUID
    type: OrderItemType
    status: OrderStatus
    price: Decimal

    model_config = ConfigDict(from_attributes=True)

class OrderCreate(BaseModel):
    """
    Схема для создания заказа.
    Клиент передает только тип (RENT или PURCHASE).
    Сами картины берутся из его корзины.
    """
    type: OrderItemType = OrderItemType.RENT

class OrderRead(BaseModel):
    """Полный ответ с деталями заказа."""
    id: UUID
    customer_id: UUID
    status: OrderStatus
    total_price: Decimal
    created_at: datetime
    items: List[OrderItemRead]  # Вложенный список позиций

    model_config = ConfigDict(from_attributes=True)