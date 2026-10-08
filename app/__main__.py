import asyncio
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud.order import OrderCRUD
from .db.connection import get_db, AsyncSessionLocal
from .db.crud import UserCRUD, UserRole
from .db.connection import engine
from .db.model import Base, User, OrderStatus, Order


async def check_user_crud(db: AsyncSession) -> UUID:
    print("UserCRUD — создание пользователя")

    crud = UserCRUD()
    user = await crud.get_by_email(db, "kirillpivovarov.andr@gmail.com")
    await crud.delete(db, user)

    user = await crud.create(
        db,
        "kirillpivovarov.andr@gmail.com",
        "1234",
        "Кирилл",
        "Пивоваров",
        UserRole.CLIENT,
        "89022371889",
    )
    print(f"  ✓ Создан: {user.name} {user.surname}  id={user.id}")
    return user.id


async def check_order_crud(db: AsyncSession, customer_id: UUID) -> None:
    crud = OrderCRUD()

    order = await crud.create(
        db,
        customer_id=customer_id,
        status=OrderStatus.CREATED,
    )
    print(f"  ✓ Создан заказ id={order.id}, статус={order.status.value}")
    order_id = order.id

    found = await crud.get_by_id(db, Order, order_id)
    if found is None:
        print("  ❌ Заказ не найден")
        return
    print(f"  ✓ Найден: id={found.id}, статус={found.status.value}, "
          f"customer_id={found.customer_id}")

    updated = await crud.update_order(
        db,
        order_id=order_id,
        status=OrderStatus.CONFIRMED,
    )
    if updated is None:
        print("  ❌ Не удалось обновить заказ")
        return
    print(f"  ✓ Новый статус: {updated.status.value}")

    # ---------- DELETE ----------
    ok = await crud.delete(db, order)
    print(f"  ✓ Удаление: {'успешно' if ok else 'не удалось'}")

    # Проверка, что удалился
    after = await crud.get_by_id(db, Order,  order_id)
    print(f"  ✓ Заказ после удаления: {after} (ожидаем None)")


async def main():
    async with AsyncSessionLocal() as db:
        try:
            customer_id = await check_user_crud(db)

            await check_order_crud(db, customer_id)

            await db.commit()
            print("\n" + "=" * 60)
            print("Все проверки пройдены. Транзакция зафиксирована.")
            print("=" * 60)
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Ошибка: {type(e).__name__}: {e}")
            raise

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # ← раскомментировать
        await conn.run_sync(Base.metadata.create_all)


async def bootstrap():
    await init_models()          # создаём/пересоздаём таблицы
    await main()

if __name__ == "__main__":
    asyncio.run(bootstrap())

