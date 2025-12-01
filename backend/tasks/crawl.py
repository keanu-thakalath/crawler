from service import services
from service.unit_of_work import UnitOfWork

from .config import async_task


@async_task(acks_late=True)
async def crawl_url(uow: UnitOfWork, source_url: str, max_pages: int, extract_prompt: str | None = None, summarize_prompt: str | None = None):
    await services.crawl_source(source_url, max_pages, uow, extract_prompt, summarize_prompt)
