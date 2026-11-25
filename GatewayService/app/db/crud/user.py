from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from sqlalchemy import select, update
from uuid import UUID, uuid4

from app.db.model import User, Client, Partner, UserRole, Cart
from app.schemas import (
    ClientCreate,
    PartnerCreate, 
    ClientUpdate, 
    PartnerUpdate, 
    ClientProfile, 
    PartnerProfile,
    ClientRead,
    PartnerRead
)
from app.db.crud.base import BaseCRUD
from app.services import hash_password

class UserCRUD(BaseCRUD):
    def __init__(self):
        super().__init__(User)

    async def create_client(
        self,
        db: AsyncSession,
        client_create: ClientCreate
    ) -> Client:
        client = Client(**client_create.model_dump())
        client.cart = Cart(id=uuid4(), user_id=client.id)
        db.add(client)
        await db.flush() 
        await db.refresh(client)
        return client

    async def create_partner(
        self,
        db: AsyncSession,
        partner_create: PartnerCreate
    ) -> Partner:
        partner = Partner(**partner_create.model_dump())
        db.add(partner)
        await db.flush()
        await db.refresh(partner)
        return partner

    async def update_client(
        self,
        db: AsyncSession,
        id: UUID,
        client_update: ClientUpdate,
    ) -> Client:
        stmt = update(Client)\
            .where(Client.id == id)\
            .values(**client_update.model_dump(exclude_unset=True))\
            .returning(Client)
        try:
            client = (await db.execute(stmt)).scalar_one_or_none()
        except NoResultFound as e:
             return None
        await db.flush()
        return client


    async def update_partner(
        self,
        db: AsyncSession,
        id: UUID,
        partner_update: PartnerUpdate,
) -> Partner:
        stmt = update(Partner)\
            .where(Partner.id == id)\
            .values(**partner_update.model_dump(exclude_unset=True))\
            .returning(Partner)
        try:
            partner = (await db.execute(stmt)).scalar_one_or_none()
        except NoResultFound as e:
            return None
        await db.flush()
        return partner

        
user_crud = UserCRUD()