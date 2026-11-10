from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.model import UserRole
from app.schemas import (
    JWTPayload,
    ClientOnboardingForm,
    ClientCreate
) 
from app.api.deps import get_jwt_payload, require_role
from app.db.deps import get_db
from app.db.crud.user import UserCRUD

clients_router = APIRouter(prefix="/users", tags=["Users"], dependencies=[Depends(require_role(UserRole.CLIENT))])

@clients_router.post("/register", status_code=status.HTTP_201_CREATED, summary="Регистрация нового пользователя")
async def register_client(
    client_form: ClientOnboardingForm,
    db: AsyncSession = Depends(get_db),
    jwt_payload: JWTPayload = Depends(require_role(UserRole.CLIENT))
):
    crud = UserCRUD()
    user_db = await crud.get_by_id(db, jwt_payload.sub)
    if user_db:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists.")

    user_db = await crud.create_client(db, ClientCreate(id=jwt_payload.sub, **client_form.model_dump()))
    