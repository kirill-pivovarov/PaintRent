from typing import TypeVar, Type, Optional, Generic, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.model import Base


ModelType = TypeVar("ModelType", bound=Base)


class BaseCRUD(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get_by_id(
        self,
        db: AsyncSession,
        id: UUID
    ) -> Optional[ModelType]:
        return await db.get(self.model, id)
    
    async def delete(
        self,
        db: AsyncSession,
        obj: ModelType
    ) -> bool:
        if obj is None:
            return False
        await db.delete(obj)
        await db.flush()
        return True
