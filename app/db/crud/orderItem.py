from uuid import UUID
from decimal import Decimal

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.model import OrderItem, OrderItemType, OrderStatus
from app.db.crud.base import BaseCRUD


class OrderItemCRUD(BaseCRUD):
    model = OrderItem
    def __init__(self):
        super().__init__(OrderItem)

    async def create(
        self,
        db: AsyncSession,
        order_id: UUID,
        painting_id: UUID,
        price: Decimal,
        type: OrderItemType = OrderItemType.RENT,
        status: OrderStatus = OrderStatus.CREATED,
    ) -> OrderItem:
        item = OrderItem(
            order_id=order_id,
            painting_id=painting_id,
            type=type,
            status=status,
            price=price,
        )
        db.add(item)
        await db.flush()
        await db.refresh(item)
        await db.commit()
        return item


    async def update(
        self,
        db: AsyncSession,
        obj: OrderItem,
    ) -> OrderItem:
        if obj is None:
            raise ValueError("update: obj is None")
        merged = await db.merge(obj)
        await db.commit()
        await db.refresh(merged)
        return merged


    async def update_status(
        self,
        db: AsyncSession,
        order_item_id: UUID,
        status: OrderStatus,
    ) -> OrderItem | None:

        result = await db.execute(
            update(OrderItem)
            .where(OrderItem.id == order_item_id)
            .values(status=status)
            .returning(OrderItem.id)
        )

        updated_id = result.scalar_one_or_none()
        await db.commit()
        if updated_id is None:
            return None
        return await self.get_by_id(db, OrderItem, updated_id)


    async def get_by_order(
        self,
        db: AsyncSession,
        order_id: UUID,
    ) -> list[OrderItem]:
        stmt = (
            select(OrderItem)
            .where(OrderItem.order_id == order_id)
            .order_by(OrderItem.id)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_painting(
        self,
        db: AsyncSession,
        painting_id: UUID,
    ) -> list[OrderItem]:
        stmt = (
            select(OrderItem)
            .where(OrderItem.painting_id == painting_id)
            .order_by(OrderItem.id)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def list_by_status(
        self,
        db: AsyncSession,
        status: OrderStatus,
    ) -> list[OrderItem]:
        stmt = (
            select(OrderItem)
            .where(OrderItem.status == status)
            .order_by(OrderItem.id)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())