from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.model import User, Client, Partner, UserRole, Cart
from app.schemas import ClientCreate, PartnerCreate
from app.db.crud.base import BaseCRUD
from app.services import hash_password

class UserCRUD(BaseCRUD):
    def __init__(self):
        super().__init__(User)

    async def create_client(
        self,
        db: AsyncSession,
        client_create: ClientCreate
    ) -> User:
        user = User(
            id=client_create.id,
            name=client_create.name,
            surname=client_create.surname,
        )

        user.client_profile = Client(
            phone=client_create.phone
        )

        db.add(user)
        await db.flush() 
        await db.refresh(user)
        return user

    async def create_partner(
        self,
        db: AsyncSession,
        partner_create: PartnerCreate
    ) -> User:
        user = User(
            id=partner_create.id,
            name=partner_create.name,
            surname=partner_create.surname,
        )

        user.partner_profile = Partner(
            phone=partner_create.phone,
            company_name=partner_create.company_name,
            address=partner_create.address
        )

        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user