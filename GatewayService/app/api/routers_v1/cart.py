from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.deps import get_db, require_role, CurrentUser
from app.db.crud.cart import CartCRUD
from app.db.model import UserRole, Painting, PaintingStatus
from app.schemas.cart import CartRead

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("/", response_model=CartRead)
async def get_my_cart(
        db: AsyncSession = Depends(get_db),
        current_user: CurrentUser = Depends(require_role(UserRole.CLIENT))
):
    """Посмотреть свою корзину."""
    crud = CartCRUD()
    cart = await crud.get_or_create_by_user(db, current_user.id)
    return cart


@router.post("/items/{painting_id}", status_code=status.HTTP_201_CREATED)
async def add_to_cart(
        painting_id: UUID,
        db: AsyncSession = Depends(get_db),
        current_user: CurrentUser = Depends(require_role(UserRole.CLIENT))
):
    """Добавить картину в корзину (только если она доступна)."""
    # 1. Проверяем картину
    painting = await db.get(Painting, painting_id)
    if not painting:
        raise HTTPException(404, "Painting not found")
    if painting.status != PaintingStatus.AVAILABLE:
        raise HTTPException(400, "Painting is not available")

    # 2. Получаем корзину
    crud = CartCRUD()
    cart = await crud.get_or_create_by_user(db, current_user.id)

    # 3. Проверяем, нет ли уже этой картины в корзине
    for item in cart.items:
        if item.painting_id == painting_id:
            raise HTTPException(400, "Painting already in cart")

    # 4. Добавляем
    await crud.add_item(db, cart.id, painting_id)

    # Возвращаем обновленную корзину
    updated_cart = await crud.get_or_create_by_user(db, current_user.id)
    return {"message": "Added", "cart": updated_cart}


@router.delete("/items/{painting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_cart(
        painting_id: UUID,
        db: AsyncSession = Depends(get_db),
        current_user: CurrentUser = Depends(require_role(UserRole.CLIENT))
):
    """Убрать картину из корзины."""
    crud = CartCRUD()
    cart = await crud.get_or_create_by_user(db, current_user.id)

    ok = await crud.remove_item(db, cart.id, painting_id)
    if not ok:
        raise HTTPException(404, "Item not in cart")
    return None


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
        db: AsyncSession = Depends(get_db),
        current_user: CurrentUser = Depends(require_role(UserRole.CLIENT))
):
    """Очистить корзину."""
    crud = CartCRUD()
    cart = await crud.get_or_create_by_user(db, current_user.id)
    await crud.clear_cart(db, cart.id)
    return None