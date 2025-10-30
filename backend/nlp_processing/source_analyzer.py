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

        base_prompt = f"""Analyze the following combined summaries of pages from a website for a research campaign investigating the effects of Concentrated Animal Feeding Operations (CAFOs) in Washington state. We're conducting a literature review on environmental and community impacts of CAFOs.

Please provide a comprehensive analysis that includes:

1. Summary: Synthesize the main conclusions and findings across all pages, focusing on CAFO-related content, environmental impacts, community health effects, and agricultural practices.

2. Key Facts: Aggregate and synthesize the most important factual information from all pages. Combine related facts and identify patterns or trends relevant to CAFO research.

3. Key Quotes: Compile the most significant quotes from across all pages that support the research. Prioritize quotes from experts, officials, and researchers about impacts, policies, or industrial agriculture.

4. Key Figures: Aggregate important statistics and quantitative data from all pages. Look for patterns in the data and highlight the most significant numbers relevant to CAFO impacts.

5. Classification: Classify the source according to the following categories:

Data Origin options:
{data_origin_options}

Source Format options:
{source_format_options}

Focus Area options:
{focus_area_options}

Guidelines:
- Synthesize information rather than just listing individual page content
- Identify connections and patterns across the different pages
- Focus on content most relevant to understanding CAFO impacts
- Prioritize information that adds value to the literature review
- For aggregated fields, organize information logically and remove redundancy"""

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
