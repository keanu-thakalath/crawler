import json

from sqlalchemy import Column, Enum, ForeignKey, Integer, String, Table, Text
from sqlalchemy.types import TypeDecorator

from domain.values import (
    CrawlJobResult,
    DataOrigin,
    ExtractJobResult,
    FocusArea,
    JobError,
    ReviewStatus,
    ScrapeJobResult,
    SourceFormat,
    SummarizeJobResult,
)

from . import mapper_registry, metadata


class JSONList(TypeDecorator):
    impl = Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value


job_errors = Table(
    "job_errors",
    metadata,
    Column("job_id", String(255), ForeignKey("jobs.job_id"), primary_key=True),
    Column("created_at", String(255), nullable=False),
    Column("message", Text, nullable=False),
)

scrape_job_results = Table(
    "scrape_job_results",
    metadata,
    Column("job_id", String(255), ForeignKey("jobs.job_id"), primary_key=True),
    Column("created_at", String(255), nullable=False),
    Column("markdown", Text, nullable=False),
)

extract_job_results = Table(
    "extract_job_results",
    metadata,
    Column("job_id", String(255), ForeignKey("jobs.job_id"), primary_key=True),
    Column("created_at", String(255), nullable=False),
    Column("summary", Text, nullable=False),
    Column("input_tokens", Integer, nullable=False),
    Column("output_tokens", Integer, nullable=False),
    Column("internal_links", JSONList, nullable=False),
    Column("external_links", JSONList, nullable=False),
    Column("file_links", JSONList, nullable=False),
    Column(
        "review_status",
        Enum(ReviewStatus),
        default=ReviewStatus.UNREVIEWED,
        nullable=False,
    ),
)

summarize_job_results = Table(
    "summarize_job_results",
    metadata,
    Column("job_id", String(255), ForeignKey("jobs.job_id"), primary_key=True),
    Column("created_at", String(255), nullable=False),
    Column("summary", Text, nullable=False),
    Column("data_origin", Enum(DataOrigin), nullable=False),
    Column("source_format", Enum(SourceFormat), nullable=False),
    Column("focus_area", Enum(FocusArea), nullable=False),
    Column("input_tokens", Integer, nullable=False),
    Column("output_tokens", Integer, nullable=False),
    Column(
        "review_status",
        Enum(ReviewStatus),
        default=ReviewStatus.UNREVIEWED,
        nullable=False,
    ),
)

crawl_job_results = Table(
    "crawl_job_results",
    metadata,
    Column("job_id", String(255), ForeignKey("jobs.job_id"), primary_key=True),
    Column("created_at", String(255), nullable=False),
    Column("pages_crawled", Integer, nullable=False),
    Column("total_pages_found", Integer, nullable=False),
    Column("max_pages_limit", Integer, nullable=False),
)


def map_values():
    job_error_mapper = mapper_registry.map_imperatively(JobError, job_errors)

    scrape_result_mapper = mapper_registry.map_imperatively(
        ScrapeJobResult, scrape_job_results
    )

    extract_result_mapper = mapper_registry.map_imperatively(
        ExtractJobResult, extract_job_results
    )

    summarize_result_mapper = mapper_registry.map_imperatively(
        SummarizeJobResult, summarize_job_results
    )

    crawl_result_mapper = mapper_registry.map_imperatively(
        CrawlJobResult, crawl_job_results
    )

    return (
        job_error_mapper,
        scrape_result_mapper,
        extract_result_mapper,
        summarize_result_mapper,
        crawl_result_mapper,
    )
