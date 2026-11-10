from pydantic import BaseModel, EmailStr, ConfigDict, Field  # @validator
from pydantic_extra_types.phone_numbers import PhoneNumber

from uuid import UUID
from app.db.model import UserRole

class UserBase(BaseModel):
    name: str
    surname: str

class ClientProfile(UserBase):
    phone: PhoneNumber | None = None

class PartnerProfile(UserBase):
    phone: PhoneNumber | None = None
    company_name: str | None = None
    address: str | None = None


class ClientCreate(ClientProfile):
    id: UUID

class PartnerCreate(PartnerProfile):
    id: UUID


ClientOnboardingForm = ClientProfile
PartnerOnboardingForm = PartnerProfile


