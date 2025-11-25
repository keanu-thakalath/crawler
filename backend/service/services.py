from domain.exceptions import InvalidUrlError
from domain.values import ExtractJobResult, ReviewStatus, ScrapeJobResult, SummarizeJobResult
from domain.entities import (
    CrawlJob,
    ExtractJob,
    Job,
    Page,
    ScrapeJob,
    Source,
    SummarizeJob,
)
from domain.types import NormalizedUrl

from .exceptions import (
    InvalidJobTypeError,
    InvalidSummaryValueError,
    JobNotFoundError,
    PageAlreadyExistsError,
    PageNotFoundError,
    SourceAlreadyExistsError,
    SourceNotFoundError,
)
from .unit_of_work import UnitOfWork


async def auto_summarize_approved_source(source_url: str, uow: UnitOfWork) -> SummarizeJob:
    """Auto-trigger source summarization when all extract jobs are approved."""
    source = await uow.sources.get(source_url)
    if not source:
        raise SourceNotFoundError(source_url)
    
    # Build page summaries from approved extract jobs
    page_summaries = []
    
    for page in source.pages:
        for job in page.jobs:
            if (isinstance(job, ExtractJob) and 
                job.outcome and 
                isinstance(job.outcome, ExtractJobResult) and 
                job.outcome.review_status == ReviewStatus.APPROVED):
                page_summaries.append(
                    f"Markdown for {page.url}:\n\n{job.outcome.summary}"
                )
                break  # Only take the first approved extract job per page
    
    if page_summaries:
        all_page_summaries = "\n\n".join(page_summaries)
        # Trigger source summarization without custom prompt
        async for summary_job in source.summarize_source(uow.source_analyzer, all_page_summaries, None):
            await uow.commit()
        return summary_job
    else:
        raise ValueError(f"No approved extract jobs found for source {source_url}")


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

    async for job in page.scrape_page(uow.content_scraper, uow.manual_link_extractor):
        await uow.commit()

    return job


async def extract_page(
    page_url: str, markdown_content: str, uow: UnitOfWork, custom_prompt: str | None = None
) -> ExtractJob:
    page = await uow.pages.get(page_url)
    if not page:
        raise PageNotFoundError(page_url)

    async for job in page.extract_page(
        uow.page_summarizer, markdown_content, custom_prompt
    ):
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
    source_url: str, all_page_summaries: str, uow: UnitOfWork, custom_prompt: str | None = None
) -> SummarizeJob:
    source = await uow.sources.get(source_url)
    if not source:
        raise SourceNotFoundError(source_url)

    async for job in source.summarize_source(uow.source_analyzer, all_page_summaries, custom_prompt):
        await uow.commit()

    return job


async def crawl_source(source_url: str, max_pages: int, uow: UnitOfWork, extract_prompt: str | None = None) -> CrawlJob:
    source = await uow.sources.get(source_url)
    if not source:
        raise SourceNotFoundError(source_url)

    async for job in source.crawl_source(
        max_pages,
        uow.content_scraper,
        uow.manual_link_extractor,
        uow.page_summarizer,
        extract_prompt,
    ):
        await uow.commit()

        # External links are now extracted during scraping, so we check ScrapeJobResult
        if isinstance(job.outcome, ScrapeJobResult):
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


async def approve_job_review_status(job_id: str, uow: UnitOfWork) -> Job:
    job = await uow.jobs.get_by_id(job_id)
    if not job:
        raise JobNotFoundError(job_id)

    # Check if job outcome supports review status updates
    if not isinstance(job.outcome, (ExtractJobResult, SummarizeJobResult)):
        outcome_type = type(job.outcome).__name__ if job.outcome else "None"
        raise InvalidJobTypeError(job_id, outcome_type)

    # Update review status to approved
    job.outcome.review_status = ReviewStatus.APPROVED
    await uow.commit()
    
    # If this is an extract job, check if all extract jobs for the source are now approved
    if isinstance(job, ExtractJob):
        # Get the source URL from the page URL
        page = await uow.pages.get(job.page_url)
        if page:
            source = await uow.sources.get(page.source_url)
            if source and source.all_extract_jobs_approved():
                # Auto-trigger source summarization as async task
                from tasks.crawl import auto_summarize_source
                auto_summarize_source.delay(str(source.url))
    
    return job


async def edit_job_outcome_summary(job_id: str, summary: str, uow: UnitOfWork) -> Job:
    # Validate summary is not empty or whitespace-only
    if not summary or not summary.strip():
        raise InvalidSummaryValueError(summary)

    job = await uow.jobs.get_by_id(job_id)
    if not job:
        raise JobNotFoundError(job_id)

    # Check if job outcome supports summary updates
    if not isinstance(job.outcome, (ExtractJobResult, SummarizeJobResult)):
        outcome_type = type(job.outcome).__name__ if job.outcome else "None"
        raise InvalidJobTypeError(job_id, outcome_type)

    # Update the summary
    job.outcome.summary = summary.strip()
    await uow.commit()
    return job
