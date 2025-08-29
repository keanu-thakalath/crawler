from domain.exceptions import InvalidUrlError
from domain.values import ExtractJobResult
from domain.entities import CrawlJob, ExtractJob, Page, ScrapeJob, Source, SummarizeJob
from domain.types import NormalizedUrl

from .exceptions import (
    PageAlreadyExistsError,
    PageNotFoundError,
    SourceAlreadyExistsError,
    SourceNotFoundError,
)
from .unit_of_work import UnitOfWork


async def add_source(url: str, uow: UnitOfWork) -> Source:
    normalized_url = NormalizedUrl(url)

    existing_source = await uow.sources.get(normalized_url)
    if existing_source:
        raise SourceAlreadyExistsError(normalized_url)

    source = Source(url=normalized_url)

    await uow.sources.add(source)
    await uow.commit()
    return source


async def scrape_page(page_url: str, uow: UnitOfWork) -> ScrapeJob:
    page = await uow.pages.get(page_url)
    if not page:
        raise PageNotFoundError(page_url)

    async for job in page.scrape_page(uow.html_scraper, uow.html_converter):
        await uow.commit()

    return job


async def extract_page(
    page_url: str, markdown_content: str, uow: UnitOfWork
) -> ExtractJob:
    page = await uow.pages.get(page_url)
    if not page:
        raise PageNotFoundError(page_url)

    async for job in page.extract_page(uow.page_link_extractor, markdown_content):
        await uow.commit()

    return job


async def list_sources(uow: UnitOfWork) -> list[Source]:
    return await uow.sources.list_all()


async def get_source(source_url: str, uow: UnitOfWork) -> Source:
    source = await uow.sources.get(source_url)
    if not source:
        raise SourceNotFoundError(source_url)
    return source


async def get_page(page_url: str, uow: UnitOfWork) -> Page:
    page = await uow.pages.get(page_url)
    if not page:
        raise PageNotFoundError(page_url)
    return page


async def add_page_to_source(source_url: str, page_url: str, uow: UnitOfWork) -> Page:
    source = await uow.sources.get(source_url)
    if not source:
        raise SourceNotFoundError(source_url)

    normalized_page_url = NormalizedUrl(page_url)

    existing_page = await uow.pages.get(normalized_page_url)
    if existing_page:
        raise PageAlreadyExistsError(normalized_page_url)

    page = Page(url=normalized_page_url)
    source.pages.append(page)

    await uow.pages.add(page)
    await uow.commit()
    return page


async def summarize_source(
    source_url: str, all_page_summaries: str, uow: UnitOfWork
) -> SummarizeJob:
    source = await uow.sources.get(source_url)
    if not source:
        raise SourceNotFoundError(source_url)

    async for job in source.summarize_source(uow.source_analyzer, all_page_summaries):
        await uow.commit()

    return job


async def crawl_source(source_url: str, max_pages: int, uow: UnitOfWork) -> CrawlJob:
    source = await uow.sources.get(source_url)
    if not source:
        raise SourceNotFoundError(source_url)

    async for job in source.crawl_source(
        max_pages,
        uow.html_scraper,
        uow.html_converter,
        uow.page_link_extractor,
        uow.source_analyzer,
    ):
        await uow.commit()

        if isinstance(job.outcome, ExtractJobResult):
            for external_link in job.outcome.external_links:
                try:
                    await add_source(external_link, uow)
                except SourceAlreadyExistsError:
                    pass
                except InvalidUrlError:
                    pass

    return job


async def delete_source(source_url: str, uow: UnitOfWork) -> None:
    source = await uow.sources.get(source_url)
    if not source:
        raise SourceNotFoundError(source_url)

    await uow.sources.delete(source)
    await uow.commit()
