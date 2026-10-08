from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID, uuid4

from app.db.model import User, ClientProfile, PartnerProfile, UserRole
from app.db.crud.base import BaseCRUD
from app.core import hash_password, verify_password

class UserCRUD(BaseCRUD):

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
        print(user.id)
        db.add(user)
        await db.flush()
        await db.refresh(user)
        print(user.id)


        if role == UserRole.CLIENT:
            profile = ClientProfile(
                user_id=user.id,
                phone_number=phone_number
            )
        elif role == UserRole.PARTNER:
            profile = PartnerProfile(
                user_id=user.id,
                phone_number=phone_number,
                company_name=company_name
            )

        db.add(profile)
        await db.commit()

        return user