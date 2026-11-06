from contextlib import asynccontextmanager
from fastapi import FastAPI
import redis.asyncio as aioredis

from app.settings import get_settings

@asynccontextmanager
async def lifespan(app: FastAPI):

    app.state.redis = aioredis.from_url(
        get_settings().redis_url, 
        encoding="utf-8", 
        decode_responses=True  # Автоматически переводит bytes в строки str
    )
    yield  
    await app.state.redis.close()
