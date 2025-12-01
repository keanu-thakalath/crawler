from typing import List
from domain.exceptions import InvalidUrlError
from domain.values import ExtractJobResult, ScrapeJobResult, ReviewStatus, SummarizeJobResult, CrawlJobResult, JobError
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
    page_url: str, 
    markdown_content: str, 
    uow: UnitOfWork, 
    custom_prompt: str | None = None,
    scraped_internal_links: List[NormalizedUrl] = None,
) -> ExtractJob:
    page = await uow.pages.get(page_url)
    if not page:
        raise PageNotFoundError(page_url)

    # For manual extraction, use scraped internal links as candidates (no crawl context)
    candidate_internal_links = scraped_internal_links or []

    async for job in page.extract_page(
        uow.page_summarizer, 
        markdown_content, 
        candidate_internal_links,
        custom_prompt
    ):
        await uow.commit()

    return job


async def list_sources(uow: UnitOfWork) -> list[Source]:
    return await uow.sources.list_all()


async def get_unreviewed_jobs(uow: UnitOfWork) -> List[Source]:
    """Get sources with pages containing only unreviewed extract/summarize jobs."""
    sources = await uow.sources.get_sources_with_unreviewed_jobs()
    
    # Filter jobs to only include unreviewed ones to match original behavior
    filtered_sources = []
    for source in sources:
        # Filter source-level jobs to only unreviewed ones
        source_jobs = []
        for job in source.jobs:
            if (hasattr(job.outcome, 'review_status') and 
                job.outcome.review_status == ReviewStatus.UNREVIEWED):
                source_jobs.append(job)
        
        # Filter pages to only include those with unreviewed jobs
        filtered_pages = []
        for page in source.pages:
            page_jobs = []
            for job in page.jobs:
                if (hasattr(job.outcome, 'review_status') and 
                    job.outcome.review_status == ReviewStatus.UNREVIEWED):
                    page_jobs.append(job)
            
            if page_jobs:  # Only include page if it has unreviewed jobs
                page.jobs = page_jobs
                filtered_pages.append(page)
        
        # Only include source if it has unreviewed source-jobs or pages with unreviewed jobs
        if source_jobs or filtered_pages:
            source.jobs = source_jobs
            source.pages = filtered_pages
            filtered_sources.append(source)
    
    return filtered_sources


async def get_failed_jobs(uow: UnitOfWork) -> List[Source]:
    """Get sources with pages containing only failed jobs."""
    sources = await uow.sources.get_sources_with_failed_jobs()
    
    # Filter jobs to only include failed ones to match original behavior
    filtered_sources = []
    for source in sources:
        # Filter source-level jobs to only failed ones
        source_jobs = []
        for job in source.jobs:
            if isinstance(job.outcome, JobError):
                source_jobs.append(job)
        
        # Filter pages to only include those with failed jobs
        filtered_pages = []
        for page in source.pages:
            page_jobs = []
            for job in page.jobs:
                if isinstance(job.outcome, JobError):
                    page_jobs.append(job)
            
            if page_jobs:  # Only include page if it has failed jobs
                page.jobs = page_jobs
                filtered_pages.append(page)
        
        # Only include source if it has failed source-jobs or pages with failed jobs
        if source_jobs or filtered_pages:
            source.jobs = source_jobs
            source.pages = filtered_pages
            filtered_sources.append(source)
    
    return filtered_sources


async def get_crawled_sources(uow: UnitOfWork) -> List[Source]:
    """Get sources with completed crawl jobs. No pages included."""
    return await uow.sources.get_crawled_sources()


async def get_discovered_sources(uow: UnitOfWork) -> List[Source]:
    """Get sources with no crawl job (discovered via external links). No pages included."""
    return await uow.sources.get_discovered_sources()


async def get_in_progress_sources(uow: UnitOfWork) -> List[Source]:
    """Get sources with jobs but no CrawlJobResult (crawl in progress). No pages included."""
    return await uow.sources.get_in_progress_sources()


async def get_source_only(source_url: str, uow: UnitOfWork) -> Source:
    """Get source data without page jobs."""
    source = await uow.sources.get(source_url)
    if not source:
        raise SourceNotFoundError(source_url)
    
    # Create new source without pages but with source-level jobs
    return Source(url=source.url, jobs=source.jobs, pages=[Page(page.url) for page in source.pages])


async def crawl_url_with_source_check(url: str, max_pages: int, uow: UnitOfWork, extract_prompt: str | None = None) -> str:
    """Add source if it doesn't exist, then start crawl. Returns source URL."""
    from tasks.crawl import crawl_url
    
    normalized_url = NormalizedUrl(url)
    
    # Check if source exists, if not create it
    try:
        await add_source(normalized_url, uow)
    except SourceAlreadyExistsError:
        pass  # Source already exists, continue with crawl
    
    # Start crawl job
    crawl_url.delay(normalized_url, max_pages, extract_prompt)
    return str(normalized_url)


def filter_markdown_from_scrape_results(sources: List[Source]) -> List[Source]:
    """Remove markdown field from ScrapeJobResult in all sources except for specific endpoints."""
    
    filtered_sources = []
    for source in sources:
        # Filter source jobs
        filtered_source_jobs = []
        for job in source.jobs:
            if isinstance(job.outcome, ScrapeJobResult):
                # Create new ScrapeJobResult without markdown
                new_outcome = ScrapeJobResult(
                    created_at=job.outcome.created_at,
                    markdown="",  # Remove markdown
                    internal_links=job.outcome.internal_links,
                    external_links=job.outcome.external_links,
                    file_links=job.outcome.file_links
                )
                job.outcome = new_outcome
            filtered_source_jobs.append(job)
        
        # Filter page jobs
        filtered_pages = []
        for page in source.pages:
            filtered_page_jobs = []
            for job in page.jobs:
                if isinstance(job.outcome, ScrapeJobResult):
                    # Create new ScrapeJobResult without markdown
                    new_outcome = ScrapeJobResult(
                        created_at=job.outcome.created_at,
                        markdown="",  # Remove markdown
                        internal_links=job.outcome.internal_links,
                        external_links=job.outcome.external_links,
                        file_links=job.outcome.file_links
                    )
                    job.outcome = new_outcome
                filtered_page_jobs.append(job)
            
            page.jobs = filtered_page_jobs
            filtered_pages.append(page)
        
        source.jobs = filtered_source_jobs
        source.pages = filtered_pages
        filtered_sources.append(source)
    
    return filtered_sources


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


async def crawl_source(source_url: str, max_pages: int, uow: UnitOfWork, extract_prompt: str | None = None, summarize_prompt: str | None = None) -> CrawlJob:
    source = await uow.sources.get(source_url)
    if not source:
        raise SourceNotFoundError(source_url)

    async for job in source.crawl_source(
        max_pages,
        uow.content_scraper,
        uow.manual_link_extractor,
        uow.page_summarizer,
        uow.source_analyzer,
        extract_prompt,
        summarize_prompt,
    ):
        await uow.commit()
        # Process external links from completed summarize job
        if isinstance(job.outcome, SummarizeJobResult):
            for external_link in job.outcome.relevant_external_links:
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
