from fastapi import FastAPI

from app.api.routers_v1.access_control import router as auth_router

app = FastAPI()
app.include_router(auth_router)

