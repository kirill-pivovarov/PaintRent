from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List

from app.api.deps import get_jwt_payload, require_role
from app.db.deps import get_db
from app.db.crud.order import OrderCRUD
from app.db.model import User, UserRole, Order, Painting, PaintingStatus, OrderItemType, OrderStatus, OrderItemStatus
from app.schemas.order import OrderCreate, OrderRead
from app.schemas import JWTPayload

router = APIRouter(prefix="/orders", tags=["Orders"])

order_crud = OrderCRUD()

@router.post("/form", response_model=OrderRead, status_code=status.HTTP_200_OK)
async def form_order(
    db: AsyncSession = Depends(get_db),
    jwt_payload: JWTPayload = Depends(require_role(UserRole.CLIENT))
) -> OrderRead:
    order = await order_crud.create_order_from_cart(db, user_id=jwt_payload.sub)
    return order
    

@router.get("/my", response_model=List[OrderRead])
async def get_my_orders(
        db: AsyncSession = Depends(get_db),
        jwt_payload: JWTPayload = Depends(require_role(UserRole.CLIENT))
):
    """История заказов текущего клиента."""
    return await order_crud.get_by_customer(db, jwt_payload.sub)


@router.patch("/items/{item_id}/confirm", status_code=status.HTTP_200_OK)
async def confirm_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    jwt_payload: JWTPayload = Depends(require_role(UserRole.PARTNER))
):
    """Партнёр подтверждает наличие картины в заказе."""
    crud = OrderCRUD()
    try:
        item = await crud.confirm_order_item(db, item_id, jwt_payload.sub)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not item:
        raise HTTPException(status_code=404, detail="Order item not found")

    return {"message": "Item confirmed successfully", "item_id": item.id}


@router.patch("/{order_id}/pay", response_model=OrderRead)
async def pay_order(
        order_id: UUID,
        db: AsyncSession = Depends(get_db),
        jwt_payload: JWTPayload = Depends(require_role(UserRole.CLIENT))
):
    """Оплата заказа. Доступна только если все позиции подтверждены."""
    crud = OrderCRUD()
    order = await crud.get_by_id(db, order_id)

    if not order or order.customer_id != jwt_payload.sub:
        raise HTTPException(404, "Order not found")

    if order.status != OrderStatus.CONFIRMED:
        raise HTTPException(
            status_code=400,
            detail="Cannot pay for order. Some items are not confirmed yet."
        )

    updated_order = await crud.update_status(db, order_id, OrderStatus.PAID)
    for item in updated_order.items:
        item.status = OrderItemStatus.PAID
    db.flush()
    return updated_order


@router.patch("/{order_id}/cancel", response_model=OrderRead)
async def cancel_order(
        order_id: UUID,
        db: AsyncSession = Depends(get_db),
        jwt_payload: JWTPayload = Depends(require_role(UserRole.CLIENT, UserRole.ADMIN))  # Может быть и клиент, и админ
):
    """Отмена заказа (клиентом или админом). Картины возвращаются в каталог."""
    crud = OrderCRUD()
    order = await crud.get_by_id(db, order_id)

    if not order:
        raise HTTPException(404, "Order not found")


    if order.status == OrderStatus.PAID:
        raise HTTPException(400, "Cannot cancel already paid order")

    updated_order = await crud.update_status(db, order_id, OrderStatus.CANCELED)
    return updated_order