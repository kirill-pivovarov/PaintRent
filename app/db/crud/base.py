from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import TypeVar, Type, Optional
from uuid import UUID, uuid4

from app.db.model import Base


ModelType = TypeVar("ModelType", bound=Base)

class BaseCRUD:

    async def get_by_id(
        self,
        db: AsyncSession,
        entity: Type[ModelType],
        id: UUID
    ) -> Optional[ModelType]:
        return await db.get(entity, id)
    
    async def delete(
        self,
        db: AsyncSession,
        obj: Base
    ) -> bool:
        if obj is None:
            return False
        await db.delete(obj)
        await db.commit()
        return True


    async def update(
        self,
        db: AsyncSession,
        obj: ModelType
    ) -> ModelType | None:
        if obj is None:
            raise ValueError("update: obj is None")
        merged_obj = await db.merge(obj)
        await db.commit()
        await db.refresh(merged_obj)
        return merged_obj