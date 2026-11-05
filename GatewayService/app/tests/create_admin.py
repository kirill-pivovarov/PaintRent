import asyncio
from app.db.connection import AsyncSessionLocal
from app.db.crud.user import UserCRUD
from app.db.model import UserRole
from app.core.security import hash_password

async def main():
    async with AsyncSessionLocal() as db:
        crud = UserCRUD()
        # Проверяем, нет ли уже такого
        existing = await crud.get_by_email(db, "admin@example.com")
        if existing:
            print("Админ уже существует!")
            return

        await crud.create(
            db,
            email="admin@example.com",
            password=hash_password("admin123"),
            name="Главный",
            surname="Админ",
            role=UserRole.ADMIN
        )
        await db.commit()
        print("Админ успешно создан!")

if __name__ == "__main__":
    asyncio.run(main())