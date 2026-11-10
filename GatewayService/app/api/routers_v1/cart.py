from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_role
from app.db.model import User, UserRole
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


@router.get("/", response_model=CartRead, summary="Получить корзину текущего клиента")
async def get_my_cart(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CLIENT))
):
    cart = await cart_crud.get_or_create_cart(db, user_id=current_user.id)
    return cart


@router.post("/items", response_model=CartItemRead, status_code=status.HTTP_201_CREATED, summary="Добавить картину в корзину")
async def add_item_to_cart(
    item_in: CartItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CLIENT))
):
    try:
        cart_item = await cart_crud.add_item_to_cart(db, user_id=current_user.id, item_in=item_in)
        return cart_item
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить позицию из корзины")
async def remove_item_from_cart(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CLIENT))
):
    deleted = await cart_crud.remove_item(db, user_id=current_user.id, item_id=item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Элемент корзины не найден")
    return None


@router.delete("/", response_model=CartClearResponse, summary="Очистить корзину")
async def clear_my_cart(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CLIENT))
):
    await cart_crud.clear_cart(db, user_id=current_user.id)
    return CartClearResponse(message="Корзина успешно очищена")