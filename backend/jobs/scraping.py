from typing import List
from database.models import (
    Source, Page, File, PageJob, SourceJob, ScrapeJob, ExtractJob, SummarizeJob,
    JobStatus, JobType
)
from contextlib import contextmanager
from crawlbase import CrawlingAPI
import logging
from markdownify import markdownify as md
import os
from dotenv import load_dotenv
from llm_processor import extract_page_links, analyze_source_content
from urllib.parse import urljoin, urlparse
from sqlalchemy import select
from sqlalchemy.orm import Session

load_dotenv()

logger = logging.getLogger(__name__)
crawling_api = CrawlingAPI({ 'token': os.getenv('CRAWLBASE_TOKEN') })

class UrlQueue:
    def __init__(self, *urls: str, urls_per_batch=2, max_urls=3):
        self._unprocessed_urls = [*urls]
        self._processed_urls: List[str] = []
        self._url_batch = []
        self._urls_per_batch = urls_per_batch
        self._max_urls = max_urls

    @contextmanager
    def next_url_batch(self):
        self._url_batch = self._unprocessed_urls[:self._urls_per_batch]
        self._unprocessed_urls = self._unprocessed_urls[self._urls_per_batch:]
        try:
            yield self._url_batch
        finally:
            self._processed_urls.extend(self._url_batch)
            self._url_batch = []
    
    def has_next_batch(self):
        return len(self._unprocessed_urls) != 0
    
    def is_in_queue(self, url):
        return url in self._unprocessed_urls or url in self._url_batch or url in self._processed_urls

    def __len__(self):
        return len(self._unprocessed_urls) + len(self._url_batch) + len(self._processed_urls)
    
    def urls_left(self):
        return len(self._unprocessed_urls)
    
    def add_url(self, url: str, source_url: str, session: Session = None):
        """Add a URL to the queue if not already present"""
        if len(self) >= self._max_urls:
            return False
        if (url.endswith('.pdf')):
            return False
        
        # Convert relative URLs to absolute URLs based on source URL
        if source_url and not url.startswith(('http://', 'https://')):
            parsed_base = urlparse(source_url)
            domain_only_base = f"{parsed_base.scheme}://{parsed_base.netloc}/"
            url = urljoin(domain_only_base, url)
        
        normalized_url = url.rstrip("/")
        if not self.is_in_queue(normalized_url):
            self._unprocessed_urls.append(normalized_url)
            
            # Add Page to database
            if session:
                existing_page = session.get(Page, normalized_url)
                if not existing_page:
                    page = Page(url=normalized_url, source_url=source_url)
                    session.add(page)
                    
                    # Create a scrape job for this page
                    scrape_job = PageJob(page_url=page.url, job_type=JobType.SCRAPE)
                    session.add(scrape_job)
                    
                    logger.info(f'Added page and scrape job for: {normalized_url}')
            return True
        return False

def scrape_page(page_url: str, session: Session) -> bool:
    """Scrape a single page"""
    page = session.get(Page, page_url)
    if not page:
        logger.error(f'Page not found: {page_url}')
        return False
    
    # Find pending scrape job
    scrape_job = session.execute(
        select(PageJob).where(
            PageJob.page_url == page.url,
            PageJob.job_type == JobType.SCRAPE,
            PageJob.status == JobStatus.PENDING
        )
    ).scalar_one_or_none()
    
    if not scrape_job:
        logger.error(f'No pending scrape job found for page: {page_url}')
        return False
    
    # Update job status
    scrape_job.status = JobStatus.RUNNING
    session.flush()
    
    try:
        logger.info(f'Scraping page {page_url}')
        response = crawling_api.get(page_url, { 'cookies_session': 'anything' })
        try:
            body = response['body'].decode('utf-8', 'ignore')
        except Exception:
            body = response['body']
        markdown = md(body)
        logger.info(f'Processed {page_url} to get markdown of length {len(markdown)}')
        
        # Create scrape result
        scrape_result = ScrapeJob(
            page_job_id=scrape_job.id,
            markdown=markdown,
            html=body
        )
        session.add(scrape_result)
        
        # Update job status
        scrape_job.status = JobStatus.COMPLETED
        
        return True
        
    except Exception as e:
        logger.error(f'Scraping failed for {page_url}: {e}')
        scrape_job.status = JobStatus.FAILED
        return False

def extract_links(page_url: str, session: Session, url_queue: UrlQueue) -> bool:
    """Extract links from a scraped page"""
    page = session.get(Page, page_url)
    if not page:
        logger.error(f'Page not found: {page_url}')
        return False
    
    # Get completed scrape job
    scrape_job = session.execute(
        select(PageJob)
        .join(ScrapeJob)
        .where(
            PageJob.page_url == page_url,
            PageJob.job_type == JobType.SCRAPE,
            PageJob.status == JobStatus.COMPLETED
        )
    ).scalar_one_or_none()
    
    if not scrape_job:
        logger.error(f'No completed scrape job found for page: {page_url}')
        return False
    
    scrape_result = session.execute(
        select(ScrapeJob).where(ScrapeJob.page_job_id == scrape_job.id)
    ).scalar_one()
    
    # Create extract job
    extract_job = PageJob(page_url=page_url, job_type=JobType.EXTRACT, status=JobStatus.RUNNING)
    session.add(extract_job)
    session.flush()
    
    try:
        # Extract structured data with LLM
        structured_data = extract_page_links(scrape_result.markdown, page_url)
        
        # Create extract result
        extract_result = ExtractJob(
            page_job_id=extract_job.id,
            summary=structured_data.get("summary", ""),
            input_tokens=structured_data.get("input_tokens", 0),
            output_tokens=structured_data.get("output_tokens", 0)
        )
        session.add(extract_result)
        session.flush()
        
        # Add discovered files
        for file_link in structured_data.get("file_links", []):
            file_obj = File(url=file_link, extract_job_id=extract_result.id)
            session.add(file_obj)
            logger.info(f'Added file link: {file_link}')
        
        # Add discovered internal links as new pages/jobs
        for internal_link in structured_data["internal_links"]:
            url_queue.add_url(internal_link, page.source_url, session)
        
        # Update job status
        extract_job.status = JobStatus.COMPLETED
        session.flush()
        
        return True, 
        
    except Exception as e:
        logger.error(f'Link extraction failed for {page_url}: {e}')
        extract_job.status = JobStatus.FAILED
        session.flush()
        return False

def summarize_source(source_url: str, session: Session) -> bool:
    """Summarize and classify a source"""
    source = session.get(Source, source_url)
    if not source:
        logger.error(f'Source not found: {source_url}')
        return False
    
    # Create summarize job
    summarize_job = SourceJob(
        source_url=source_url, 
        job_type=JobType.SUMMARIZE,
        status=JobStatus.RUNNING
    )
    session.add(summarize_job)
    session.flush()
    
    # Get all completed extract results for this source
    extract_results = session.execute(
        select(ExtractJob)
        .join(PageJob)
        .join(Page)
        .where(
            Page.source_url == source_url,
            PageJob.job_type == JobType.EXTRACT,
            PageJob.status == JobStatus.COMPLETED
        )
    ).scalars().all()
    
    if not extract_results:
        logger.error(f'No completed extract results found for source: {source_url}')
        summarize_job.status = JobStatus.FAILED
        session.flush()
        return False
    
    try:
        # Concatenate all page summaries
        all_summaries = ""
        for extract_result in extract_results:
            page_job = session.get(PageJob, extract_result.page_job_id)
            page = session.get(Page, page_job.page_url)
            all_summaries += f"\n\n=== Page: {page.url} ===\n{extract_result.summary}"
        
        # Analyze source content using LLM
        logger.info(f'Analyzing source content for source: {source_url}')
        analysis = analyze_source_content(all_summaries, source.url)
        
        # Create summarize result
        summarize_result = SummarizeJob(
            source_job_id=summarize_job.id,
            summary=analysis.get("summary", ""),
            data_origin=analysis.get("data_origin", ""),
            source_format=analysis.get("source_format", ""),
            focus_area=analysis.get("focus_area", ""),
            input_tokens=analysis.get("input_tokens", 0),
            output_tokens=analysis.get("output_tokens", 0)
        )
        session.add(summarize_result)
        
        # Update job status
        summarize_job.status = JobStatus.COMPLETED
        session.flush()
        
        logger.info(f'Source analysis completed for {source.url}: {analysis.get("data_origin")} - {analysis.get("focus_area")}')
        return True
        
    except Exception as e:
        logger.error(f'Source summarization failed for source {source_url}: {e}')
        summarize_job.status = JobStatus.FAILED
        session.flush()
        return False