from dataclasses import dataclass
from typing import List


@dataclass
class CrawlRequest:
    url: str

@dataclass
class FileWithoutPage:
    id: int
    url: str


@dataclass
class PageWithoutSource:
    url: str


@dataclass
class SourceWithoutContent:
    url: str
    pages: List[PageWithoutSource]

# Job-related response models
@dataclass
class JobResponse:
    id: int
    job_type: str
    status: str


@dataclass
class ScrapeJobResponse:
    id: int
    page_job_id: int
    markdown: str
    html: str


@dataclass
class ExtractJobResponse:
    id: int
    page_job_id: int
    summary: str
    input_tokens: int
    output_tokens: int
    files: List[FileWithoutPage]


@dataclass
class SummarizeJobResponse:
    id: int
    source_job_id: int
    summary: str
    data_origin: str
    source_format: str
    focus_area: str
    input_tokens: int
    output_tokens: int
