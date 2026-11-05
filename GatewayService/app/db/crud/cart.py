from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from uuid import UUID, uuid4

from sqlalchemy.orm import selectinload

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


    async def get_items(
            self,
            db: AsyncSession,
            cart: Cart,
    ) -> list[CartItem]:
        """Вернуть список позиций корзины."""
        stmt = select(CartItem).where(CartItem.cart_id == cart.id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_or_create_by_user(self, db: AsyncSession, user_id: UUID) -> Cart:
        """Получает корзину пользователя или создает новую, если ее нет."""
        # Загружаем корзину вместе с позициями и картинами
        stmt = (
            select(Cart)
            .where(Cart.user_id == user_id)
            .options(selectinload(Cart.items).selectinload(CartItem.painting))
        )
        result = await db.execute(stmt)
        cart = result.scalar_one_or_none()

        if not cart:
            cart = Cart(user_id=user_id)
            db.add(cart)
            await db.flush()
            # Перезагружаем, чтобы подтянулись пустые items
            stmt = select(Cart).where(Cart.id == cart.id).options(selectinload(Cart.items))
            result = await db.execute(stmt)
            cart = result.scalar_one()

        return cart

    async def add_item(self, db: AsyncSession, cart_id: UUID, painting_id: UUID) -> CartItem:
        """Добавляет картину в корзину."""
        item = CartItem(cart_id=cart_id, painting_id=painting_id)
        db.add(item)
        await db.flush()
        return item

    async def remove_item(self, db: AsyncSession, cart_id: UUID, painting_id: UUID) -> bool:
        """Удаляет картину из корзины."""
        stmt = select(CartItem).where(
            CartItem.cart_id == cart_id,
            CartItem.painting_id == painting_id
        )
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()

        if item:
            await db.delete(item)
            await db.flush()
            return True
        return False

    async def clear_cart(self, db: AsyncSession, cart_id: UUID):
        """Полностью очищает корзину."""
        await db.execute(delete(CartItem).where(CartItem.cart_id == cart_id))
        await db.flush()
