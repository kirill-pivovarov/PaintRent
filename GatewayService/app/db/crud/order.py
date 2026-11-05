from decimal import Decimal
from uuid import UUID

from sqlalchemy import update,select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from GatewayService.app.db.model import Order, OrderStatus, OrderItem, OrderItemStatus, PaintingStatus, OrderItemType, Painting
from GatewayService.app.db.crud.base import BaseCRUD


class OrderCRUD(BaseCRUD[Order]):
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

        return await self.get_by_id(db, order_id)

    async def create_order_from_paintings(
            self,
            db: AsyncSession,
            customer_id: UUID,
            paintings: list[Painting],
            order_type: OrderItemType = OrderItemType.RENT
    ) -> Order:
        """
        Создает заказ из списка картин.
        Проверяет статус, создает Order и OrderItem, меняет статус картин на RENTED.
        """
        order = Order(
            customer_id=customer_id,
            status=OrderStatus.CREATED,
            total_price=Decimal("0.00")
        )
        db.add(order)
        await db.flush()

        total_price = Decimal("0.00")

        for painting in paintings:
            if painting.status != PaintingStatus.AVAILABLE:
                raise ValueError(f"Painting '{painting.title}' is not available")

            price = painting.rent_price if order_type == OrderItemType.RENT else painting.price

            order_item = OrderItem(
                order_id=order.id,
                painting_id=painting.id,
                type=order_type,
                status=OrderItemStatus.CREATED,
                price=price
            )
            db.add(order_item)
            total_price += price

            painting.status = PaintingStatus.RENTED

        order.total_price = total_price
        await db.flush()

        stmt = select(Order).where(Order.id == order.id).options(selectinload(Order.items))
        result = await db.execute(stmt)
        return result.scalar_one()


    async def confirm_order_item(
            self,
            db: AsyncSession,
            item_id: UUID,
            partner_id: UUID
    ) -> OrderItem | None:
        """
        Подтверждение наличия картины партнёром.
        Если все подтвердили - заказ становится CONFIRMED.
        """
        stmt = (
            select(OrderItem)
            .where(OrderItem.id == item_id)
            .options(
                selectinload(OrderItem.order).selectinload(Order.items),
                selectinload(OrderItem.painting)
            )
        )
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            return None

        if item.painting.partner_id != partner_id:
            raise ValueError("You can only confirm your own paintings")

        if item.order.status == OrderStatus.CANCELED:
            raise ValueError("Cannot confirm items in canceled order")

        item.status = OrderItemStatus.CONFIRMED
        await db.flush()

        all_confirmed = all(i.status == OrderItemStatus.CONFIRMED for i in item.order.items)

        if all_confirmed:
            item.order.status = OrderStatus.CONFIRMED
            await db.flush()

        return item

    async def update_status(self, db: AsyncSession, order_id: UUID, new_status: OrderStatus):
        """Меняет статус заказа. При отмене — возвращает картины в продажу."""
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items).selectinload(OrderItem.painting))
        )
        result = await db.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            return None

        # Логика отмены: если отменяем, возвращаем картины в продажу
        if new_status == OrderStatus.CANCELED:
            for item in order.items:
                item.status = OrderItemStatus.CANCELED
                item.painting.status = PaintingStatus.AVAILABLE

        order.status = new_status
        await db.flush()

        # Перезагружаем, чтобы вернуть в ответе с items
        stmt = select(Order).where(Order.id == order.id).options(selectinload(Order.items))
        result = await db.execute(stmt)
        return result.scalar_one()


    async def get_by_customer(self, db: AsyncSession, customer_id: UUID) -> list[Order]:
        """Возвращает все заказы конкретного клиента с загруженными позициями."""
        stmt = (
            select(Order)
            .where(Order.customer_id == customer_id)
            .options(selectinload(Order.items))  # Подгружаем позиции
            .order_by(Order.created_at.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())