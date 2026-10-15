from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.model import Painting, PaintingStatus
from app.db.crud.base import BaseCRUD


async def painting_list_available(db: AsyncSession) -> list[Painting]:
    stmt = (
        select(Painting)
        .where(Painting.status == PaintingStatus.AVAILABLE)
        .order_by(Painting.title)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


class PaintingCRUD(BaseCRUD):
    model = Painting
    title: str | None = None
    author: str | None = None
    price: Decimal | None = None
    rent_price: Decimal | None = None
    creation_year: int | None = None
    status: PaintingStatus | None = None

    def __init__(self):
        super().__init__(Painting)

    async def create(
        self,
        db: AsyncSession,
        partner_id: UUID,
        title: str,
        author: str,
        price,
        rent_price,
        creation_year: int | None = None,
        status: PaintingStatus = PaintingStatus.AVAILABLE,
    ) -> Painting:
        painting = Painting(
            partner_id=partner_id,
            title=title,
            author=author,
            creation_year=creation_year,
            price=price,
            rent_price=rent_price,
            status=status,
        )
        db.add(painting)

        await db.flush()
        await db.refresh(painting)

        return painting

    async def update_paintings(self, db, painting_id, **kwargs):
        painting = await self.get_by_id(db, painting_id)

        if painting is None:
            return None

        for k, v in kwargs.items():
            setattr(painting, k, v)

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

    async def update_status(self, db, painting_id, status):
        return await self.update_paintings(db, painting_id, status=status)