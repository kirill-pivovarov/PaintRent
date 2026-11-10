import asyncio
from decimal import Decimal
from uuid import UUID
import uvicorn

from sqlalchemy.ext.asyncio import AsyncSession






if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)

