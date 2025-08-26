import asyncio
from functools import wraps
import os

from celery import Celery

from database.session import create_async_session_factory
from service.unit_of_work import SqlAlchemyUnitOfWork

from dotenv import load_dotenv

load_dotenv()


def create_celery_app() -> Celery:
    celery_app = Celery(
        "crawler_demo",
        broker=os.getenv("CELERY_BROKER"),
        backend=os.getenv("CELERY_BACKEND"),
        include=["tasks.crawl"],
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
    )

    return celery_app


celery_app = create_celery_app()


def async_task(**celery_kwargs):
    def decorator(async_func):
        @wraps(async_func)
        def sync_wrapper(*args, **kwargs):
            return asyncio.run(_run_with_uow(async_func, *args, **kwargs))

        # Create the Celery task
        task = celery_app.task(**celery_kwargs)(sync_wrapper)
        return task

    return decorator


async def _run_with_uow(async_func, *args, **kwargs):
    session_factory, engine = await create_async_session_factory()

    try:
        async with SqlAlchemyUnitOfWork(session_factory=session_factory) as uow:
            return await async_func(uow, *args, **kwargs)
    finally:
        await engine.dispose()
