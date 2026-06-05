import asyncio
from api.db import engine
from api.models import Base

async def create():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Done")

asyncio.run(create())
