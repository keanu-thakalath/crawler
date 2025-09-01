import abc

from domain.types import NormalizedUrl
from .html_scraper import CrawlbaseScraper
from .html_to_markdown_converter import MarkdownifyConverter
from .pdf_scraper import PdfScraper


class ContentScraper(abc.ABC):
    @abc.abstractmethod
    async def scrape_url_to_markdown(self, url: NormalizedUrl) -> str:
        raise NotImplementedError


class UniversalContentScraper(ContentScraper):
    def __init__(self):
        self.html_scraper = CrawlbaseScraper()
        self.html_converter = MarkdownifyConverter()
        self.pdf_scraper = PdfScraper()

    async def scrape_url_to_markdown(self, url: NormalizedUrl) -> str:
        if NormalizedUrl.is_pdf(url):
            return await self.pdf_scraper.scrape_url(url)
        else:
            html_content = await self.html_scraper.scrape_url(url)
            return self.html_converter.convert_to_markdown(html_content)
