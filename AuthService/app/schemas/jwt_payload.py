from datetime import datetime 

from pydantic import BaseModel 

from app.db import UserRole

class JWTPayload(BaseModel):
    sub: str
    role: UserRole
    exp: datetime