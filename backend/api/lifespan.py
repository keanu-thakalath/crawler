from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from litestar import Litestar

from database.session import create_async_session_factory


@asynccontextmanager
async def db_connection(app: Litestar) -> AsyncGenerator[None, None]:
    session_factory, engine = await create_async_session_factory(
        "sqlite+aiosqlite:///crawler.sqlite"
    )
    app.state.session_factory = session_factory
    app.state.engine = engine

    try:
        yield
    finally:
        await engine.dispose()
