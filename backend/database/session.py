import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .models import Models, metadata

load_dotenv()


async def create_async_session_factory():
    engine = create_async_engine(os.getenv("DATABASE_URL"))

    Models.start_mappers()

    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

    return async_session_factory, engine
