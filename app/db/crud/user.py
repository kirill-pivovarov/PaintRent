from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.model import User, ClientProfile, PartnerProfile, UserRole, Cart
from app.db.crud.base import BaseCRUD
from app.core import hash_password

class UserCRUD(BaseCRUD):
    def __init__(self):
        super().__init__(User)

    async def create(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        name: str,
        surname: str,
        role: UserRole,
        phone_number: str | None=None,
        address: str | None=None,
        company_name: str | None=None
    ) -> User:
        user = User(
            email=email,
            password_hash=hash_password(password),
            name=name,
            surname=surname,
            role=role
        )

        if role == UserRole.CLIENT:
            user.client_profile = ClientProfile(phone_number=phone_number)
        elif role == UserRole.PARTNER:
            user.partner_profile = PartnerProfile(
                phone_number=phone_number,
                company_name=company_name,
                address=address
            )

        user.cart = Cart()

        db.add(user)
        await db.flush() 
        await db.refresh(user)
        return user

    async def get_by_email(
        self,
        db: AsyncSession,
        email: str
    ) -> User:
        stmt = select(User).where(User.email == email)
        return await db.scalar(stmt)

    