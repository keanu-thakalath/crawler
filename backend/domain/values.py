from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from .types import NormalizedUrl


@dataclass(kw_only=True)
class JobResult:
    created_at: datetime = field(default_factory=datetime.now)


@dataclass(kw_only=True)
class JobError:
    message: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class LLMResponseMetadata:
    input_tokens: int
    output_tokens: int


@dataclass(kw_only=True)
class ScrapeJobResult(JobResult):
    markdown: str
    html: str


@dataclass
class ExtractJobResultData:
    summary: str
    internal_links: List[NormalizedUrl]
    external_links: List[NormalizedUrl]
    file_links: List[NormalizedUrl]


@dataclass(kw_only=True)
class ExtractJobResult(JobResult, ExtractJobResultData, LLMResponseMetadata):
    pass


@dataclass
class SummarizeJobResultData:
    summary: str
    data_origin: str
    source_format: str
    focus_area: str


@dataclass(kw_only=True)
class SummarizeJobResult(JobResult, SummarizeJobResultData, LLMResponseMetadata):
    pass


@dataclass(kw_only=True)
class CrawlJobResult(JobResult):
    pages_crawled: int
    total_pages_found: int
    max_pages_limit: int
