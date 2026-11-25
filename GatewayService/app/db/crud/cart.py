from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from uuid import UUID, uuid4

from app.db.model import Cart, CartItem, Painting
from app.db.crud import BaseCRUD
from app.schemas.cart import CartItemCreate 

class CartCRUD(BaseCRUD):
    def __init__(self):
        super().__init__(Cart)

    async def get_by_user_id(
        self, 
        db: AsyncSession,
        user_id: UUID
    ) -> Cart | None:
        stmt = select(Cart).where(Cart.user_id == user_id)
        return await db.scalar(stmt)

    async def get_item_by_id(
        self,
        db: AsyncSession,
        item_id: UUID
    ) -> CartItem | None:
        return await db.get(CartItem, item_id)


    async def add_item(
        self,
        db: AsyncSession,
        cart_id: UUID, 
        cart_item_create: CartItemCreate
    ) -> CartItem:
        cart_item = CartItem(**cart_item_create.model_dump(exclude_unset=True))
        cart_item.cart = await db.get(Cart, cart_id)
        cart_item.painting = await db.get(Painting, cart_item_create.painting_id)

        db.add(cart_item)
        await db.flush()
        await db.refresh(cart_item)
        return cart_item

    async def clear_cart(
        self, 
        db: AsyncSession,
        cart_id: UUID
    ) -> bool:
        stmt = delete(CartItem).where(CartItem.cart_id == cart_id)
        result = await db.execute(stmt)
        await db.flush()
        return result.rowcount > 0

    async def remove_item(
            self,
            db: AsyncSession,
            cart_item_id: UUID,
    ) -> bool:
        """Удалить одну позицию из корзины. Возвращает True, если что-то удалено."""
        stmt = (
            delete(CartItem)
            .where(CartItem.id == cart_item_id)
        )
        result = await db.execute(stmt)
        await db.flush()
        return result.rowcount > 0

    async def get_items(
            self,
            db: AsyncSession,
            cart_id: UUID,
    ) -> list[CartItem]:
        """Вернуть список позиций корзины."""
        stmt = select(CartItem).where(CartItem.cart_id == cart_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())


