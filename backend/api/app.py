from typing import List
from litestar import Litestar, get, post, delete
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import SwaggerRenderPlugin
from litestar.plugins.sqlalchemy import SQLAlchemyAsyncConfig, SQLAlchemyPlugin
from litestar.config.cors import CORSConfig
from database.models import (
    Base,
    Source,
    Page,
    File,
    PageJob,
    SourceJob,
    ScrapeJob,
    ExtractJob,
    SummarizeJob,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tasks.crawl_tasks import crawl_url
from api.models import (
    CrawlRequest,
    FileWithoutPage,
    PageWithoutSource,
    SourceWithoutContent,
    JobResponse,
    ScrapeJobResponse,
    ExtractJobResponse,
    SummarizeJobResponse,
)
from collections.abc import AsyncGenerator

from sqlalchemy.exc import IntegrityError
from litestar.exceptions import ClientException
from litestar.status_codes import (
    HTTP_409_CONFLICT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)


async def provide_session(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncSession, None]:
    try:
        async with db_session.begin():
            yield db_session
    except IntegrityError as exc:
        raise ClientException(
            status_code=HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@post("/crawl")
async def queue_crawl(data: CrawlRequest, session: AsyncSession) -> None:
    # Validate HTTPS only
    if not data.url.startswith("https://"):
        raise ClientException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Only HTTPS URLs are allowed",
        )

    # Normalize URL by removing trailing slash
    normalized_url = data.url.rstrip("/")

    existing_source = await session.execute(
        select(Source).where(Source.url == normalized_url)
    )
    if existing_source.unique().scalar_one_or_none():
        raise ClientException(
            status_code=HTTP_409_CONFLICT,
            detail="URL already exists in database",
        )

    crawl_url.delay(normalized_url)


@get("/sources")
async def sources(session: AsyncSession) -> List[SourceWithoutContent]:
    sources = (await session.execute(select(Source))).unique().scalars().all()
    sources = [SourceWithoutContent(url=source.url, pages=[PageWithoutSource(url=page.url) for page in source.pages]) for source in sources]
    return sources


@get("/sources/jobs")
async def get_source_jobs(source_url: str, session: AsyncSession) -> List[JobResponse]:
    """Get all jobs for a source"""
    jobs_result = await session.execute(
        select(SourceJob).where(SourceJob.source_url == source_url)
    )
    jobs = jobs_result.scalars().all()
    return [
        JobResponse(id=job.id, job_type=job.job_type.value, status=job.status.value)
        for job in jobs
    ]


@get("/pages/jobs")
async def get_page_jobs(page_url: str, session: AsyncSession) -> List[JobResponse]:
    """Get all jobs for a page"""
    jobs_result = await session.execute(
        select(PageJob).where(PageJob.page_url == page_url)
    )
    jobs = jobs_result.scalars().all()
    return [
        JobResponse(id=job.id, job_type=job.job_type.value, status=job.status.value)
        for job in jobs
    ]


@get("/jobs/scrape/{job_id:int}")
async def get_scrape_result(job_id: int, session: AsyncSession) -> ScrapeJobResponse:
    """Get scrape job result"""
    result = await session.execute(
        select(ScrapeJob).where(ScrapeJob.page_job_id == job_id)
    )
    scrape_job = result.scalar_one_or_none()
    if not scrape_job:
        raise ClientException(status_code=HTTP_404_NOT_FOUND)

    return ScrapeJobResponse(
        id=scrape_job.id,
        page_job_id=scrape_job.page_job_id,
        markdown=scrape_job.markdown,
        html=scrape_job.html,
    )


@get("/jobs/extract/{job_id:int}")
async def get_extract_result(job_id: int, session: AsyncSession) -> ExtractJobResponse:
    """Get extract job result with files"""
    result = await session.execute(
        select(ExtractJob).where(ExtractJob.page_job_id == job_id)
    )
    extract_job = result.scalar_one_or_none()
    if not extract_job:
        raise ClientException(status_code=HTTP_404_NOT_FOUND)

    files_result = await session.execute(
        select(File).where(File.extract_job_id == extract_job.id)
    )
    files = files_result.scalars().all()

    return ExtractJobResponse(
        id=extract_job.id,
        page_job_id=extract_job.page_job_id,
        summary=extract_job.summary,
        input_tokens=extract_job.input_tokens,
        output_tokens=extract_job.output_tokens,
        files=[FileWithoutPage(id=file.id, url=file.url) for file in files],
    )


@get("/jobs/summarize/{job_id:int}")
async def get_summarize_result(
    job_id: int, session: AsyncSession
) -> SummarizeJobResponse:
    """Get summarize job result"""
    result = await session.execute(
        select(SummarizeJob).where(SummarizeJob.source_job_id == job_id)
    )
    summarize_job = result.scalar_one_or_none()
    if not summarize_job:
        raise ClientException(status_code=HTTP_404_NOT_FOUND)

    return SummarizeJobResponse(
        id=summarize_job.id,
        source_job_id=summarize_job.source_job_id,
        summary=summarize_job.summary,
        data_origin=summarize_job.data_origin,
        source_format=summarize_job.source_format,
        focus_area=summarize_job.focus_area,
        input_tokens=summarize_job.input_tokens,
        output_tokens=summarize_job.output_tokens,
    )


@delete("/reset")
async def reset_tables() -> None:
    async with db_config.get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


db_config = SQLAlchemyAsyncConfig(
    connection_string="sqlite+aiosqlite:///crawler.sqlite",
    metadata=Base.metadata,
    create_all=True,
    before_send_handler="autocommit",
)

cors_config = CORSConfig(allow_origins=["http://localhost:3000"])

app = Litestar(
    route_handlers=[
        queue_crawl,
        sources,
        reset_tables,
        get_source_jobs,
        get_page_jobs,
        get_scrape_result,
        get_extract_result,
        get_summarize_result,
    ],
    openapi_config=OpenAPIConfig(
        title="Crawler Demo",
        description="A web crawler, scraper, and archiving service",
        version="0.0.1",
        render_plugins=[SwaggerRenderPlugin()],
    ),
    dependencies={"session": provide_session},
    plugins=[SQLAlchemyPlugin(db_config)],
    cors_config=cors_config,
)
