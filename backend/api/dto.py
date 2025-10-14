from dataclasses import dataclass

from .auth import Token


@dataclass
class CrawlRequest:
    url: str
    max_pages: int = 3
    extract_prompt: str | None = None
    summarize_prompt: str | None = None


@dataclass
class ScrapeRequest:
    page_url: str


@dataclass
class ExtractRequest:
    page_url: str
    markdown_content: str
    prompt: str | None = None


@dataclass
class SummarizeRequest:
    source_url: str
    all_page_summaries: str
    prompt: str | None = None


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
