import abc
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.entities import Job, Page, Source


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
