"""
Быстрое наполнение БД тестовыми данными.

Запуск:
    python -m app.seed

Что создаётся:
  - 3 клиента       (UserRole.CLIENT)
  - 2 партнёра      (UserRole.PARTNER)
  - 1 админ         (UserRole.ADMIN)
  - 6 картин        (у партнёров)
  - 3 корзины       (по одной на клиента)
  - 4 позиции       в корзинах
  - 3 заказа        (в разных статусах)
  - 6 позиций       в заказах
"""
import asyncio
from decimal import Decimal

from sqlalchemy import select, delete, func

from app.db.connection import AsyncSessionLocal, engine
from app.db.crud import (
    UserCRUD,
    PaintingCRUD,
    OrderCRUD,
    OrderItemCRUD,
    UserRole
)
from app.db.model import (
    Base,
    User,
    Painting,
    Cart,
    CartItem,
    Order,
    OrderItem,

    PaintingStatus,
    OrderStatus,
    OrderItemType,
)


# Очистка БД
async def wipe(db) -> None:
    """Полная очистка всех таблиц (в правильном порядке)."""
    print(">>> Очистка таблиц...")
    for model in (OrderItem, Order, CartItem, Cart, Painting, User):
        await db.execute(delete(model))
    await db.commit()
    print("    Готово.")


# Пользователи
async def seed_users(db) -> dict:
    """Создаёт клиентов, партнёров и админа. Возвращает id по email."""
    print("\n>>> Создаём пользователей...")
    crud = UserCRUD()
    ids = {}

    # Клиенты
    for email, name, surname, phone in [
        ("ivan@example.com",   "Иван",   "Клиентов",     "+7-900-111-11-11"),
        ("maria@example.com",  "Мария",  "Покупателева", "+7-900-222-22-22"),
        ("sergey@example.com", "Сергей", "Заказчиков",   "+7-900-333-33-33"),
    ]:
        user = await crud.create(
            db, email, "1234", name, surname,
            UserRole.CLIENT, phone,
        )
        ids[email] = user.id
        print(f"    ✓ клиент:  {user.email}")

    # Партнёры
    for email, name, surname, phone, address, company in [
        ("petr@example.com", "Пётр",  "Партнёров",   "+7-900-444-44-44",
         "г. Самара, ул. Ленина, 1", "ООО «Арт-Галерея»"),
        ("olga@example.com", "Ольга", "Художникова", "+7-900-555-55-55",
         "г. Самара, ул. Мира, 10",  "ИП Художникова О.В."),
    ]:
        user = await crud.create(
            db, email, "1234", name, surname,
            UserRole.PARTNER, phone, address, company,
        )
        ids[email] = user.id
        print(f"    ✓ партнёр: {user.email}")

    # Админ
    admin = await crud.create(
        db, "admin@example.com", "1234", "Анна", "Админова",
        UserRole.ADMIN, "+7-900-666-66-66",
    )
    ids[admin.email] = admin.id
    print(f"    ✓ админ:   {admin.email}")

    return ids


# Картины
async def seed_paintings(db, user_ids: dict) -> dict:
    """Создаёт картины у партнёров. Возвращает {title: id}."""
    print("\n>>> Создаём картины...")
    crud = PaintingCRUD()
    ids = {}

    petr_id = user_ids["petr@example.com"]
    olga_id = user_ids["olga@example.com"]

    data = [
        (petr_id, "Утро в сосновом лесу", "И. И. Шишкин",      1889, 150000,  3000),
        (petr_id, "Девятый вал",          "И. К. Айвазовский", 1850, 200000,  4000),
        (petr_id, "Незнакомка",           "И. Н. Крамской",    1883, 170000,  3200),
        (olga_id, "Чёрный квадрат",       "К. С. Малевич",     1915, 1000000, 10000),
        (olga_id, "Бурлаки на Волге",     "И. Е. Репин",       1873, 180000,  3500),
        (olga_id, "Алёнушка",             "В. М. Васнецов",    1881, 160000,  3100),
    ]

    for partner_id, title, author, year, price, rent in data:
        painting = await crud.create(
            db,
            partner_id=partner_id,
            title=title,
            author=author,
            creation_year=year,
            price=Decimal(str(price)),
            rent_price=Decimal(str(rent)),
            status=PaintingStatus.AVAILABLE,
        )
        ids[title] = painting.id
        print(f"    ✓ {painting.title} ({painting.author})")

    return ids


# Корзины — напрямую через ORM (без CartCRUD / CartItemCRUD)
async def seed_carts(db, user_ids: dict, painting_ids: dict) -> None:
    """Создаёт корзины клиентов и позиции в них — через ORM."""
    print("\n>>> Создаём корзины...")

    # ---- Корзина Ивана: 2 картины ----
    cart1 = Cart(user_id=user_ids["ivan@example.com"])
    db.add(cart1)
    await db.flush()

    db.add(CartItem(cart_id=cart1.id,
                    painting_id=painting_ids["Утро в сосновом лесу"]))
    db.add(CartItem(cart_id=cart1.id,
                    painting_id=painting_ids["Девятый вал"]))
    print(f"    ✓ корзина Ивана: 2 позиции")

    # ---- Корзина Марии: 2 картины ----
    cart2 = Cart(user_id=user_ids["maria@example.com"])
    db.add(cart2)
    await db.flush()

    db.add(CartItem(cart_id=cart2.id,
                    painting_id=painting_ids["Чёрный квадрат"]))
    db.add(CartItem(cart_id=cart2.id,
                    painting_id=painting_ids["Алёнушка"]))
    print(f"    ✓ корзина Марии: 2 позиции")

    # ---- Корзина Сергея: пустая ----
    cart3 = Cart(user_id=user_ids["sergey@example.com"])
    db.add(cart3)
    await db.flush()
    print(f"    ✓ корзина Сергея: пустая")

    await db.flush()


# Заказы
async def seed_orders(db, user_ids: dict, painting_ids: dict) -> None:
    """Создаёт заказы и позиции заказов."""
    print("\n>>> Создаём заказы...")
    order_crud = OrderCRUD()
    item_crud = OrderItemCRUD()

    ivan_id  = user_ids["ivan@example.com"]
    maria_id = user_ids["maria@example.com"]

    # ---- Заказ №1: Иван, PAID (аренда + покупка) ----
    order1 = await order_crud.create(
        db, customer_id=ivan_id, status=OrderStatus.PAID,
    )
    await item_crud.create(
        db,
        order_id=order1.id,
        painting_id=painting_ids["Утро в сосновом лесу"],
        price=Decimal("3000.00"),
        type=OrderItemType.RENT,
        status=OrderStatus.PAID,
    )
    await item_crud.create(
        db,
        order_id=order1.id,
        painting_id=painting_ids["Девятый вал"],
        price=Decimal("200000.00"),
        type=OrderItemType.PURCHASE,
        status=OrderStatus.PAID,
    )
    print(f"    ✓ заказ #{order1.id} — Иван (PAID, 2 позиции)")

    # ---- Заказ №2: Мария, CONFIRMED ----
    order2 = await order_crud.create(
        db, customer_id=maria_id, status=OrderStatus.CONFIRMED,
    )
    await item_crud.create(
        db,
        order_id=order2.id,
        painting_id=painting_ids["Чёрный квадрат"],
        price=Decimal("1000000.00"),
        type=OrderItemType.PURCHASE,
        status=OrderStatus.CONFIRMED,
    )
    await item_crud.create(
        db,
        order_id=order2.id,
        painting_id=painting_ids["Алёнушка"],
        price=Decimal("3100.00"),
        type=OrderItemType.RENT,
        status=OrderStatus.CONFIRMED,
    )
    print(f"    ✓ заказ #{order2.id} — Мария (CONFIRMED, 2 позиции)")

    # ---- Заказ №3: Иван, CREATED ----
    order3 = await order_crud.create(
        db, customer_id=ivan_id, status=OrderStatus.CREATED,
    )
    await item_crud.create(
        db,
        order_id=order3.id,
        painting_id=painting_ids["Незнакомка"],
        price=Decimal("3200.00"),
        type=OrderItemType.RENT,
        status=OrderStatus.CREATED,
    )
    await item_crud.create(
        db,
        order_id=order3.id,
        painting_id=painting_ids["Бурлаки на Волге"],
        price=Decimal("3500.00"),
        type=OrderItemType.RENT,
        status=OrderStatus.CREATED,
    )
    print(f"    ✓ заказ #{order3.id} — Иван (CREATED, 2 позиции)")



# Сводка
async def print_summary(db) -> None:
    print("\n" + "=" * 60)
    print("СВОДКА")
    print("=" * 60)

    for model, name in (
        (User,      "users"),
        (Painting,  "paintings"),
        (Cart,      "carts"),
        (CartItem,  "cart_items"),
        (Order,     "orders"),
        (OrderItem, "order_items"),
    ):
        n = await db.scalar(select(func.count()).select_from(model))
        print(f"  {name:15} {n}")


# Точка входа
async def main() -> None:
    async with AsyncSessionLocal() as db:
        try:
            await wipe(db)

            user_ids     = await seed_users(db)
            painting_ids = await seed_paintings(db, user_ids)
            # await seed_carts(db, user_ids, painting_ids)
            await seed_orders(db, user_ids, painting_ids)

            await db.commit()
            print("\n>>> Транзакция зафиксирована.")

            await print_summary(db)

            print("\n" + "=" * 60)
            print("ГОТОВО")
            print("=" * 60)

        except Exception as e:
            await db.rollback()
            print(f"\n   ОШИБКА: {type(e).__name__}: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())