from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from uuid import UUID, uuid4

from app.db.model import Cart, CartItem, Painting
from app.db.crud import BaseCRUD

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

    async def add_item(
        self,
        db: AsyncSession,
        cart: Cart,
        painting: Painting
    ) -> CartItem:
        cart_item = CartItem()
        cart_item.cart = cart
        cart_item.painting = painting

        db.add(cart_item)
        await db.flush()
        await db.refresh(cart_item)
        return cart_item

    async def clear_cart(
        self, 
        db: AsyncSession,
        cart: Cart
    ) -> Cart:

        stmt = delete(CartItem).where(CartItem.cart_id == cart.id)
        await db.execute(stmt)
        await db.flush()
        await db.refresh(cart)
        return cart

    async def remove_item(
            self,
            db: AsyncSession,
            cart: Cart,
            painting_id: UUID,
    ) -> bool:
        """Удалить одну позицию из корзины. Возвращает True, если что-то удалено."""
        stmt = (
            delete(CartItem)
            .where(CartItem.cart_id == cart.id,
                   CartItem.painting_id == painting_id)
        )
        result = await db.execute(stmt)
        await db.flush()
        return result.rowcount > 0

    async def get_items(
            self,
            db: AsyncSession,
            cart: Cart,
    ) -> list[CartItem]:
        """Вернуть список позиций корзины."""
        stmt = select(CartItem).where(CartItem.cart_id == cart.id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def delete_cart(
            self,
            db: AsyncSession,
            cart: Cart,
    ) -> bool:
        """Удалить корзину целиком (с позициями — каскадно)."""
        if cart is None:
            return False
        await db.delete(cart)
        await db.flush()
        return True
