import uuid
from pathlib import Path
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status

from app.api.deps import require_role
from app.schemas.jwt_payload import JWTPayload
from app.schemas.media import ImageUploadResponse
from app.db.model import UserRole

router = APIRouter(prefix="/media", tags=["Media"])

# Базовая папка на сервере для хранения изображений
UPLOAD_DIR = Path("../static/paintings")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Ограничения безопасности
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 Мегабайт
CHUNK_SIZE = 1024 * 1024  # Чтение чанками по 1 МБ


@router.post(
    "/upload",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Загрузка изображения картины",
    description="""
    Загружает файл изображения на сервер и возвращает относительный `image_url`.
    
    * **Доступно ролям:** `PARTNER`, `ADMIN`.
    * **Поддерживаемые форматы:** JPEG, PNG, WebP.
    * **Максимальный размер:** 10 МБ.
    """,
    responses={
        400: {"description": "Недопустимый формат или превышен размер файла"},
        401: {"description": "Пользователь не авторизован"},
        403: {"description": "Недостаточно прав (доступно только PARTNER/ADMIN)"},
    }
)
async def upload_painting_image(
    file: UploadFile = File(..., description="Файл изображения картины"),
    # Только партнеры и админы могут загружать картины
    jwt_payload: JWTPayload = Depends(require_role(UserRole.PARTNER, UserRole.ADMIN))
) -> ImageUploadResponse:
    # 1. Валидация расширения файла
    file_extension = Path(file.filename or "").suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимое расширение файла. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 2. Валидация MIME-типа (Content-Type)
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый тип контента: '{file.content_type}'. Ожидается изображение."
        )

    # 3. Генерация безопасного уникального имени
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    target_file_path = UPLOAD_DIR / unique_filename

    # 4. Потоковое асинхронное сохранение с контролем размера
    bytes_written = 0
    try:
        async with aiofiles.open(target_file_path, "wb") as out_file:
            while chunk := await file.read(CHUNK_SIZE):
                bytes_written += len(chunk)
                if bytes_written > MAX_FILE_SIZE_BYTES:
                    # Если размер превышен, удаляем недописанный файл
                    await out_file.close()
                    if target_file_path.exists():
                        target_file_path.unlink()
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Размер файла превышает лимит в 10 МБ."
                    )
                await out_file.write(chunk)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        # Если произошел сбой ввода-вывода, чистим временный файл
        if target_file_path.exists():
            target_file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось сохранить файл на сервере."
        )
    finally:
        await file.close()

    # 5. Формируем URL для базы данных
    image_url = f"/static/paintings/{unique_filename}"

    return ImageUploadResponse(
        image_url=image_url,
        filename=unique_filename
    )