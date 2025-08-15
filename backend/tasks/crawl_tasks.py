from celery_config import DatabaseTask, celery_app
from database.models import Source, Page, SourceJob, JobType, JobStatus
from jobs.scraping import UrlQueue, scrape_page, extract_links, summarize_source
from celery.utils.log import get_task_logger
from sqlalchemy import select

logger = get_task_logger(__name__)

@celery_app.task(base=DatabaseTask, bind=True)
def crawl_url(self: DatabaseTask, source_url: str):
    with self.Session.begin() as session:
        # Create source
        source = Source(url=source_url)
        session.add(source)
        session.flush()  # Get the source ID
        
        # Create crawl job
        crawl_job = SourceJob(source_url=source.url, job_type=JobType.CRAWL, status=JobStatus.RUNNING)
        session.add(crawl_job)
        
        url_queue = UrlQueue()
        url_queue.add_url(source_url, source.url, session)

    # Process all pages sequentially using job functions
    while url_queue.has_next_batch():
        with url_queue.next_url_batch() as url_batch:
            for current_url in url_batch:
                with self.Session.begin() as session:
                    # Run scrape job
                    if scrape_page(current_url, session):
                        logger.info(f'Successfully scraped: {current_url}')
                        
                with self.Session.begin() as session:
                    # Run extract job
                    if extract_links(current_url, session, url_queue):
                        logger.info(f'Successfully extracted links from: {current_url}')
    
    # After all pages processed, run summarize job
    with self.Session.begin() as session:
        if summarize_source(source_url, session):
            logger.info(f'Successfully summarized source: {source_url}')
        
    with self.Session.begin() as session:
        # Update crawl job status
        crawl_job = session.execute(
            select(SourceJob).where(
                SourceJob.source_url == source_url,
                SourceJob.job_type == JobType.CRAWL
            )
        ).scalar_one()
        crawl_job.status = JobStatus.COMPLETED