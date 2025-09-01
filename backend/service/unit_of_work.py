from __future__ import annotations

import abc

from database.repositories import (
    JobRepository,
    PageRepository,
    SourceRepository,
    SqlAlchemyJobRepository,
    SqlAlchemyPageRepository,
    SqlAlchemySourceRepository,
)
from nlp_processing.page_link_extractor import (
    LiteLLMPageLinkExtractor,
    PageLinkExtractor,
)
from nlp_processing.source_analyzer import LiteLLMSourceAnalyzer, SourceAnalyzer
from nlp_processing.structured_completion import LiteLLMStructuredCompletion
from scraping.html_scraper import CrawlbaseScraper, HtmlScraper
from scraping.html_to_markdown_converter import (
    HtmlToMarkdownConverter,
    MarkdownifyConverter,
)


class UnitOfWork(abc.ABC):
    sources: SourceRepository
    pages: PageRepository
    jobs: JobRepository
    html_scraper: HtmlScraper
    html_converter: HtmlToMarkdownConverter
    page_link_extractor: PageLinkExtractor
    source_analyzer: SourceAnalyzer

    async def __aenter__(self) -> UnitOfWork:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.rollback()

    @abc.abstractmethod
    async def commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def rollback(self):
        raise NotImplementedError


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def __aenter__(self):
        self.session = self.session_factory()
        self.sources = SqlAlchemySourceRepository(self.session)
        self.pages = SqlAlchemyPageRepository(self.session)
        self.jobs = SqlAlchemyJobRepository(self.session)
        self.html_scraper = CrawlbaseScraper()
        self.html_converter = MarkdownifyConverter()

        # Create shared structured completion instance
        structured_completion = LiteLLMStructuredCompletion()

        self.page_link_extractor = LiteLLMPageLinkExtractor(structured_completion)
        self.source_analyzer = LiteLLMSourceAnalyzer(structured_completion)
        return await super().__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await super().__aexit__(exc_type, exc_val, exc_tb)
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
