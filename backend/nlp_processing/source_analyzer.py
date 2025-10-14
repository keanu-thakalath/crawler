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
        self, all_markdown: str, source_url: str, custom_prompt: str | None = None
    ) -> tuple[SummarizeJobResultData, LLMResponseMetadata]:
        raise NotImplementedError


class LiteLLMSourceAnalyzer(SourceAnalyzer):
    def __init__(self, structured_completion: LiteLLMStructuredCompletion):
        self.structured_completion = structured_completion

    async def analyze_content(
        self, all_markdown: str, source_url: str, custom_prompt: str | None = None
    ) -> tuple[SummarizeJobResultData, LLMResponseMetadata]:
        data_origin_options = "\n".join(
            [f'- "{option.value}"' for option in DataOrigin]
        )
        source_format_options = "\n".join(
            [f'- "{option.value}"' for option in SourceFormat]
        )
        focus_area_options = "\n".join([f'- "{option.value}"' for option in FocusArea])

        base_prompt = f"""Analyze the following combined summaries of pages from a website and provide a structured analysis.

Guidelines for classification:

Data Origin options:
{data_origin_options}

Source Format options:
{source_format_options}

Focus Area options:
{focus_area_options}"""

        prompt_to_use = custom_prompt if custom_prompt else base_prompt
        full_prompt = f"{prompt_to_use}\n\nSource URL: {source_url}\n\nCombined summaries of all pages:\n{all_markdown}"

        raw_result, metadata = await self.structured_completion.complete(full_prompt, SummarizeJobResultData)
        
        # Override the stored prompt to exclude content being analyzed
        metadata = LLMResponseMetadata(
            input_tokens=metadata.input_tokens,
            output_tokens=metadata.output_tokens,
            prompt=prompt_to_use,
            review_status=metadata.review_status,
        )
        
        return raw_result, metadata
