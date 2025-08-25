import abc

from domain.types import NormalizedUrl
from domain.values import ExtractJobResultData, LLMResponseMetadata

from .structured_completion import LiteLLMStructuredCompletion


class PageLinkExtractor(abc.ABC):
    @abc.abstractmethod
    async def extract_links_and_summary(
        self, url: NormalizedUrl, markdown: str
    ) -> tuple[ExtractJobResultData, LLMResponseMetadata]:
        raise NotImplementedError


class LiteLLMPageLinkExtractor(PageLinkExtractor):
    def __init__(self, structured_completion: LiteLLMStructuredCompletion):
        self.structured_completion = structured_completion

    async def extract_links_and_summary(
        self, url: NormalizedUrl, markdown: str
    ) -> tuple[ExtractJobResultData, LLMResponseMetadata]:
        prompt = f"""
Analyze the following markdown content and extract relevant links, plus provide a summary.

Guidelines:
- Only include links that are relevant to the content (no login pages, social media, contact forms, privacy policies, terms of service)
- Internal links are relative URLs or URLs that belong to the same domain
- External links are HTTPS URLs to different domains that provide valuable content
- File links are URLs that point to downloadable files like PDFs, Word docs, Excel files, images, etc.
- If internal or file links are relative, prepend the base path to them to form a complete URL
- Look for links with file extensions like .pdf, .doc, .docx, .xls, .xlsx, .ppt, .pptx, .zip, .png, .jpg, .jpeg, .gif, .svg, etc.
- Exclude navigation, footer, and header links unless they're content-relevant
- Focus on links to articles, resources, documentation, or related content

Markdown content for URL {url}:
{markdown}
"""

        return await self.structured_completion.complete(prompt, ExtractJobResultData)
