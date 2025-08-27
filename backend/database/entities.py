from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from domain.entities import Job, Page, Source
from domain.values import (
    CrawlJobResult,
    ExtractJobResult,
    JobError,
    ScrapeJobResult,
    SummarizeJobResult,
)

from . import mapper_registry, metadata


def create_entity_tables():
    sources = Table(
        "sources",
        metadata,
        Column("url", String(255), primary_key=True),
    )

    pages = Table(
        "pages",
        metadata,
        Column("url", String(255), primary_key=True),
        Column("source_url", ForeignKey("sources.url"), nullable=False),
    )

    jobs = Table(
        "jobs",
        metadata,
        Column("job_id", String(255), primary_key=True),
        Column("created_at", String(255), nullable=False),
        Column("page_url", ForeignKey("pages.url"), nullable=True),
        Column("source_url", ForeignKey("sources.url"), nullable=True),
    )

    return sources, pages, jobs


def map_entities(
    job_error_mapper,
    scrape_result_mapper,
    extract_result_mapper,
    summarize_result_mapper,
    crawl_result_mapper,
):
    sources, pages, jobs = create_entity_tables()

    job_mapper = mapper_registry.map_imperatively(
        Job,
        jobs,
        properties={
            "_error": relationship(
                job_error_mapper, uselist=False, cascade="all, delete-orphan"
            ),
            "_scrape_result": relationship(
                scrape_result_mapper, uselist=False, cascade="all, delete-orphan"
            ),
            "_extract_result": relationship(
                extract_result_mapper, uselist=False, cascade="all, delete-orphan"
            ),
            "_summarize_result": relationship(
                summarize_result_mapper, uselist=False, cascade="all, delete-orphan"
            ),
            "_crawl_result": relationship(
                crawl_result_mapper, uselist=False, cascade="all, delete-orphan"
            ),
        },
    )

    def outcome_getter(self):
        return (
            self._error
            or self._scrape_result
            or self._extract_result
            or self._summarize_result
            or self._crawl_result
        )

    def outcome_setter(self, value):
        self._error = None
        self._scrape_result = None
        self._extract_result = None
        self._summarize_result = None
        self._crawl_result = None
        if isinstance(value, JobError):
            self._error = value
        elif isinstance(value, ScrapeJobResult):
            self._scrape_result = value
        elif isinstance(value, ExtractJobResult):
            self._extract_result = value
        elif isinstance(value, SummarizeJobResult):
            self._summarize_result = value
        elif isinstance(value, CrawlJobResult):
            self._crawl_result = value

    Job.outcome = hybrid_property(outcome_getter, outcome_setter)

    source_mapper = mapper_registry.map_imperatively(
        Source,
        sources,
        properties={
            "pages": relationship(
                lambda: page_mapper,
                collection_class=list,
                cascade="all, delete-orphan",
            ),
            "jobs": relationship(
                job_mapper,
                collection_class=list,
                cascade="all, delete-orphan",
            ),
        },
    )

    page_mapper = mapper_registry.map_imperatively(
        Page,
        pages,
        properties={
            "jobs": relationship(
                job_mapper,
                collection_class=list,
                cascade="all, delete-orphan",
            )
        },
    )

    return source_mapper, page_mapper, job_mapper
