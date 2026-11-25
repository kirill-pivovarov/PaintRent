from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role, get_jwt_payload
from app.db.deps import get_db
from app.db.model import User, UserRole
from app.schemas import JWTPayload
from app.db.crud.cart import CartCRUD
from app.schemas.cart import (
    CartRead, 
    CartItemCreate, 
    CartItemRead, 
    CartItemUpdate, 
    CartClearResponse
)

router = APIRouter(prefix="/cart", tags=["Cart"])
cart_crud = CartCRUD()


@router.get(
    "/",
    response_model=CartRead,
    status_code=status.HTTP_200_OK,
    summary="Получить корзину текущего клиента"
)
async def get_my_cart(
    db: AsyncSession = Depends(get_db),
    jwt_payload: JWTPayload = Depends(require_role(UserRole.CLIENT))
) -> CartRead:
    cart = await cart_crud.get_by_user_id(db, jwt_payload.sub)
    if not cart:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )
    return cart


@router.post("/items", response_model=CartItemRead, status_code=status.HTTP_201_CREATED, summary="Добавить картину в корзину")
async def add_item_to_cart(
    cart_item_create: CartItemCreate,
    db: AsyncSession = Depends(get_db),
    jwt_payload: JWTPayload = Depends(require_role(UserRole.CLIENT))
) -> CartItemRead:
    try:
        cart = await cart_crud.get_by_user_id(db, jwt_payload.sub)
        cart_item = await cart_crud.add_item(db, cart.id, cart_item_create)
        return cart_item
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить позицию из корзины")
async def remove_item_from_cart(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    jwt_payload: JWTPayload = Depends(require_role(UserRole.CLIENT))
):
    cart = await cart_crud.get_by_user_id(db, jwt_payload.sub)
    cart_item = await cart_crud.get_item_by_id(db, item_id)
    if not cart_item in cart.items:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You have not access to this cart."
        )
    deleted = await cart_crud.remove_item(db, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Элемент корзины не найден")
    return None


@router.delete("/", response_model=CartClearResponse, summary="Очистить корзину")
async def clear_my_cart(
    db: AsyncSession = Depends(get_db),
    jwt_payload: JWTPayload = Depends(require_role(UserRole.CLIENT))
):
    cart = await cart_crud.get_by_user_id(db, jwt_payload.sub)
    if await cart_crud.clear_cart(db, cart.id):
        return CartClearResponse(message="Корзина успешно очищена")
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found."
        )