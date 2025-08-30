from typing import Self
from urllib.parse import urljoin

from .exceptions import InvalidUrlError


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
    def from_path(cls, path: str, base_url: Self):
        return cls(urljoin(base_url, path))


