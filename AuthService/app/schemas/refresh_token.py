from pydantic import BaseModel, ConfigDict, SecretStr
from datetime import datetime
from uuid import UUID

class RefreshTokenCreate(BaseModel):
    user_id: UUID
    token_hash: str
    expires_at: datetime
    session_id: UUID

class RefreshTokenRead(BaseModel):
    id: UUID
    user_id: UUID
    token_hash: str
    expires_at: datetime
    session_id: UUID
    is_revoked: bool

    model_config = ConfigDict(from_attributes=True)


class RefreshTokenUpdate(BaseModel):
    expires_at: datetime | None = None
    is_revoked: bool | None = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str