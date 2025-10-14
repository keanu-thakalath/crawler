from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List

from .types import NormalizedUrl


class DataOrigin(Enum):
    ACADEMIC = "Academic"
    GOVERNMENT = "Government"
    NEWS = "News"
    BLOG = "Blog"
    NON_PROFIT = "Non-Profit"


class SourceFormat(Enum):
    RESEARCH_PAPER = "Research Paper"
    ARTICLE = "Article"
    DATA_REPOSITORY = "Data Repository"
    HISTORICAL_INFO = "Historical Info"
    POLICY = "Policy"
    LAW = "Law"
    NARRATIVE = "Narrative"
    DATA_VISUALIZATION = "Data Visualization"
    LETTER = "Letter"
    GOVERNMENT_SOURCE = "Government Source"


class FocusArea(Enum):
    NON_HUMAN_ANIMALS = "Non-Human Animals"
    HUMANS = "Humans"
    ENVIRONMENT = "Environment"
    COMMUNITY = "Community"
    BUSINESS = "Business"


class ReviewStatus(Enum):
    UNREVIEWED = "Unreviewed"
    APPROVED = "Approved"


@dataclass(kw_only=True)
class JobResult:
    created_at: datetime = field(default_factory=datetime.now)


@dataclass(kw_only=True)
class JobError:
    message: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass(kw_only=True)
class LLMResponseMetadata:
    input_tokens: int
    output_tokens: int
    prompt: str
    review_status: ReviewStatus = ReviewStatus.UNREVIEWED


@dataclass(kw_only=True)
class ScrapeJobResult(JobResult):
    markdown: str


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
    data_origin: DataOrigin
    source_format: SourceFormat
    focus_area: FocusArea


@dataclass(kw_only=True)
class SummarizeJobResult(JobResult, SummarizeJobResultData, LLMResponseMetadata):
    pass


@dataclass(kw_only=True)
class CrawlJobResult(JobResult):
    pages_crawled: int
    total_pages_found: int
    max_pages_limit: int
