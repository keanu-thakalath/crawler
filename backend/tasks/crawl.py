from service import services
from service.unit_of_work import UnitOfWork

from .config import async_task


@async_task()
async def crawl_url(uow: UnitOfWork, source_url: str, max_pages: int):
    await services.crawl_source(source_url, max_pages, uow)
