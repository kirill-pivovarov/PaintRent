from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_role
from app.db.crud import PaintingCRUD
from app.db.crud.painting import painting_list_available, painting_list, painting_list_
from app.db.model import Painting, UserRole, User, Base
from app.schemas.painting import PaintingRead, PaintingCreate, PaintingUpdate

router = APIRouter(prefix="/paintings", tags=["Paintings"])

painting_crud = PaintingCRUD()


# ---------- зависимости ----------
async def get_painting_or_404(
    painting_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Painting:
    painting = await painting_crud.get_by_id(db, painting_id)
    if not painting:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Painting not found")
    return painting


def require_owner_or_admin(
    painting: Painting = Depends(get_painting_or_404),
    current_user: User = Depends(require_role(UserRole.PARTNER, UserRole.ADMIN)),
) -> Painting:
    if current_user.role != UserRole.ADMIN and painting.partner_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your painting")
    return painting


# Публичный каталог (не требует токена)
@router.get("/", response_model=List[PaintingRead])
async def get_all_paintings(only_available: bool = True, db: AsyncSession = Depends(get_db)):
    """Получить список картин.
    Если only_available=true, вернет только картины со статусом AVAILABLE."""
    return painting_list_(db, only_available=only_available)


# Получить одну картину
@router.get("/{painting_id}", response_model=PaintingRead)
async def get_painting(painting_id: UUID, db: AsyncSession = Depends(get_db)):
    """Получить одну картину."""
    crud = PaintingCRUD()
    painting = await crud.get_by_id(db, painting_id)

    if not painting:
        raise HTTPException(status_code=404, detail="Painting not found")
    return painting



# Создать картину
@router.post("/", response_model=PaintingRead, status_code=status.HTTP_201_CREATED)
async def create_painting(data: PaintingCreate,
                          db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(require_role(UserRole.PARTNER, UserRole.ADMIN))
                          ):
    """Создать картину (только PARTNER или ADMIN)."""
    crud = PaintingCRUD()
    painting = await crud.create(db,
                                 partner_id=current_user.id,
                                 **data.model_dump())
    return painting


# Обновить картину
@router.patch("/{painting_id}", response_model=PaintingRead)
async def update_painting(painting_id: UUID,
                          data: PaintingUpdate,
                          db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(require_role(UserRole.PARTNER, UserRole.ADMIN))):
    """Обновить картину (только владелец или ADMIN)."""
    crud = PaintingCRUD()
    painting = await crud.get_by_id(db, painting_id)
    if not painting:
        raise HTTPException(status_code=404, detail="Painting not found")

    if current_user.role != UserRole.ADMIN and painting.partner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your painting")

    updated = await crud.update_paintings(
        db, painting_id, **data.model_dump(exclude_unset=True)
    )
    return updated

# Удалить картину
@router.delete("/{painting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_painting(painting_id: UUID,
                          db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(require_role(UserRole.PARTNER, UserRole.ADMIN))
                          ):
    """Удалить картину (только владелец или ADMIN)."""
    crud = PaintingCRUD()
    painting = await crud.get_by_id(db, painting_id)
    if not painting:
        raise HTTPException(status_code=404, detail="Painting not found")

    if current_user.role != UserRole.ADMIN and painting.partner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your painting")

    await crud.delete(db, painting)
    return None