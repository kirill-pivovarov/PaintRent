from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List

from app.api.deps import get_db, require_role, CurrentUser, get_current_user
from app.db.crud.order import OrderCRUD
from app.db.crud.cart import CartCRUD  # Импортируем CRUD корзины!
from app.db.model import UserRole, Order, OrderStatus, OrderItem
from app.schemas.order import OrderCreate, OrderRead

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
        data: OrderCreate,
        db: AsyncSession = Depends(get_db),
        current_user: CurrentUser = Depends(require_role(UserRole.CLIENT))
):
    """Создать заказ из корзины."""
    cart_crud = CartCRUD()
    order_crud = OrderCRUD()

    # 1. Получаем корзину пользователя (вместе с картинами)
    cart = await cart_crud.get_or_create_by_user(db, current_user.id)

    if not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # 2. Создаем заказ (вся логика внутри CRUD)
    try:
        order = await order_crud.create_order_from_cart(
            db,
            customer_id=current_user.id,
            cart=cart,
            order_type=data.type
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return order


@router.get("/my", response_model=List[OrderRead])
async def get_my_orders(
        db: AsyncSession = Depends(get_db),
        current_user: CurrentUser = Depends(require_role(UserRole.CLIENT))
):
    """История заказов клиента."""
    stmt = (
        select(Order)
        .where(Order.customer_id == current_user.id)
        .options(selectinload(Order.items).selectinload(OrderItem.painting))
        .order_by(Order.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.patch("/items/{item_id}/confirm", status_code=status.HTTP_200_OK)
async def confirm_item(
        item_id: UUID,
        db: AsyncSession = Depends(get_db),
        current_user: CurrentUser = Depends(require_role(UserRole.PARTNER))
):
    """Партнёр подтверждает наличие картины."""
    crud = OrderCRUD()
    try:
        item = await crud.confirm_order_item(db, item_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not item:
        raise HTTPException(status_code=404, detail="Order item not found")

    return {"message": "Item confirmed", "item_id": item.id}


@router.patch("/{order_id}/pay", response_model=OrderRead)
async def pay_order(
        order_id: UUID,
        db: AsyncSession = Depends(get_db),
        current_user: CurrentUser = Depends(require_role(UserRole.CLIENT))
):
    """Клиент оплачивает заказ."""
    crud = OrderCRUD()
    order = await crud.get_with_items(db, order_id)

    if not order or order.customer_id != current_user.id:
        raise HTTPException(404, "Order not found")

    if order.status != OrderStatus.CONFIRMED:
        raise HTTPException(
            status_code=400,
            detail="Cannot pay. Wait for all partners to confirm items."
        )

    updated_order = await crud.update_status(db, order_id, OrderStatus.PAID)
    return updated_order


@router.patch("/{order_id}/cancel", response_model=OrderRead)
async def cancel_order(
        order_id: UUID,
        db: AsyncSession = Depends(get_db),
        current_user: CurrentUser = Depends(get_current_user)  # Может клиент или админ
):
    """Отмена заказа."""
    crud = OrderCRUD()
    order = await crud.get_with_items(db, order_id)

    if not order:
        raise HTTPException(404, "Order not found")

    if current_user.role not in (UserRole.ADMIN, UserRole.CLIENT) or \
            (current_user.role == UserRole.CLIENT and order.customer_id != current_user.id):
        raise HTTPException(403, "Not allowed to cancel this order")

    if order.status == OrderStatus.PAID:
        raise HTTPException(400, "Cannot cancel already paid order")

    updated_order = await crud.update_status(db, order_id, OrderStatus.CANCELED)
    return updated_order