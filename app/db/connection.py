from os import getenv
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{getenv('DB_USER')}:{getenv('DB_PASSWORD')}"
    f"@{getenv('DB_HOST')}:{getenv('DB_PORT')}/{getenv('DB_NAME')}"
)

engine = create_async_engine(DATABASE_URL,
                       echo=False,
                       future=True,
                       pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session