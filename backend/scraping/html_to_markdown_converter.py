import abc

from markdownify import markdownify as md


class HtmlToMarkdownConverter(abc.ABC):
    @abc.abstractmethod
    def convert_to_markdown(self, html: str) -> str:
        raise NotImplementedError


class MarkdownifyConverter(HtmlToMarkdownConverter):
    def convert_to_markdown(self, html: str) -> str:
        return md(html)
