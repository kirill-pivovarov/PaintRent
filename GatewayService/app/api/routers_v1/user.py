from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.model import UserRole, Client
from app.schemas import (
    JWTPayload,
    ClientOnboardingForm,
    PartnerOnboardingForm,
    ClientProfile,
    ClientCreate,
    ClientUpdate,
    ClientRead,
    PartnerUpdate,
    PartnerCreate,
    PartnerProfile,
    PartnerRead
) 
from app.api.deps import get_jwt_payload, require_role
from app.db.deps import get_db
from app.db.crud.user import user_crud

clients_router = APIRouter(prefix="/clients", tags=["Users"], dependencies=[Depends(require_role(UserRole.CLIENT))])
partners_router = APIRouter(prefix="/partners", tags=["Users"], dependencies=[Depends(require_role(UserRole.PARTNER))])

@clients_router.post("/profile", status_code=status.HTTP_201_CREATED, summary="Регистрация нового пользователя")
async def register_client(
    client_form: ClientOnboardingForm,
    db: AsyncSession = Depends(get_db),
    jwt_payload: JWTPayload = Depends(get_jwt_payload)
):

    user_db = await user_crud.get_by_id(db, jwt_payload.sub)
    if user_db:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists.")

    user_db = await user_crud.create_client(db, ClientCreate(id=jwt_payload.sub, **client_form.model_dump()))


@clients_router.get("/profile", status_code=status.HTTP_200_OK, response_model=ClientRead)
async def get_client_profile(
    db: AsyncSession = Depends(get_db),
    jwt_payload: JWTPayload = Depends(get_jwt_payload)
) -> ClientRead:
    user = await db.get(Client, jwt_payload.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."    
        )

    return user

@clients_router.patch("/profile", status_code=status.HTTP_200_OK, response_model=ClientRead)
async def patch_client_profile(
    client_update: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    jwt_payload: JWTPayload = Depends(get_jwt_payload)
) -> ClientRead:
    user = await user_crud.get_by_id(db, jwt_payload.sub)
    if not user:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Profile not found."
        )

    new_client = await user_crud.update_client(db, jwt_payload.sub, client_update)
    return new_client


@partners_router.post("/profile", status_code=status.HTTP_201_CREATED)
async def register_partner(
    partner_form: PartnerOnboardingForm,
    db: AsyncSession = Depends(get_db),
    jwt_payload: JWTPayload = Depends(get_jwt_payload)
):
    user = await user_crud.get_by_id(db, jwt_payload.sub)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The user already registered."
        )

    user = await user_crud.create_partner(db, PartnerCreate(
        id=jwt_payload.sub,
        **partner_form.model_dump()
    ))


@partners_router.get("/profile", status_code=status.HTTP_200_OK, response_model=PartnerRead)
async def get_partner_profile(
    db: AsyncSession = Depends(get_db),
    jwt_payload: JWTPayload = Depends(get_jwt_payload)
) -> PartnerRead:
    user = await user_crud.get_by_id(db, jwt_payload.sub)
    if not user:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "User not found."
        )
    return user


@partners_router.patch("/profile", status_code=status.HTTP_200_OK, response_model=PartnerRead)
async def patch_partner_profile(
    partner_update: PartnerUpdate,
    db: AsyncSession = Depends(get_db),
    jwt_payload: JWTPayload = Depends(get_jwt_payload)
) -> PartnerRead:
    user = await user_crud.get_by_id(db, jwt_payload.sub)
    if not user:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Profile not found."
        )

    new_partner = await user_crud.update_partner(db, jwt_payload.sub, partner_update)
    return new_partner