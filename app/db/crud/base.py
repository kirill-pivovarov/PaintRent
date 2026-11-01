from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar, Type, Optional, Generic
from uuid import UUID

from app.db.model import Base


ModelType = TypeVar("ModelType", bound=Base)

class BaseCRUD(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get_by_id(
        self,
        db: AsyncSession,
        id: UUID) -> Optional[ModelType]:
        return await db.get(self.model, id)

    
    async def delete(
        self,
        db: AsyncSession,
        obj: ModelType | None
    ) -> bool:
        if obj is None:
            return False
        await db.delete(obj)
        await db.flush()
        return True


    async def update(
        self,
        db: AsyncSession,
        obj: ModelType
    ) -> ModelType:
        if obj is None:
            raise ValueError("update: obj is None")
        merged = await db.merge(obj)

        await db.flush()
        return merged