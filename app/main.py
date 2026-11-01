from fastapi import FastAPI, Depends
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api.deps import get_db
from app.api.routers_v1.auth import router as auth_router
from app.api.routers_v1.paintings import router as paintings_router

# Создаем приложение FastAPI
app = FastAPI(
    title="PaintRent API",
    version="1.0.0",
    docs_url="/api/v1/docs",       # Где будет доступен Swagger UI
    openapi_url="/api/v1/openapi.json" # Где лежит JSON-схема API
)

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
app.include_router(paintings_router, prefix="/api/v1")
