from enum import Enum
from typing import List, Optional, Self
from urllib.parse import urljoin

from .exceptions import InvalidUrlError

class UrlType(Enum):
    HTML = "html"
    PDF = "pdf"

class NormalizedUrl(str):
    def __new__(cls, url: str):
        if not url:
            raise InvalidUrlError(url, "URL cannot be empty")

        if not url.startswith("https://"):
            raise InvalidUrlError(url, "Only HTTPS URLs are allowed")

        normalized_url = url.rstrip("/")

        if not normalized_url.count("://") == 1:
            raise InvalidUrlError(url, "Invalid URL format")

        return super().__new__(cls, normalized_url)
    
    @classmethod
    def try_new(cls, url: str):
        try:
            return cls(url)
        except InvalidUrlError:
            return None


    @classmethod
    def from_path(cls, path: str, base_url: Self) -> Self:
        return cls(urljoin(base_url, path))
    
    @classmethod
    def from_string_list(cls, url_strings: List[str]) -> List[Self]:
        """Convert a list of string URLs to NormalizedUrls, skipping invalid ones."""
        normalized_urls = []
        for url_str in url_strings:
            try:
                normalized_urls.append(cls(url_str))
            except InvalidUrlError:
                pass  # Skip invalid URLs
        return normalized_urls

    @property
    def type(self) -> UrlType:
        if self.lower().endswith(".pdf"):
            return UrlType.PDF
        return UrlType.HTML
