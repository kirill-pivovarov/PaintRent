from datetime import datetime 
from uuid import UUID

from pydantic import BaseModel, field_serializer

from app.db import UserRole

class JWTPayload(BaseModel):
    sub: UUID
    role: UserRole
    exp: datetime

    @field_serializer('sub')
    def serialize_sub(self, v: UUID, _info):
        return str(v)  

    @field_serializer("exp")
    def serialiize_exp(self, v: datetime, _info):
        return int(v.timestamp())