import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from .db.connection import get_db, AsyncSessionLocal
from .db.crud import UserCRUD, UserRole
from .db.connection import engine
from .db.model import Base, User


async def main():
    async with AsyncSessionLocal() as db:
        crud = UserCRUD()
        user = await crud.create(
            db,
            "kirillpivovarov.andr@gmail.com",
            "1234",
            "Кирилл",
            "Пивоваров",
            UserRole.CLIENT,
            "89022371889"    
        )
        print(user.name + " " + user.surname)

async def init_models():
    async with engine.begin() as conn:
        # Необязательно: убирает старые таблицы перед созданием (ОСТОРОЖНО: удалит данные)
        # await conn.run_sync(Base.metadata.drop_all)
        
        # Создает все таблицы, описанные в моделях SQLAlchemy
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(main())
