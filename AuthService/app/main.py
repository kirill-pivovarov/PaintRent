import sys
import asyncio

# ОБЯЗАТЕЛЬНО для Windows перед запуском asyncpg / uvicorn
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
from fastapi import FastAPI

from app.api.routers_v1.main import router as auth_router

app = FastAPI()
app.include_router(auth_router)

