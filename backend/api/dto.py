from dataclasses import dataclass

from .auth import Token


@dataclass
class CrawlRequest:
    url: str
    max_pages: int = 3


@dataclass
class ScrapeRequest:
    page_url: str


@dataclass
class ExtractRequest:
    page_url: str
    markdown_content: str


@dataclass
class SummarizeRequest:
    source_url: str
    all_page_summaries: str


@dataclass
class AddPageToSourceRequest:
    source_url: str
    page_url: str


@dataclass
class EditJobSummaryRequest:
    summary: str


@dataclass
class TokenResponse:
    token: Token
