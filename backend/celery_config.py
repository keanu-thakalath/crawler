from celery import Celery, Task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def create_celery_app() -> Celery:
    celery_app = Celery(
        "crawler_demo",
        broker="pyamqp://guest@localhost//",
        backend="db+sqlite:///celery_results.db",
        include=["tasks.crawl_tasks"]
    )
    
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
    )
    
    return celery_app


celery_app = create_celery_app()

class DatabaseTask(Task):
    def __init__(self):
        engine = create_engine("sqlite:///crawler.sqlite", echo=True)
        self.engine = engine
        self.Session = sessionmaker(self.engine)

    # def __del__(self):
    #     self.engine.dispose()
