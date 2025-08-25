import abc
import os

from crawlbase import CrawlingAPI
from dotenv import load_dotenv

load_dotenv()


class HtmlScraper(abc.ABC):
    @abc.abstractmethod
    async def scrape_url(self, url: str) -> str:
        raise NotImplementedError


class CrawlbaseScraper(HtmlScraper):
    def __init__(self):
        self.crawling_api = CrawlingAPI({"token": os.getenv("CRAWLBASE_TOKEN")})

    async def scrape_url(self, url: str) -> str:
        response = self.crawling_api.get(url, {"cookies_session": "anything"})

        try:
            return response["body"].decode("utf-8", "ignore")
        except Exception:
            return response["body"]
