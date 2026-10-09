from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.model import Order, OrderStatus
from app.db.crud.base import BaseCRUD


class OrderCRUD(BaseCRUD):
    def __init__(self):
        super().__init__(Order)

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

        return order


    async def update_order(self,
                           db: AsyncSession,
                           order_id: UUID,
                           **kwargs) -> Order | None:
        await db.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(**kwargs)
        )

        return await self.get_by_id(db, Order, order_id)
