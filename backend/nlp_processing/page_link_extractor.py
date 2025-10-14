import abc
from dataclasses import dataclass
from typing import List

from domain.types import NormalizedUrl
from domain.values import ExtractJobResultData, LLMResponseMetadata

from .structured_completion import LiteLLMStructuredCompletion


@dataclass
class ExtractJobResultRawData:
    summary: str
    internal_links: List[str]
    external_links: List[str]
    file_links: List[str]


class PageLinkExtractor(abc.ABC):
    @abc.abstractmethod
    async def extract_links_and_summary(
        self, url: NormalizedUrl, markdown: str, custom_prompt: str | None = None
    ) -> tuple[ExtractJobResultData, LLMResponseMetadata]:
        raise NotImplementedError


class LiteLLMPageLinkExtractor(PageLinkExtractor):
    def __init__(self, structured_completion: LiteLLMStructuredCompletion):
        self.structured_completion = structured_completion

    @staticmethod
    def _try_normalize_url(url: str) -> NormalizedUrl | None:
        try:
            return NormalizedUrl(url)
        except Exception:
            return None

    async def extract_links_and_summary(
        self, url: NormalizedUrl, markdown: str, custom_prompt: str | None = None
    ) -> tuple[ExtractJobResultData, LLMResponseMetadata]:
        base_prompt = """Analyze the following markdown content and extract relevant links, plus provide a summary.

Guidelines:
- Only include links that are relevant to the content (no login pages, social media, contact forms, privacy policies, terms of service)
- Internal links are relative URLs or URLs that belong to the same domain
- External links are HTTPS URLs to different domains that provide valuable content
- File links are URLs that point to downloadable files like PDFs, Word docs, Excel files, images, etc.
- If internal or file links are relative, prepend the base path to them to form a complete URL
- Look for links with file extensions like .pdf, .doc, .docx, .xls, .xlsx, .ppt, .pptx, .zip, .png, .jpg, .jpeg, .gif, .svg, etc.
- Exclude navigation, footer, and header links unless they're content-relevant
- Focus on links to articles, resources, documentation, or related content"""

        prompt_to_use = custom_prompt if custom_prompt else base_prompt
        full_prompt = f"{prompt_to_use}\n\nMarkdown content for URL {url}:\n{markdown}"

        raw_result, metadata = await self.structured_completion.complete(
            full_prompt, ExtractJobResultRawData
        )
        
        # Override the stored prompt to exclude markdown content
        metadata = LLMResponseMetadata(
            input_tokens=metadata.input_tokens,
            output_tokens=metadata.output_tokens,
            prompt=prompt_to_use,
            review_status=metadata.review_status,
        )

        def validate_urls(urls: List[str]) -> List[NormalizedUrl]:
            return [
                normalized_url
                for url in urls
                if (normalized_url := self._try_normalize_url(url)) is not None
            ]

        # Validate and filter URLs
        internal_links = validate_urls(raw_result.internal_links)
        external_links = validate_urls(raw_result.external_links)
        file_links = validate_urls(raw_result.file_links)

        validated_result = ExtractJobResultData(
            summary=raw_result.summary,
            internal_links=internal_links,
            external_links=external_links,
            file_links=file_links,
        )

        return validated_result, metadata
