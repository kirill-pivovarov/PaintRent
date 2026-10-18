from fastapi import FastAPI, Depends
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api.deps import get_db
from app.api.v1.auth import router as auth_router

# Создаем приложение FastAPI
app = FastAPI(
    title="PaintRent API",
    version="1.0.0",
    docs_url="/api/v1/docs",       # Где будет доступен Swagger UI
    openapi_url="/api/v1/openapi.json" # Где лежит JSON-схема API
)

# Простейший эндпоинт для проверки, что сервер жив
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Эндпоинт, который проверит, что настройки считались
@app.get("/config-check")
async def config_check():
    # Внимание: НИКОГДА не отдавайте SECRET_KEY или DATABASE_URL в реальном API!
    # Мы делаем это только для теста, чтобы убедиться, что .env прочитался.
    return {
        "db_url_starts_with": settings.DATABASE_URL[:10] + "...",
        "has_secret": len(settings.SECRET_KEY) > 0
    }


@app.get("/db-check")
async def db_check(db: AsyncSession = Depends(get_db)):
    """
    Проверяем, что подключение к базе данных работает.
    """
    # Выполняем самый простой SQL-запрос: "выбери 1"
    result = await db.execute(text("SELECT 1"))
    value = result.scalar()  # Достаем результат

    return {
        "db_status": "connected" if value == 1 else "error",
        "result": value
    }

app.include_router(auth_router, prefix="/api/v1")
