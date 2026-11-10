from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Используем тот же самый enum, что и в заказах!
from app.db.model import OrderItemType
from app.schemas.painting import PaintingRead


# ==========================================
# 1. Позиция в корзине (CartItem)
# ==========================================

class CartItemBase(BaseModel):
    """Базовые параметры позиции в корзине."""
    rental_type: OrderItemType = Field(
        default=OrderItemType.RENT,
        description="Тип операции: RENT (аренда) или PURCHASE (покупка)"
    )
    rental_begin_date: Optional[date] = Field(
        default=None,
        description="Дата начала аренды (обязательна при rental_type == RENT)"
    )
    rental_end_date: Optional[date] = Field(
        default=None,
        description="Дата окончания аренды (обязательна при rental_type == RENT)"
    )


class CartItemCreate(CartItemBase):
    """
    Схема для добавления картины в корзину (POST /api/v1/cart/items).
    Клиент передает painting_id, желаемый тип и даты аренды.
    """
    painting_id: UUID = Field(..., description="ID добавляемой картины")

    @model_validator(mode="after")
    def validate_rental_conditions(self) -> "CartItemCreate":
        if self.rental_type == OrderItemType.RENT:
            if not self.rental_begin_date or not self.rental_end_date:
                raise ValueError("Для аренды (RENT) необходимо указать даты начала и окончания")
            if self.rental_end_date <= self.rental_begin_date:
                raise ValueError("Дата окончания аренды должна быть строго позже даты начала")
            if self.rental_begin_date < date.today():
                raise ValueError("Дата начала аренды не может быть в прошлом")
        elif self.rental_type == OrderItemType.PURCHASE:
            # При покупке даты аренды не имеют смысла
            self.rental_begin_date = None
            self.rental_end_date = None

        return self


class CartItemUpdate(BaseModel):
    """
    Схема для частичного изменения позиции в корзине (PATCH /api/v1/cart/items/{item_id}).
    Позволяет переключить RENT/PURCHASE или скорректировать даты.
    """
    rental_type: Optional[OrderItemType] = None
    rental_begin_date: Optional[date] = None
    rental_end_date: Optional[date] = None

    @model_validator(mode="after")
    def validate_dates(self) -> "CartItemUpdate":
        if self.rental_begin_date and self.rental_end_date:
            if self.rental_end_date <= self.rental_begin_date:
                raise ValueError("Дата окончания аренды должна быть позже даты начала")
        return self


class CartItemRead(CartItemBase):
    """
    Детали одной позиции в корзине при чтении (GET /api/v1/cart).
    Согласуется с OrderItemRead: содержит id, painting_id, тип и данные картины.
    """
    id: UUID
    cart_id: UUID
    painting_id: UUID
    created_at: datetime

    # Вложенная схема картины (автоматически подтянется из relationship `painting`)
    painting: Optional[PaintingRead] = None

    # Рассчитанная цена позиции (сумма за дни аренды или цена выкупа)
    item_price: Optional[Decimal] = Field(
        default=None, 
        description="Рассчитанная стоимость позиции на основе цен картины и срока"
    )

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 2. Корзина целиком (Cart)
# ==========================================

class CartRead(BaseModel):
    """
    Полный ответ с деталями корзины клиента (GET /api/v1/cart).
    Согласована по стилю с OrderRead.
    """
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    # Список позиций в корзине (как `items: List[OrderItemRead]` в OrderRead)
    items: List[CartItemRead] = Field(default_factory=list)

    # Итоговые агрегаты для удобства фронтенда
    total_items_count: int = Field(default=0, description="Количество картин в корзине")
    total_price: Decimal = Field(default=Decimal("0.00"), description="Общая стоимость всех позиций")

    model_config = ConfigDict(from_attributes=True)


class CartClearResponse(BaseModel):
    """Ответ при очистке корзины (DELETE /api/v1/cart)."""
    message: str = "Корзина успешно очищена"