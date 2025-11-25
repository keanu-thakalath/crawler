import uuid
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncGenerator, Generic, List, Optional, TypeVar, Union

from nlp_processing.page_summarizer import PageSummarizer
from nlp_processing.source_analyzer import SourceAnalyzer
from scraping.content_scraper import ContentScraper
from scraping.manual_link_extractor import ManualLinkExtractor

from .types import NormalizedUrl
from .values import (
    CrawlJobResult,
    ExtractJobResult,
    JobError,
    JobResult,
    ReviewStatus,
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
        self, content_scraper: ContentScraper, manual_link_extractor: ManualLinkExtractor
    ) -> AsyncGenerator[ScrapeJob, None]:
        job = ScrapeJob()
        self.jobs.append(job)

        yield job

        try:
            markdown_content = await content_scraper.scrape_url_to_markdown(self.url)
            html_content = await content_scraper.html_scraper.scrape_url(self.url)
            
            internal_links, external_links, file_links = manual_link_extractor.extract_links_from_html(
                html_content, self.url
            )

            job_result = ScrapeJobResult(
                markdown=markdown_content,
                internal_links=internal_links,
                external_links=external_links,
                file_links=file_links
            )
            job.outcome = job_result

            yield job

        except Exception as e:
            job_error = JobError(message=f"{traceback.format_exc()}\n{str(e)}")
            job.outcome = job_error

            yield job

    async def extract_page(
        self, 
        page_summarizer: PageSummarizer, 
        markdown_content: str, 
        scraped_internal_links: List[NormalizedUrl],
        scraped_external_links: List[NormalizedUrl],
        scraped_file_links: List[NormalizedUrl],
        custom_prompt: str | None = None
    ) -> AsyncGenerator[ExtractJob, None]:
        job = ExtractJob()
        self.jobs.append(job)

        yield job

        try:
            (
                summary_result,
                llm_response_metadata,
            ) = await page_summarizer.summarize_page(
                self.url, 
                markdown_content, 
                scraped_internal_links,
                scraped_external_links,
                scraped_file_links,
                custom_prompt
            )

            job_result = ExtractJobResult(
                **llm_response_metadata.__dict__,
                **summary_result.__dict__
            )
            job.outcome = job_result

            yield job

        except Exception as e:
            job_error = JobError(message=f"{traceback.format_exc()}\n{str(e)}")
            job.outcome = job_error

            yield job


@dataclass
class Source:
    url: NormalizedUrl
    pages: List[Page] = field(default_factory=list)
    jobs: List[SourceJob] = field(default_factory=list)

    def all_extract_jobs_approved(self) -> bool:
        """Check if all extract jobs for this source have been approved."""
        extract_jobs = []
        
        for page in self.pages:
            for job in page.jobs:
                if isinstance(job, ExtractJob) and job.outcome:
                    if isinstance(job.outcome, ExtractJobResult):
                        extract_jobs.append(job)
        
        if not extract_jobs:
            return False  # No extract jobs exist
            
        return all(
            job.outcome.review_status == ReviewStatus.APPROVED 
            for job in extract_jobs
        )

    async def crawl_source(
        self,
        max_pages: int,
        content_scraper: ContentScraper,
        manual_link_extractor: ManualLinkExtractor,
        page_summarizer: PageSummarizer,
        extract_prompt: str | None = None,
    ) -> AsyncGenerator[Union[CrawlJob, ScrapeJob, ExtractJob], None]:
        crawl_job = CrawlJob()
        self.jobs.append(crawl_job)

        yield crawl_job

        try:
            url_queue: List[NormalizedUrl] = [self.url]
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

                async for scrape_job in current_page.scrape_page(content_scraper, manual_link_extractor):
                    yield scrape_job

                if isinstance(scrape_job.outcome, ScrapeJobResult):
                    async for extract_job in current_page.extract_page(
                        page_summarizer, 
                        scrape_job.outcome.markdown,
                        scrape_job.outcome.internal_links,
                        scrape_job.outcome.external_links,
                        scrape_job.outcome.file_links,
                        extract_prompt
                    ):
                        yield extract_job

                    if isinstance(extract_job.outcome, ExtractJobResult):
                        for internal_link in extract_job.outcome.relevant_internal_links:
                            if internal_link not in url_queue:
                                url_queue.append(internal_link)
                                total_pages_found += 1

                pages_crawled += 1

            # Note: Source summarization is now triggered automatically 
            # when all extract jobs are approved, not at end of crawl
            
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
        self, source_analyzer: SourceAnalyzer, all_page_summaries: str, custom_prompt: str | None = None
    ) -> AsyncGenerator[SummarizeJob, None]:
        job = SummarizeJob()
        self.jobs.append(job)

        yield job

        try:
            (
                job_result_data,
                llm_response_metadata,
            ) = await source_analyzer.analyze_content(all_page_summaries, str(self.url), custom_prompt)

            job_result = SummarizeJobResult(
                **job_result_data.__dict__, **llm_response_metadata.__dict__
            )
            job.outcome = job_result

            yield job

        except Exception as e:
            job_error = JobError(message=str(e))
            job.outcome = job_error

            yield job
