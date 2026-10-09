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

        await db.commit()
        return painting


    async def update_paintings(
        self,
        db: AsyncSession,
        painting_id: UUID,
        **kwargs,
    ) -> Painting | None:
        await db.execute(
            update(Painting)
            .where(Painting.id == painting_id)
            .values(**kwargs)
        )
        await db.commit()
        return await self.get_by_id(db, Painting, painting_id)


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

        # будет ли такой вариант лучше? он тяжелее, но понтовей
        # partner = await db.get(PartnerProfile, partner_id)
        # paintings = partner.paintings

        return list(result.scalars().all())

    async def update_status(
        self,
        db: AsyncSession,
        painting_id: UUID,
        status: PaintingStatus,
    ) -> Painting | None:
        result = await db.execute(
            update(Painting)
            .where(Painting.id == painting_id)
            .values(status=status)
        )
        await db.commit()
        if result.rowcount == 0:
            return None  # объекта не было

        return await self.get_by_id(db, Painting, painting_id)