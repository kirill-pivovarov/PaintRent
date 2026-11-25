from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.model import Painting, PaintingStatus
from app.db.crud.base import BaseCRUD
from app.schemas.painting import PaintingUpdate, PaintingCreate


async def painting_list(
    db: AsyncSession,
    *,
    only_available: bool = False,
    order_by: str = "created_at_desc",
    ) -> list[Painting]:

    stmt = select(Painting)

    if only_available:
        stmt = stmt.where(Painting.status == PaintingStatus.AVAILABLE)

    stmt = stmt.order_by(
        Painting.title if order_by == "title" else Painting.created_at.desc()
    )

    result = await db.execute(stmt)
    return list(result.scalars().all())


class PaintingCRUD(BaseCRUD[Painting]):
    def __init__(self):
        super().__init__(Painting)

    async def create(
        self,
        db: AsyncSession,
        partner_id: UUID,
        painting_create: PaintingCreate
    ) -> Painting:
        painting = Painting(partner_id=partner_id, **painting_create.model_dump(exclude_unset=True))
        db.add(painting)

        await db.flush()
        await db.refresh(painting)

        return painting

    async def update(self, db, id, painting_update: PaintingUpdate) -> Painting:
        painting = await self.get_by_id(db, id)

        if painting is None:
            return None

        stmt = update(Painting)\
            .where(Painting.id == id)\
            .values(
                **painting_update.model_dump(exclude_unset=True)
            )\
            .returning(Painting)

        painting = (await db.execute(stmt)).scalar_one_or_none()
        await db.flush()
        return painting


    async def get_by_partner(
        self,
        db: AsyncSession,
        partner_id: UUID,
    ) -> list[Painting]:
        stmt = (
            select(Painting)
            .where(Painting.partner_id == partner_id)
            .order_by(Painting.created_at.desc())
        )
        result = await db.execute(stmt)

        return list(result.scalars().all())

    async def update_status(self, db, painting_id, status) -> Painting | None:
        return await self.update_paintings(db, painting_id, status=status)


painting_crud = PaintingCRUD()