from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List

from app.api.deps import get_db, get_current_user, require_role
from app.db.crud.order import OrderCRUD
from app.db.model import User, UserRole, Order, Painting, PaintingStatus, OrderItemType, OrderStatus
from app.schemas.order import OrderCreate, OrderRead

router = APIRouter(prefix="/orders", tags=["Orders"])


# ЗАГЛУШКА: имитация того, что корзина уже работает
async def get_paintings_from_cart(db: AsyncSession, user_id: UUID) -> list[Painting]:
    """
    В реальности здесь будет запрос к CartCRUD.
    Пока мы просто достаем все доступные картины из базы (для тестов).
    """
    result = await db.execute(
        select(Painting).where(Painting.status == PaintingStatus.AVAILABLE).limit(1)
    )
    return list(result.scalars().all())


@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
        data: OrderCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(require_role(UserRole.CLIENT))
):
    """
    Создать заказ из корзины.
    (Корзина пока имитируется, но логика заказа полностью рабочая).
    """
    crud = OrderCRUD()

    paintings = await get_paintings_from_cart(db, current_user.id)
    if not paintings:
        raise HTTPException(status_code=400, detail="Cart is empty or no available paintings")

    try:
        order = await crud.create_order_from_paintings(
            db,
            customer_id=current_user.id,
            paintings=paintings,
            order_type=data.type
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 3. Подгружаем заказ с позициями для ответа
    # (нам нужно обновить объект, чтобы подтянулись created_at и items)
    stmt = select(Order).where(Order.id == order.id).options(selectinload(Order.items))
    result = await db.execute(stmt)
    return result.scalar_one()


@router.get("/my", response_model=List[OrderRead])
async def get_my_orders(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(require_role(UserRole.CLIENT))
):
    """История заказов текущего клиента."""
    crud = OrderCRUD()
    return await crud.get_by_customer(db, current_user.id)


@router.patch("/items/{item_id}/confirm", status_code=status.HTTP_200_OK)
async def confirm_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.PARTNER))
):
    """Партнёр подтверждает наличие картины в заказе."""
    crud = OrderCRUD()
    try:
        item = await crud.confirm_order_item(db, item_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not item:
        raise HTTPException(status_code=404, detail="Order item not found")

    return {"message": "Item confirmed successfully", "item_id": item.id}


@router.patch("/{order_id}/pay", response_model=OrderRead)
async def pay_order(
        order_id: UUID,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(require_role(UserRole.CLIENT))
):
    """Оплата заказа. Доступна только если все позиции подтверждены."""
    crud = OrderCRUD()
    order = await crud.get_by_id(db, order_id)

    if not order or order.customer_id != current_user.id:
        raise HTTPException(404, "Order not found")

    if order.status != OrderStatus.CONFIRMED:
        raise HTTPException(
            status_code=400,
            detail="Cannot pay for order. Some items are not confirmed yet."
        )

    updated_order = await crud.update_status(db, order_id, OrderStatus.PAID)
    return updated_order


@router.patch("/{order_id}/cancel", response_model=OrderRead)
async def cancel_order(
        order_id: UUID,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)  # Может быть и клиент, и админ
):
    """Отмена заказа (клиентом или админом). Картины возвращаются в каталог."""
    crud = OrderCRUD()
    order = await crud.get_by_id(db, order_id)

    if not order:
        raise HTTPException(404, "Order not found")

    if current_user.role not in (UserRole.ADMIN, UserRole.CLIENT) or \
            (current_user.role == UserRole.CLIENT and order.customer_id != current_user.id):
        raise HTTPException(403, "Not allowed to cancel this order")

    if order.status == OrderStatus.PAID:
        raise HTTPException(400, "Cannot cancel already paid order")

    updated_order = await crud.update_status(db, order_id, OrderStatus.CANCELED)
    return updated_order