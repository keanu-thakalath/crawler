import abc

from domain.values import (
    DataOrigin,
    FocusArea,
    LLMResponseMetadata,
    SourceFormat,
    SummarizeJobResultData,
)

from .structured_completion import LiteLLMStructuredCompletion


class SourceAnalyzer(abc.ABC):
    @abc.abstractmethod
    async def analyze_content(
        self, all_markdown: str, source_url: str
    ) -> tuple[SummarizeJobResultData, LLMResponseMetadata]:
        raise NotImplementedError


class LiteLLMSourceAnalyzer(SourceAnalyzer):
    def __init__(self, structured_completion: LiteLLMStructuredCompletion):
        self.structured_completion = structured_completion

    async def analyze_content(
        self, all_markdown: str, source_url: str
    ) -> tuple[SummarizeJobResultData, LLMResponseMetadata]:
        data_origin_options = "\n".join(
            [f'- "{option.value}"' for option in DataOrigin]
        )
        source_format_options = "\n".join(
            [f'- "{option.value}"' for option in SourceFormat]
        )
        focus_area_options = "\n".join([f'- "{option.value}"' for option in FocusArea])

        prompt = f"""
Analyze the following combined summaries of pages from a website and provide a structured analysis.

Guidelines for classification:

Data Origin options:
{data_origin_options}

Source Format options:
{source_format_options}

Focus Area options:
{focus_area_options}

Source URL: {source_url}

Combined summaries of all pages:
{all_markdown}
"""

        return await self.structured_completion.complete(prompt, SummarizeJobResultData)
