# Import tasks from the new tasks directory
from tasks.crawl_tasks import crawl_url
from celery_config import celery_app

# This allows backward compatibility with existing imports
__all__ = ["crawl_url", "celery_app"]