from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .models import Models, metadata


async def create_async_session_factory(database_url):
    engine = create_async_engine(database_url)

    Models.start_mappers()

    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

    return async_session_factory, engine
