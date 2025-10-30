import abc
import re
from typing import List
from urllib.parse import urljoin, urlparse

from domain.types import NormalizedUrl


class ManualLinkExtractor(abc.ABC):
    @abc.abstractmethod
    def extract_links_from_html(self, html_content: str, base_url: NormalizedUrl) -> tuple[List[NormalizedUrl], List[NormalizedUrl], List[NormalizedUrl]]:
        raise NotImplementedError


class HtmlManualLinkExtractor(ManualLinkExtractor):
    def __init__(self):
        self.file_extensions = {
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
            '.zip', '.tar', '.gz', '.rar', '.7z', '.png', '.jpg', '.jpeg', 
            '.gif', '.svg', '.bmp', '.webp', '.ico', '.csv', '.txt', '.rtf'
        }
        
        # URLs to exclude (navigation, footer, header, social media, etc.)
        self.exclude_patterns = [
            r'/login', r'/signin', r'/register', r'/signup', r'/contact',
            r'/privacy', r'/terms', r'/cookie', r'/legal', r'/disclaimer',
            r'facebook\.com', r'twitter\.com', r'linkedin\.com', r'instagram\.com',
            r'youtube\.com', r'github\.com/(?!.*\.(pdf|doc|docx|zip))', 
            r'mailto:', r'tel:', r'javascript:', r'#$'
        ]

    def _try_normalize_url(self, url: str) -> NormalizedUrl | None:
        try:
            return NormalizedUrl(url)
        except Exception:
            return None

    def _is_excluded_url(self, url: str) -> bool:
        for pattern in self.exclude_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False

    def _is_file_url(self, url: str) -> bool:
        parsed = urlparse(url.lower())
        path = parsed.path
        return any(path.endswith(ext) for ext in self.file_extensions)

    def _is_internal_url(self, url: str, base_url: NormalizedUrl) -> bool:
        parsed_url = urlparse(url)
        parsed_base = urlparse(str(base_url))
        
        # Relative URLs are internal
        if not parsed_url.netloc:
            return True
            
        # Same domain
        return parsed_url.netloc == parsed_base.netloc

    def extract_links_from_html(self, html_content: str, base_url: NormalizedUrl) -> tuple[List[NormalizedUrl], List[NormalizedUrl], List[NormalizedUrl]]:
        # Extract all href attributes from anchor tags
        href_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>'
        matches = re.findall(href_pattern, html_content, re.IGNORECASE)
        
        internal_links = []
        external_links = []
        file_links = []
        
        seen_urls = set()
        
        for match in matches:
            url = match.strip()
            
            # Skip empty URLs or fragments
            if not url or url == '#' or url.startswith('#'):
                continue
                
            # Skip excluded URLs
            if self._is_excluded_url(url):
                continue
            
            # Convert relative URLs to absolute
            if not url.startswith(('http://', 'https://')):
                url = urljoin(str(base_url), url)
            
            # Skip duplicates
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            # Try to normalize the URL
            normalized_url = self._try_normalize_url(url)
            if not normalized_url:
                continue
            
            # Categorize the URL
            if self._is_file_url(url):
                file_links.append(normalized_url)
            elif self._is_internal_url(url, base_url):
                internal_links.append(normalized_url)
            else:
                external_links.append(normalized_url)
        
        return internal_links, external_links, file_links