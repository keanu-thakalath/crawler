import abc
from typing import List, Optional

from sqlalchemy import select, exists, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.entities import Job, Page, Source
from domain.values import ReviewStatus, ExtractJobResult, SummarizeJobResult, JobError, CrawlJobResult


class SourceRepository(abc.ABC):
    @abc.abstractmethod
    async def add(self, source: Source) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def get(self, url: str) -> Optional[Source]:
        raise NotImplementedError

    @abc.abstractmethod
    async def list_all(self) -> List[Source]:
        raise NotImplementedError

    @abc.abstractmethod
    async def delete(self, source: Source) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_sources_with_unreviewed_jobs(self) -> List[Source]:
        """Get sources with unreviewed extract/summarize jobs."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_sources_with_failed_jobs(self) -> List[Source]:
        """Get sources with failed jobs."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_crawled_sources(self) -> List[Source]:
        """Get sources with completed crawl jobs."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_discovered_sources(self) -> List[Source]:
        """Get sources with no crawl jobs (discovered via external links)."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_in_progress_sources(self) -> List[Source]:
        """Get sources with jobs but no completed crawl results."""
        raise NotImplementedError


class PageRepository(abc.ABC):
    @abc.abstractmethod
    async def add(self, page: Page) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def get(self, url: str) -> Optional[Page]:
        raise NotImplementedError


class SqlAlchemySourceRepository(SourceRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, source: Source) -> None:
        self.session.add(source)

    async def get(self, url: str) -> Optional[Source]:
        stmt = (
            select(Source)
            .where(Source.url == url)
            .options(
                selectinload(Source.pages),
                selectinload(Source.jobs).selectinload(Job._error),
                selectinload(Source.jobs).selectinload(Job._scrape_result),
                selectinload(Source.jobs).selectinload(Job._extract_result),
                selectinload(Source.jobs).selectinload(Job._summarize_result),
                selectinload(Source.jobs).selectinload(Job._crawl_result),
                selectinload(Source.pages)
                .selectinload(Page.jobs)
                .selectinload(Job._error),
                selectinload(Source.pages)
                .selectinload(Page.jobs)
                .selectinload(Job._scrape_result),
                selectinload(Source.pages)
                .selectinload(Page.jobs)
                .selectinload(Job._extract_result),
                selectinload(Source.pages)
                .selectinload(Page.jobs)
                .selectinload(Job._summarize_result),
                selectinload(Source.pages)
                .selectinload(Page.jobs)
                .selectinload(Job._crawl_result),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> List[Source]:
        stmt = select(Source).options(
            selectinload(Source.pages),
            selectinload(Source.jobs).selectinload(Job._error),
            selectinload(Source.jobs).selectinload(Job._scrape_result),
            selectinload(Source.jobs).selectinload(Job._extract_result),
            selectinload(Source.jobs).selectinload(Job._summarize_result),
            selectinload(Source.jobs).selectinload(Job._crawl_result),
            selectinload(Source.pages).selectinload(Page.jobs).selectinload(Job._error),
            selectinload(Source.pages)
            .selectinload(Page.jobs)
            .selectinload(Job._scrape_result),
            selectinload(Source.pages)
            .selectinload(Page.jobs)
            .selectinload(Job._extract_result),
            selectinload(Source.pages)
            .selectinload(Page.jobs)
            .selectinload(Job._summarize_result),
            selectinload(Source.pages)
            .selectinload(Page.jobs)
            .selectinload(Job._crawl_result),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, source: Source) -> None:
        await self.session.delete(source)

    async def get_sources_with_unreviewed_jobs(self) -> List[Source]:
        """Get sources with unreviewed extract/summarize jobs."""
        # Sources with unreviewed source-level jobs (summarize jobs)
        unreviewed_source_jobs_subq = exists().where(
            and_(
                Job.source_url == Source.url,
                Job.page_url.is_(None),  # Source-level job
                Job._summarize_result.has(),
                Job._summarize_result.has(review_status=ReviewStatus.UNREVIEWED)
            )
        )

        # Sources with unreviewed page-level jobs (extract jobs)
        unreviewed_page_jobs_subq = exists().where(
            and_(
                Job.source_url == Source.url,
                Job.page_url.isnot(None),  # Page-level job
                Job._extract_result.has(),
                Job._extract_result.has(review_status=ReviewStatus.UNREVIEWED)
            )
        )

        stmt = select(Source).where(
            or_(unreviewed_source_jobs_subq, unreviewed_page_jobs_subq)
        ).options(
            selectinload(Source.pages),
            selectinload(Source.jobs).selectinload(Job._error),
            selectinload(Source.jobs).selectinload(Job._scrape_result),
            selectinload(Source.jobs).selectinload(Job._extract_result),
            selectinload(Source.jobs).selectinload(Job._summarize_result),
            selectinload(Source.jobs).selectinload(Job._crawl_result),
            selectinload(Source.pages).selectinload(Page.jobs).selectinload(Job._error),
            selectinload(Source.pages).selectinload(Page.jobs).selectinload(Job._scrape_result),
            selectinload(Source.pages).selectinload(Page.jobs).selectinload(Job._extract_result),
            selectinload(Source.pages).selectinload(Page.jobs).selectinload(Job._summarize_result),
            selectinload(Source.pages).selectinload(Page.jobs).selectinload(Job._crawl_result),
        )
        result = await self.session.execute(stmt)
        db_sources = list(result.scalars().all())
        
        # Create new Source and Page instances not linked to the database
        sources = []
        for db_source in db_sources:
            new_pages = []
            for db_page in db_source.pages:
                new_page = Page(url=db_page.url, jobs=list(db_page.jobs))
                new_pages.append(new_page)
            
            new_source = Source(url=db_source.url, jobs=list(db_source.jobs), pages=new_pages)
            sources.append(new_source)
        
        return sources

    async def get_sources_with_failed_jobs(self) -> List[Source]:
        """Get sources with failed jobs."""
        # Sources with failed source-level jobs
        failed_source_jobs_subq = exists().where(
            and_(
                Job.source_url == Source.url,
                Job.page_url.is_(None),
                Job._error.has()
            )
        )

        # Sources with failed page-level jobs
        failed_page_jobs_subq = exists().where(
            and_(
                Job.source_url == Source.url,
                Job.page_url.isnot(None),
                Job._error.has()
            )
        )

        stmt = select(Source).where(
            or_(failed_source_jobs_subq, failed_page_jobs_subq)
        ).options(
            selectinload(Source.pages),
            selectinload(Source.jobs).selectinload(Job._error),
            selectinload(Source.jobs).selectinload(Job._scrape_result),
            selectinload(Source.jobs).selectinload(Job._extract_result),
            selectinload(Source.jobs).selectinload(Job._summarize_result),
            selectinload(Source.jobs).selectinload(Job._crawl_result),
            selectinload(Source.pages).selectinload(Page.jobs).selectinload(Job._error),
            selectinload(Source.pages).selectinload(Page.jobs).selectinload(Job._scrape_result),
            selectinload(Source.pages).selectinload(Page.jobs).selectinload(Job._extract_result),
            selectinload(Source.pages).selectinload(Page.jobs).selectinload(Job._summarize_result),
            selectinload(Source.pages).selectinload(Page.jobs).selectinload(Job._crawl_result),
        )
        result = await self.session.execute(stmt)
        db_sources = list(result.scalars().all())
        
        # Create new Source and Page instances not linked to the database
        sources = []
        for db_source in db_sources:
            new_pages = []
            for db_page in db_source.pages:
                new_page = Page(url=db_page.url, jobs=list(db_page.jobs))
                new_pages.append(new_page)
            
            new_source = Source(url=db_source.url, jobs=list(db_source.jobs), pages=new_pages)
            sources.append(new_source)
        
        return sources

    async def get_crawled_sources(self) -> List[Source]:
        """Get sources with completed crawl jobs."""
        crawl_jobs_subq = exists().where(
            and_(
                Job.source_url == Source.url,
                Job.page_url.is_(None),
                Job._crawl_result.has()
            )
        )

        stmt = select(Source).where(crawl_jobs_subq).options(
            selectinload(Source.jobs).selectinload(Job._error),
            selectinload(Source.jobs).selectinload(Job._scrape_result),
            selectinload(Source.jobs).selectinload(Job._extract_result),
            selectinload(Source.jobs).selectinload(Job._summarize_result),
            selectinload(Source.jobs).selectinload(Job._crawl_result),
        )
        result = await self.session.execute(stmt)
        db_sources = list(result.scalars().all())
        
        # Create new Source instances not linked to the database
        sources = []
        for db_source in db_sources:
            # Create new Source with jobs but no pages to match original API
            new_source = Source(url=db_source.url, jobs=list(db_source.jobs), pages=[])
            sources.append(new_source)
        
        return sources

    async def get_discovered_sources(self) -> List[Source]:
        """Get sources with no crawl jobs (discovered via external links)."""
        no_jobs_subq = ~exists().where(Job.source_url == Source.url)

        stmt = select(Source).where(no_jobs_subq).options(
            selectinload(Source.jobs).selectinload(Job._error),
            selectinload(Source.jobs).selectinload(Job._scrape_result),
            selectinload(Source.jobs).selectinload(Job._extract_result),
            selectinload(Source.jobs).selectinload(Job._summarize_result),
            selectinload(Source.jobs).selectinload(Job._crawl_result),
        )
        result = await self.session.execute(stmt)
        db_sources = list(result.scalars().all())
        
        # Create new Source instances not linked to the database
        sources = []
        for db_source in db_sources:
            # Create new Source with jobs but no pages to match original API
            new_source = Source(url=db_source.url, jobs=list(db_source.jobs), pages=[])
            sources.append(new_source)
        
        return sources

    async def get_in_progress_sources(self) -> List[Source]:
        """Get sources with at least one incomplete job (job.outcome is None)."""
        # Sources that have at least one incomplete job (no outcome)
        incomplete_jobs_subq = exists().where(
            and_(
                Job.source_url == Source.url,
                ~Job._error.has(),
                ~Job._scrape_result.has(), 
                ~Job._extract_result.has(),
                ~Job._summarize_result.has(),
                ~Job._crawl_result.has()
            )
        )

        stmt = select(Source).where(incomplete_jobs_subq).options(
            selectinload(Source.jobs).selectinload(Job._error),
            selectinload(Source.jobs).selectinload(Job._scrape_result),
            selectinload(Source.jobs).selectinload(Job._extract_result),
            selectinload(Source.jobs).selectinload(Job._summarize_result),
            selectinload(Source.jobs).selectinload(Job._crawl_result),
        )
        result = await self.session.execute(stmt)
        db_sources = list(result.scalars().all())
        
        # Create new Source instances not linked to the database
        sources = []
        for db_source in db_sources:
            # Create new Source with jobs but no pages to match original API
            new_source = Source(url=db_source.url, jobs=list(db_source.jobs), pages=[])
            sources.append(new_source)
        
        return sources


class JobRepository(abc.ABC):
    @abc.abstractmethod
    async def get_by_id(self, job_id: str) -> Optional[Job]:
        raise NotImplementedError


class SqlAlchemyPageRepository(PageRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, page: Page) -> None:
        self.session.add(page)

    async def get(self, url: str) -> Optional[Page]:
        stmt = (
            select(Page)
            .where(Page.url == url)
            .options(
                selectinload(Page.jobs).selectinload(Job._error),
                selectinload(Page.jobs).selectinload(Job._scrape_result),
                selectinload(Page.jobs).selectinload(Job._extract_result),
                selectinload(Page.jobs).selectinload(Job._summarize_result),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class SqlAlchemyJobRepository(JobRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, job_id: str) -> Optional[Job]:
        stmt = (
            select(Job)
            .where(Job.job_id == job_id)
            .options(
                selectinload(Job._error),
                selectinload(Job._scrape_result),
                selectinload(Job._extract_result),
                selectinload(Job._summarize_result),
                selectinload(Job._crawl_result),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
