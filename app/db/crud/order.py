from dataclasses import dataclass
from typing import Sequence
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.model import Painting, Order, OrderStatus
from app.db.crud.base import BaseCRUD


class OrderCRUD(BaseCRUD):
    async def create(self,
                     db: AsyncSession,
                     *,
                     customer_id: UUID,
                     status: OrderStatus = OrderStatus.CREATED,
                     ) -> Order:
        order = Order(customer_id=customer_id, status=status, )
        db.add(order)

        await db.flush()
        await db.refresh(order)

        await db.commit()
        return order


    async def update(self,
                           db: AsyncSession,
                           order_id: UUID,
                           **kwargs) -> Order | None:
        await db.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(**kwargs)
        )

        await db.commit()
        return await self.get_by_id(db, order_id)
