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
from nlp_processing.page_summarizer import LiteLLMPageSummarizer, PageSummarizer
from nlp_processing.source_analyzer import LiteLLMSourceAnalyzer, SourceAnalyzer
from nlp_processing.structured_completion import LiteLLMStructuredCompletion
from scraping.content_scraper import ContentScraper, UniversalContentScraper
from scraping.manual_link_extractor import HtmlManualLinkExtractor, ManualLinkExtractor


class UnitOfWork(abc.ABC):
    sources: SourceRepository
    pages: PageRepository
    jobs: JobRepository
    content_scraper: ContentScraper
    manual_link_extractor: ManualLinkExtractor
    page_summarizer: PageSummarizer
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
        self.content_scraper = UniversalContentScraper()
        self.manual_link_extractor = HtmlManualLinkExtractor()

        # Create shared structured completion instance
        structured_completion = LiteLLMStructuredCompletion()

        self.page_summarizer = LiteLLMPageSummarizer(structured_completion)
        self.source_analyzer = LiteLLMSourceAnalyzer(structured_completion)
        return await super().__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await super().__aexit__(exc_type, exc_val, exc_tb)
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
