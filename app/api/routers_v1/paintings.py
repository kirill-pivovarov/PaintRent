from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_role
from app.db.crud import PaintingCRUD
from app.db.crud.painting import painting_list_available, painting_list, painting_list
from app.db.model import Painting, UserRole, User
from app.schemas.painting import PaintingRead, PaintingCreate, PaintingUpdate

router = APIRouter(prefix="/paintings", tags=["Paintings"])

painting_crud = PaintingCRUD()


# ---------- зависимости ----------
async def get_painting_or_404(
    painting_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Painting:
    """Достает картину по id из path или бросает 404."""
    painting = await painting_crud.get_by_id(db, painting_id)
    if not painting:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Painting not found")
    return painting


def require_owner_or_admin(
    painting: Painting = Depends(get_painting_or_404),
    current_user: User = Depends(require_role(UserRole.PARTNER, UserRole.ADMIN)),
) -> Painting:
    """Проверяет, что текущий пользователь — владелец картины или ADMIN.
    Возвращает уже загруженную картину."""
    if current_user.role != UserRole.ADMIN and painting.partner_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your painting")
    return painting


# ---------- Публичные запросы ------------
# Публичный каталог (не требует токена)
@router.get("/", response_model=List[PaintingRead])
async def get_all_paintings(db: AsyncSession = Depends(get_db)):
    """Получить список картин.
    Если only_available=true, вернет только картины со статусом AVAILABLE."""
    return await painting_list(db, only_available=True)


# Список своих картин
@router.get("/my", response_model=list[PaintingRead])
async def get_my_paintings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.PARTNER, UserRole.ADMIN)),
):
    return await painting_crud.get_by_partner(db, current_user.id)


# Получить одну картину
@router.get("/{painting_id}", response_model=PaintingRead)
async def get_painting(painting: Painting = Depends(get_painting_or_404)):
    """Получить одну картину."""
    return painting


# ----------- partner/admin -----------
# Создать картину
@router.post("/", response_model=PaintingRead, status_code=status.HTTP_201_CREATED)
async def create_painting(data: PaintingCreate,
                          db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(require_role(UserRole.PARTNER, UserRole.ADMIN))
                          ):
    """Создать картину (только PARTNER или ADMIN)."""

    painting = await painting_crud.create(db,
                                 partner_id=current_user.id,
                                 **data.model_dump())
    return painting


# Обновить картину
@router.patch("/{painting_id}", response_model=PaintingRead)
async def update_painting(
        data: PaintingUpdate,
        painting: Painting = Depends(require_owner_or_admin),
        db: AsyncSession = Depends(get_db)):

    """Обновить картину (только владелец или ADMIN)."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(painting, field, value)
    await db.flush()
    return painting

# Удалить картину
@router.delete("/{painting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_painting(painting: Painting = Depends(require_owner_or_admin),
                          db: AsyncSession = Depends(get_db)
                          ):
    """Удалить картину (только владелец или ADMIN)."""
    await painting_crud.delete(db, painting)
    return None