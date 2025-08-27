from typing import List

from litestar import Litestar, delete, get, post
from litestar.config.cors import CORSConfig
from litestar.datastructures import State
from litestar.exceptions import ClientException
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import SwaggerRenderPlugin
from litestar.status_codes import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
)

from api.dependencies import provide_uow
from api.dto import (
    AddPageToSourceRequest,
    CrawlRequest,
    ExtractRequest,
    ScrapeRequest,
    SummarizeRequest,
)
from api.lifespan import db_connection
from database.models import metadata
from domain.entities import ExtractJob, Page, ScrapeJob, Source, SummarizeJob
from domain.exceptions import InvalidUrlError
from service import services
from service.exceptions import (
    PageAlreadyExistsError,
    PageNotFoundError,
    SourceAlreadyExistsError,
    SourceNotFoundError,
)
from service.unit_of_work import UnitOfWork
from tasks.crawl import crawl_url


@post("/sources")
async def add_source_endpoint(source_url: str, uow: UnitOfWork) -> Source:
    try:
        return await services.add_source(source_url, uow)
    except InvalidUrlError as e:
        raise ClientException(status_code=HTTP_400_BAD_REQUEST, detail=e.reason) from e
    except SourceAlreadyExistsError as e:
        raise ClientException(status_code=HTTP_409_CONFLICT, detail=str(e)) from e


@post("/scrape")
async def scrape_page_endpoint(data: ScrapeRequest, uow: UnitOfWork) -> ScrapeJob:
    try:
        return await services.scrape_page(data.page_url, uow)
    except PageNotFoundError as e:
        raise ClientException(status_code=HTTP_404_NOT_FOUND, detail=str(e)) from e


@post("/extract")
async def extract_page_endpoint(data: ExtractRequest, uow: UnitOfWork) -> ExtractJob:
    try:
        return await services.extract_page(data.page_url, data.markdown_content, uow)
    except PageNotFoundError as e:
        raise ClientException(status_code=HTTP_404_NOT_FOUND, detail=str(e)) from e


@get("/sources")
async def list_sources_endpoint(uow: UnitOfWork) -> List[Source]:
    return await services.list_sources(uow)


@get("/source")
async def get_source_endpoint(source_url: str, uow: UnitOfWork) -> Source:
    try:
        return await services.get_source(source_url, uow)
    except SourceNotFoundError as e:
        raise ClientException(status_code=HTTP_404_NOT_FOUND, detail=str(e)) from e


@get("/page")
async def get_page_endpoint(page_url: str, uow: UnitOfWork) -> Page:
    try:
        return await services.get_page(page_url, uow)
    except PageNotFoundError as e:
        raise ClientException(status_code=HTTP_404_NOT_FOUND, detail=str(e)) from e


@post("/sources/pages")
async def add_page_to_source_endpoint(
    data: AddPageToSourceRequest, uow: UnitOfWork
) -> Page:
    try:
        return await services.add_page_to_source(data.source_url, data.page_url, uow)
    except SourceNotFoundError as e:
        raise ClientException(status_code=HTTP_404_NOT_FOUND, detail=str(e)) from e
    except PageAlreadyExistsError as e:
        raise ClientException(status_code=HTTP_409_CONFLICT, detail=str(e)) from e
    except InvalidUrlError as e:
        raise ClientException(status_code=HTTP_400_BAD_REQUEST, detail=e.reason) from e


@post("/summarize")
async def summarize_source_endpoint(
    data: SummarizeRequest, uow: UnitOfWork
) -> SummarizeJob:
    try:
        return await services.summarize_source(
            data.source_url, data.all_page_summaries, uow
        )
    except SourceNotFoundError as e:
        raise ClientException(status_code=HTTP_404_NOT_FOUND, detail=str(e)) from e


@post("/crawl")
async def crawl_url_endpoint(data: CrawlRequest) -> None:
    """Start a crawl task for the given URL"""
    crawl_url.delay(data.url, data.max_pages)


@delete("/sources")
async def delete_source_endpoint(source_url: str, uow: UnitOfWork) -> None:
    try:
        await services.delete_source(source_url, uow)
    except SourceNotFoundError as e:
        raise ClientException(status_code=HTTP_404_NOT_FOUND, detail=str(e)) from e


@delete("/reset")
async def reset_database_endpoint(state: State) -> None:
    """Reset the database by dropping all tables"""
    engine = state.engine
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)


cors_config = CORSConfig()

app = Litestar(
    route_handlers=[
        add_source_endpoint,
        list_sources_endpoint,
        delete_source_endpoint,
        crawl_url_endpoint,
        reset_database_endpoint,
    ],
    openapi_config=OpenAPIConfig(
        title="Crawler Demo",
        description="A clean web crawler API using domain-driven design",
        version="1.0.0",
        render_plugins=[SwaggerRenderPlugin()],
    ),
    dependencies={"uow": provide_uow},
    cors_config=cors_config,
    lifespan=[db_connection],
)
