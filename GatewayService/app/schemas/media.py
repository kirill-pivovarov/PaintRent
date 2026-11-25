from pydantic import BaseModel, Field

class ImageUploadResponse(BaseModel):
    image_url: str = Field(..., description="Относительный URL для доступа к загруженному файлу")
    filename: str = Field(..., description="Уникальное имя файла на сервере")