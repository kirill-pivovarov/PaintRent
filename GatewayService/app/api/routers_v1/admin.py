from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from GatewayService.app.api.deps import get_db, require_role
from GatewayService.app.db.crud.painting import PaintingCRUD, painting_list
from GatewayService.app.db.model import User, UserRole
from GatewayService.app.schemas.painting import PaintingRead

router = APIRouter(prefix="/admin/paintings", tags=["Admin: Paintings"])


@router.get("/", response_model=list[PaintingRead])
async def get_all_paintings_admin(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
):
    """
    Полный список картин (все статусы, все партнёры). Только ADMIN.
    Отдельный префикс /admin/paintings — не конфликтует с /paintings/{id},
    не требует опционального токена и условной логики.
    """
    return await painting_list(db, only_available=False)