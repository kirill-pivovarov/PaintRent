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
    