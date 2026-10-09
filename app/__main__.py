import asyncio
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud.order import OrderCRUD
from app.db.crud.orderItem import OrderItemCRUD
from app.db.crud.painting import PaintingCRUD, painting_list_available
from .db.connection import get_db, AsyncSessionLocal
from .db.crud import UserCRUD, UserRole
from .db.connection import engine
from .db.model import Base, User, OrderStatus, Order, PaintingStatus, Painting, OrderItemType, OrderItem


async def check_user_crud(db: AsyncSession) -> UUID:
    print("1. UserCRUD — создание пользователя\n")

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
    print(f"  Создан: {user.name} {user.surname}  id={user.id}")
    return user.id


async def create_partner(db: AsyncSession) -> UUID:
    print("\n2. UserCRUD — создание партнёра\n")

    crud = UserCRUD()

    existing = await crud.get_by_email(db, "partner@example.com")
    if existing is not None:
        await crud.delete(db, existing)
        print(f"  → Удалён старый {existing.email}")

    partner = await crud.create(
        db,
        "partner@example.com",
        "1234",
        "Пётр",
        "Партнёров",
        UserRole.PARTNER,
        "89005554433",
        "г. Самара, ул. Ленина, 1",
        "ООО «Арт-Галерея»",
    )
    print(f"  Создан партнёр: {partner.name} {partner.surname}  id={partner.id}")
    return partner.id


async def check_order_crud(db: AsyncSession, customer_id: UUID):
    crud = OrderCRUD()
    print("\n4. OrderCRUD — работа с заказами\n")
    # CREATE
    order = await crud.create(
        db,
        customer_id=customer_id,
        status=OrderStatus.CREATED,
    )
    print(f"   Создан заказ id={order.id}, статус={order.status.value}")
    order_id = order.id

    found = await crud.get_by_id(db, Order, order_id)
    if found is None:
        print("  Заказ не найден")
        return
    print(f"  Найден: id={found.id}, статус={found.status.value}, "
          f"customer_id={found.customer_id}")

    # UPDATE
    updated = await crud.update_order(
        db,
        order_id=order_id,
        status=OrderStatus.CONFIRMED,
    )
    if updated is None:
        print("   Не удалось обновить заказ")
        return
    print(f"   Новый статус: {updated.status.value}")

    # # DELETE
    # order = await crud.get_by_id(db, Order, order_id)
    # if order is None:
    #     return
    #
    # ok = await crud.delete(db, order)
    # print(f"   Удаление: {'успешно' if ok else 'не удалось'}")
    #
    # # Проверка, что удалился
    # after = await crud.get_by_id(db, Order,  order_id)
    # print(f"    Заказ после удаления: {after} (ожидаем None)")
    return order_id


async def check_painting_crud(db: AsyncSession, partner_id: UUID) -> UUID:
    print("\n3. PaintingCRUD — работа с картинами\n")
    crud = PaintingCRUD()

    # CREATE
    painting = await crud.create(
        db,
        partner_id=partner_id,
        title="Утро в сосновом лесу",
        author="И. И. Шишкин",
        creation_year=1889,
        price=Decimal("150000.00"),
        rent_price=Decimal("3000.00"),
    )
    print(f"  Создана картина: {painting.title} ({painting.author})")
    print(f"    id={painting.id}, статус={painting.status.value}")
    painting_id = painting.id

    # READ
    found = await crud.get_by_id(db, Painting, painting_id)
    if found is None:
        print("  Картина не найдена")
        return painting_id
    print(f"  Найдена: {found.title}, статус={found.status.value}")

    # LIST
    all_paintings = await crud.get_by_partner(db, partner_id)
    print(f"  Картин у партнёра: {len(all_paintings)}")
    for p in all_paintings:
        print(f"    - {p.title} ({p.author}), {p.price} ₽")

    # LIST
    available = await painting_list_available(db)
    print(f"  Доступных картин в каталоге: {len(available)}")

    # UPDATE
    updated = await crud.update_status(db, painting_id, PaintingStatus.RENTED)
    if updated is None:
        print("  Не удалось обновить статус")
    else:
        print(f"  Новый статус: {updated.status.value}")

    return painting_id


async def check_order_item_crud(
    db: AsyncSession,
    order_id: UUID,
    painting_id: UUID,
):
    print("\n5. OrderItemCRUD — работа с позициями заказа\n")

    crud = OrderItemCRUD()

    # CREATE
    item = await crud.create(
        db,
        order_id=order_id,
        painting_id=painting_id,
        price=Decimal("3000.00"),
        type=OrderItemType.RENT,
    )
    print(f"    Создана позиция id={item.id}")
    print(f"    order_id={item.order_id}, painting_id={item.painting_id}")
    print(f"    type={item.type.value}, status={item.status.value}, "
          f"price={item.price}")
    item_id = item.id

    # READ
    found = await crud.get_by_id(db, OrderItem, item_id)
    if found is None:
        print("     Позиция не найдена")
        return
    print(f"    Найдена позиция: {found.id}")

    # LIST
    items = await crud.get_by_order(db, order_id)
    print(f"    Позиций в заказе: {len(items)}")

    by_painting = await crud.get_by_painting(db, painting_id)
    print(f"    Позиций с этой картиной: {len(by_painting)}")

    #  UPDATE STATUS
    updated = await crud.update_status(
        db, item_id, OrderStatus.CONFIRMED
    )
    if updated is None:
        print("     Не удалось обновить статус")
    else:
        print(f"    Новый статус: {updated.status.value}")

    # DELETE
    ok = await crud.delete(db, found)
    print(f"    Удаление: {'успешно' if ok else 'не удалось'}")

    after = await crud.get_by_id(db, OrderItem, item_id)
    print(f"    После удаления: {after} (ожидаем None)")


async def main():
    async with AsyncSessionLocal() as db:
        try:
            customer_id = await check_user_crud(db)
            partner_id = await create_partner(db)
            painting_id = await check_painting_crud(db, partner_id)
            order_id = await check_order_crud(db, customer_id)

            await check_order_item_crud(db, order_id, painting_id)

            await db.commit()
            print("\nВсе проверки пройдены. Транзакция зафиксирована.\n")

        except Exception as e:
            await db.rollback()
            print(f"\n Ошибка: {type(e).__name__}: {e}")
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

