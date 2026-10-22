from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.painting import PaintingRead

router = APIRouter(prefix="/paintings", tags=["Paintings"])

# Публичный каталог (не требует токена)
@router.get("/", response_model=List[PaintingRead])
async def get_all_paintings():
    """Получить список картин.
    Если only_available=true, вернет только картины со статусом AVAILABLE."""
    pass


# Получить одну картину
@router.get("/{painting_id}", response_model=PaintingRead)
async def get_painting(painting_id: UUID):
    """Получить одну картину."""
    pass


# Создать картину
@router.post("/", response_model=PaintingRead, status_code=status.HTTP_201_CREATED)
async def create_painting():
    """Создать картину (только PARTNER или ADMIN)."""
    pass


# Обновить картину
@router.patch("/{painting_id}", response_model=PaintingRead)
async def update_painting(painting_id: UUID):
    """Обновить картину (только владелец или ADMIN)."""
    pass

# Удалить картину
@router.delete("/{painting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_painting(painting_id: UUID):
    """Удалить картину (только владелец или ADMIN)."""
    pass