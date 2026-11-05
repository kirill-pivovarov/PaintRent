from fastapi import FastAPI, Depends

from app.api.routers_v1.auth import router as auth_router
from app.api.routers_v1.paintings import router as paintings_router
from app.api.routers_v1.admin import router as admin_router
from app.api.routers_v1.orders import router as orders_router
from app.api.routers_v1.cart import router as cart_router

# Создаем приложение FastAPI
app = FastAPI(
    title="PaintRent API",
    version="1.0.0",
    docs_url="/gateway/docs",       # Где будет доступен Swagger UI
    openapi_url="/gateway/openapi.json" # Где лежит JSON-схема API
)

app.include_router(auth_router, prefix="/gateway")
app.include_router(paintings_router, prefix="/gateway")
app.include_router(admin_router, prefix="/gateway")
app.include_router(orders_router, prefix="/gateway")
app.include_router(cart_router, prefix="/gateway")