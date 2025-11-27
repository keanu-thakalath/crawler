from typing import List

from litestar import Litestar, delete, get, patch, post
from litestar.config.cors import CORSConfig
from litestar.datastructures import State
from litestar.exceptions import ClientException
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import SwaggerRenderPlugin
from litestar.openapi.spec import Components, SecurityScheme
from litestar.middleware import DefineMiddleware
from litestar.status_codes import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
)

from .auth import AuthenticationMiddleware, Key, exchange_key, InvalidKeyError
from .dependencies import provide_uow
from .dto import (
    CrawlRequest,
    EditJobSummaryRequest,
    TokenResponse,
)
from .lifespan import db_connection
from database.models import metadata
from domain.entities import Job, Page, Source
from domain.exceptions import InvalidUrlError
from service import services
from service.exceptions import (
    InvalidJobTypeError,
    InvalidSummaryValueError,
    JobNotFoundError,
    PageNotFoundError,
    SourceNotFoundError,
)
from service.unit_of_work import UnitOfWork


@get("/sources/unreviewed-jobs")
async def get_unreviewed_jobs_endpoint(uow: UnitOfWork) -> List[Source]:
    """Get sources with only unreviewed jobs, filtering out pages/sources with no unreviewed jobs."""
    sources = await services.get_unreviewed_jobs(uow)
    return services.filter_markdown_from_scrape_results(sources)


@get("/sources/failed-jobs") 
async def get_failed_jobs_endpoint(uow: UnitOfWork) -> List[Source]:
    """Get sources with only failed jobs, filtering out pages/sources with no failed jobs."""
    sources = await services.get_failed_jobs(uow)
    return services.filter_markdown_from_scrape_results(sources)


@get("/sources/crawled")
async def get_crawled_sources_endpoint(uow: UnitOfWork) -> List[Source]:
    """Get sources with completed and reviewed summarize jobs. No pages included."""
    return await services.get_crawled_sources(uow)


@get("/sources/discovered") 
async def get_discovered_sources_endpoint(uow: UnitOfWork) -> List[Source]:
    """Get sources with no existing crawl job. No pages included."""
    return await services.get_discovered_sources(uow)


@get("/sources/in_progress")
async def get_in_progress_sources_endpoint(uow: UnitOfWork) -> List[Source]:
    """Get sources with jobs but no CrawlJobResult (crawl in progress). No pages included."""
    return await services.get_in_progress_sources(uow)


@get("/source")
async def get_source_endpoint(source_url: str, uow: UnitOfWork) -> Source:
    """Get source data without page jobs."""
    try:
        return await services.get_source_only(source_url, uow)
    except SourceNotFoundError as e:
        raise ClientException(status_code=HTTP_404_NOT_FOUND, detail=str(e)) from e


@get("/page")
async def get_page_endpoint(page_url: str, uow: UnitOfWork) -> Page:
    """Get complete page data with all jobs (includes markdown in ScrapeJobResult)."""
    try:
        return await services.get_page(page_url, uow)
    except PageNotFoundError as e:
        raise ClientException(status_code=HTTP_404_NOT_FOUND, detail=str(e)) from e


@post("/crawl")
async def crawl_url_endpoint(data: CrawlRequest, uow: UnitOfWork) -> dict:
    """Add URL as source if it doesn't exist, then start crawl job."""
    try:
        source_url = await services.crawl_url_with_source_check(data.url, data.max_pages, uow, data.extract_prompt)
        return {"message": "Crawl job started", "source_url": source_url}
    except InvalidUrlError as e:
        raise ClientException(status_code=HTTP_400_BAD_REQUEST, detail=e.reason) from e


@post("/exchange_key")
async def exchange_key_endpoint(key: Key) -> TokenResponse:
    """Exchange API key for authentication token."""
    try:
        return TokenResponse(token=exchange_key(key))
    except InvalidKeyError:
        raise ClientException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid key")


@patch("/jobs/{job_id:str}/approve")
async def approve_job_endpoint(job_id: str, uow: UnitOfWork) -> Job:
    """Approve a job by setting its review status to APPROVED."""
    try:
        return await services.approve_job_review_status(job_id, uow)
    except JobNotFoundError as e:
        raise ClientException(status_code=HTTP_404_NOT_FOUND, detail=str(e)) from e
    except InvalidJobTypeError as e:
        raise ClientException(status_code=HTTP_400_BAD_REQUEST, detail=str(e)) from e


@patch("/jobs/{job_id:str}/summary")
async def edit_job_summary_endpoint(
    job_id: str, data: EditJobSummaryRequest, uow: UnitOfWork
) -> Job:
    """Edit the summary field of an extract or summarize job."""
    try:
        return await services.edit_job_outcome_summary(job_id, data.summary, uow)
    except JobNotFoundError as e:
        raise ClientException(status_code=HTTP_404_NOT_FOUND, detail=str(e)) from e
    except InvalidJobTypeError as e:
        raise ClientException(status_code=HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except InvalidSummaryValueError as e:
        raise ClientException(status_code=HTTP_400_BAD_REQUEST, detail=str(e)) from e


@delete("/reset")
async def reset_database_endpoint(state: State) -> None:
    """Reset the database by dropping and recreating all tables."""
    engine = state.engine
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)


cors_config = CORSConfig()

auth_mw = DefineMiddleware(AuthenticationMiddleware, exclude=["schema", "exchange_key"])

app = Litestar(
    route_handlers=[
        exchange_key_endpoint,
        crawl_url_endpoint,
        get_unreviewed_jobs_endpoint,
        get_failed_jobs_endpoint,
        get_crawled_sources_endpoint,
        get_discovered_sources_endpoint,
        get_in_progress_sources_endpoint,
        get_source_endpoint,
        get_page_endpoint,
        approve_job_endpoint,
        edit_job_summary_endpoint,
        reset_database_endpoint,
    ],
    openapi_config=OpenAPIConfig(
        title="Crawler Demo",
        description="A clean web crawler API using domain-driven design",
        version="1.0.0",
        render_plugins=[SwaggerRenderPlugin()],
        security=[{"BearerToken": []}],
        components=Components(
            security_schemes={
                "BearerToken": SecurityScheme(
                    type="http",
                    scheme="bearer",
                )
            },
        ),
    ),
    dependencies={"uow": provide_uow},
    cors_config=cors_config,
    lifespan=[db_connection],
    middleware=[auth_mw],
)
