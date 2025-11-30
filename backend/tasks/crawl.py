from service import services
from service.unit_of_work import UnitOfWork

from .config import async_task


@async_task()
async def crawl_url(uow: UnitOfWork, source_url: str, max_pages: int, extract_prompt: str | None = None):
    await services.crawl_source(source_url, max_pages, uow, extract_prompt)


@async_task()
async def auto_summarize_source(uow: UnitOfWork, source_url: str):
    """Auto-trigger source summarization when all extract jobs are approved."""
    await services.auto_summarize_approved_source(source_url, uow)
