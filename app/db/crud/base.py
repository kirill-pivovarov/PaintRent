from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar, Type, Optional
from uuid import UUID

from app.db.model import Base


ModelType = TypeVar("ModelType", bound=Base)

class BaseCRUD:
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get_by_id(
        self,
        db: AsyncSession,
        id: UUID) -> Optional[ModelType]:  # *, entity: Type[ModelType] = None
        return await db.get(self.model, id)
        # if entity is not None:
        #     return await db.get(self.model, id)
        # else:
        #     return await db.get(entity, id)

    
    async def delete(
        self,
        db: AsyncSession,
        obj: Base
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
    ) -> ModelType | None:
        if obj is None:
            raise ValueError("update: obj is None")
        merged_obj = await db.merge(obj)

        await db.refresh(merged_obj)
        return merged_obj