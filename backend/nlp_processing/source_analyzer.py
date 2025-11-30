import abc
from dataclasses import dataclass, field

from typing import List
from domain.types import NormalizedUrl
from domain.values import (
    DataOrigin,
    DatasetPresence,
    FocusArea,
    LLMResponseMetadata,
    SourceFormat,
    SummarizeJobResultData,
)

from .structured_completion import LiteLLMStructuredCompletion


@dataclass
class SourceAnalysisResult:
    """Result type for LLM parsing with string URLs that will be converted to NormalizedUrls."""
    summary: str
    key_facts: str
    key_quotes: str
    key_figures: str
    data_origin: DataOrigin
    source_format: SourceFormat
    focus_area: FocusArea
    dataset_presence: DatasetPresence
    relevant_external_links: List[str] = field(default_factory=list)


class SourceAnalyzer(abc.ABC):
    @abc.abstractmethod
    async def analyze_content(
        self, 
        all_markdown: str, 
        source_url: str, 
        external_links: List[NormalizedUrl],
        custom_prompt: str | None = None
    ) -> tuple[SummarizeJobResultData, LLMResponseMetadata]:
        raise NotImplementedError


class LiteLLMSourceAnalyzer(SourceAnalyzer):
    def __init__(self, structured_completion: LiteLLMStructuredCompletion):
        self.structured_completion = structured_completion

    async def analyze_content(
        self, 
        all_markdown: str, 
        source_url: str, 
        external_links: List[NormalizedUrl],
        custom_prompt: str | None = None
    ) -> tuple[SummarizeJobResultData, LLMResponseMetadata]:
        data_origin_options = "\n".join(
            [f'- "{option.value}"' for option in DataOrigin]
        )
        source_format_options = "\n".join(
            [f'- "{option.value}"' for option in SourceFormat]
        )
        focus_area_options = "\n".join([f'- "{option.value}"' for option in FocusArea])
        dataset_presence_options = "\n".join([f'- "{option.value}"' for option in DatasetPresence])

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

Dataset Presence options:
{dataset_presence_options}

6. Dataset Presence: Determine whether the source contains or references any datasets, data files, or raw data that could be useful for research analysis.

7. Relevant External Links: From the provided list of all external links discovered across all pages of this source, filter and select only the most relevant ones for CAFO research. Consider:
   - Links to research institutions, government agencies, environmental organizations
   - Academic sources, peer-reviewed research, or regulatory documents
   - Organizations focused on agriculture, environmental protection, or public health
   - Data repositories, additional research sources, or policy documents
   Return up to 5 most relevant external links, prioritizing quality and research value over quantity. Return empty list if no links appear relevant to CAFO research.

Guidelines:
- Synthesize information rather than just listing individual page content
- Identify connections and patterns across the different pages
- Focus on content most relevant to understanding CAFO impacts
- Prioritize information that adds value to the literature review
- For aggregated fields, organize information logically and remove redundancy
- For external links, prioritize authoritative, academic, and governmental sources over commercial or promotional content"""

        # Build external links section
        external_links_text = "\n".join([f"- {link}" for link in external_links]) if external_links else "No external links found"
        
        prompt_to_use = custom_prompt if custom_prompt else base_prompt
        full_prompt = f"""{prompt_to_use}

Source URL: {source_url}

All external links discovered across pages:
{external_links_text}

Combined summaries of all pages:
{all_markdown}"""

        raw_result, metadata = await self.structured_completion.complete(full_prompt, SourceAnalysisResult)
        
        # Create SummarizeJobResultData with converted URLs
        summarize_result = SummarizeJobResultData(
            summary=raw_result.summary,
            key_facts=raw_result.key_facts,
            key_quotes=raw_result.key_quotes,
            key_figures=raw_result.key_figures,
            data_origin=raw_result.data_origin,
            source_format=raw_result.source_format,
            focus_area=raw_result.focus_area,
            dataset_presence=raw_result.dataset_presence,
            relevant_external_links=NormalizedUrl.from_string_list(raw_result.relevant_external_links)
        )
        
        # Override the stored prompt to exclude content being analyzed
        metadata = LLMResponseMetadata(
            input_tokens=metadata.input_tokens,
            output_tokens=metadata.output_tokens,
            prompt=prompt_to_use,
            model=metadata.model,
            review_status=metadata.review_status,
        )
        
        return summarize_result, metadata
