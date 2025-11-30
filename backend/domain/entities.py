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
        candidate_internal_links: List[NormalizedUrl],
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
                candidate_internal_links,
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
                print(job)
                if job.outcome and isinstance(job.outcome, ExtractJobResult):
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
            candidate_internal_links: List[NormalizedUrl] = []
            processed_pages: set[NormalizedUrl] = set()
            pages_crawled = 0
            total_pages_found = 1

            while url_queue and pages_crawled < max_pages:
                current_url = url_queue.pop(0)
                processed_pages.add(current_url)

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
                    # Add newly discovered internal links to candidates
                    for internal_link in scrape_job.outcome.internal_links:
                        if internal_link not in candidate_internal_links:
                            candidate_internal_links.append(internal_link)
                            total_pages_found += 1

                    # Filter candidate links to exclude processed pages
                    filtered_candidate_links = [
                        link for link in candidate_internal_links 
                        if link not in processed_pages
                    ]

                    async for extract_job in current_page.extract_page(
                        page_summarizer, 
                        scrape_job.outcome.markdown,
                        filtered_candidate_links,
                        extract_prompt
                    ):
                        yield extract_job

                    if isinstance(extract_job.outcome, ExtractJobResult):
                        # Add next internal link selected by LLM to queue
                        if extract_job.outcome.next_internal_link:
                            if extract_job.outcome.next_internal_link not in processed_pages:
                                url_queue.append(extract_job.outcome.next_internal_link)

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
            job_error = JobError(message=f"{traceback.format_exc()}\n{str(e)}")
            crawl_job.outcome = job_error

            yield crawl_job

    async def summarize_source(
        self, source_analyzer: SourceAnalyzer, all_page_summaries: str, custom_prompt: str | None = None
    ) -> AsyncGenerator[SummarizeJob, None]:
        job = SummarizeJob()
        self.jobs.append(job)

        yield job

        try:
            # Collect all external links from pages' scrape jobs
            all_external_links: List[NormalizedUrl] = []
            for page in self.pages:
                for page_job in page.jobs:
                    if isinstance(page_job.outcome, ScrapeJobResult):
                        all_external_links.extend(page_job.outcome.external_links)
            
            # Remove duplicates while preserving order
            unique_external_links = []
            seen = set()
            for link in all_external_links:
                if link not in seen:
                    unique_external_links.append(link)
                    seen.add(link)

            (
                job_result_data,
                llm_response_metadata,
            ) = await source_analyzer.analyze_content(all_page_summaries, str(self.url), unique_external_links, custom_prompt)

            job_result = SummarizeJobResult(
                **job_result_data.__dict__, **llm_response_metadata.__dict__
            )
            job.outcome = job_result

            yield job

        except Exception as e:
            job_error = JobError(message=f"{traceback.format_exc()}\n{str(e)}")
            job.outcome = job_error

            yield job
