import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncGenerator, Generic, List, Optional, TypeVar, Union

from nlp_processing.page_link_extractor import PageLinkExtractor
from nlp_processing.source_analyzer import SourceAnalyzer
from scraping.html_scraper import HtmlScraper
from scraping.html_to_markdown_converter import HtmlToMarkdownConverter

from .types import NormalizedUrl
from .values import (
    CrawlJobResult,
    ExtractJobResult,
    JobError,
    JobResult,
    ScrapeJobResult,
    SummarizeJobResult,
)

TJobResult = TypeVar("TJobResult", bound=JobResult)
Outcome = Optional[Union[JobError, TJobResult]]


@dataclass(kw_only=True)
class Job(Generic[TJobResult]):
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    outcome: Outcome[TJobResult] = None


ScrapeJob = Job[ScrapeJobResult]
ExtractJob = Job[ExtractJobResult]
SummarizeJob = Job[SummarizeJobResult]
CrawlJob = Job[CrawlJobResult]

PageJob = Union[ScrapeJob, ExtractJob]
SourceJob = Union[SummarizeJob, CrawlJob]


@dataclass
class Page:
    url: NormalizedUrl
    jobs: List[PageJob] = field(default_factory=list)

    async def scrape_page(
        self, html_scraper: HtmlScraper, html_converter: HtmlToMarkdownConverter
    ) -> AsyncGenerator[ScrapeJob, None]:
        job = ScrapeJob()
        self.jobs.append(job)

        yield job

        try:
            html_content = await html_scraper.scrape_url(self.url)
            markdown_content = html_converter.convert_to_markdown(html_content)

            job_result = ScrapeJobResult(markdown=markdown_content, html=html_content)
            job.outcome = job_result

            yield job

        except Exception as e:
            job_error = JobError(message=str(e))
            job.outcome = job_error

            yield job

    async def extract_page(
        self, page_link_extractor: PageLinkExtractor, markdown_content: str
    ) -> AsyncGenerator[ExtractJob, None]:
        job = ExtractJob()
        self.jobs.append(job)

        yield job

        try:
            (
                job_result_data,
                llm_response_metadata,
            ) = await page_link_extractor.extract_links_and_summary(
                self.url, markdown_content
            )

            job_result = ExtractJobResult(
                input_tokens=llm_response_metadata.input_tokens,
                output_tokens=llm_response_metadata.output_tokens,
                summary=job_result_data.summary,
                internal_links=job_result_data.internal_links,
                external_links=job_result_data.external_links,
                file_links=job_result_data.file_links,
            )
            job.outcome = job_result

            yield job

        except Exception as e:
            job_error = JobError(message=str(e))
            job.outcome = job_error

            yield job


@dataclass
class Source:
    url: NormalizedUrl
    pages: List[Page] = field(default_factory=list)
    jobs: List[SourceJob] = field(default_factory=list)

    async def crawl_source(
        self,
        max_pages: int,
        html_scraper: HtmlScraper,
        html_converter: HtmlToMarkdownConverter,
        page_link_extractor: PageLinkExtractor,
        source_analyzer: SourceAnalyzer,
    ) -> AsyncGenerator[Union[CrawlJob, ScrapeJob, ExtractJob, SummarizeJob], None]:
        crawl_job = CrawlJob()
        self.jobs.append(crawl_job)

        yield crawl_job

        try:
            url_queue: List[NormalizedUrl] = [self.url]
            page_summaries: List[str] = []
            pages_crawled = 0
            total_pages_found = 1

            while url_queue and pages_crawled < max_pages:
                current_url = url_queue.pop(0)

                current_page = None
                for page in self.pages:
                    if page.url == current_url:
                        current_page = page
                        break

                if not current_page:
                    current_page = Page(url=current_url)
                    self.pages.append(current_page)

                async for scrape_job in current_page.scrape_page(
                    html_scraper, html_converter
                ):
                    yield scrape_job

                if isinstance(scrape_job.outcome, ScrapeJobResult):
                    async for extract_job in current_page.extract_page(
                        page_link_extractor, scrape_job.outcome.markdown
                    ):
                        yield extract_job

                    if isinstance(extract_job.outcome, ExtractJobResult):
                        page_summaries.append(
                            f"Markdown for {current_page.url}:\n\n{extract_job.outcome.summary}"
                        )
                        for internal_link in extract_job.outcome.internal_links:
                            if internal_link not in url_queue:
                                url_queue.append(internal_link)
                                total_pages_found += 1

                pages_crawled += 1

            all_page_summaries = "\n\n".join(page_summaries)
            async for summary_job in self.summarize_source(
                source_analyzer, all_page_summaries
            ):
                yield summary_job

            crawl_job.outcome = CrawlJobResult(
                pages_crawled=pages_crawled,
                total_pages_found=total_pages_found,
                max_pages_limit=max_pages,
            )

            yield crawl_job

        except Exception as e:
            job_error = JobError(message=str(e))
            crawl_job.outcome = job_error

            yield crawl_job

    async def summarize_source(
        self, source_analyzer: SourceAnalyzer, all_page_summaries: str
    ) -> AsyncGenerator[SummarizeJob, None]:
        job = SummarizeJob()
        self.jobs.append(job)

        yield job

        try:
            (
                job_result_data,
                llm_response_metadata,
            ) = await source_analyzer.analyze_content(all_page_summaries, str(self.url))

            job_result = SummarizeJobResult(
                **job_result_data.__dict__, **llm_response_metadata.__dict__
            )
            job.outcome = job_result

            yield job

        except Exception as e:
            job_error = JobError(message=str(e))
            job.outcome = job_error

            yield job
