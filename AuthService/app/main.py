from fastapi import FastAPI

from app.api.routers_v1.access_control import router as auth_router
from app.redis import lifespan

app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)

