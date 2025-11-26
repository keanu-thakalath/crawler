import abc
from dataclasses import dataclass
from typing import List
from domain.types import NormalizedUrl
from domain.values import ExtractJobResultData, LLMResponseMetadata, Relevancy

from .structured_completion import LiteLLMStructuredCompletion


@dataclass
class SummaryResult:
    """Result type for LLM parsing with string URLs that will be converted to NormalizedUrls."""
    summary: str
    key_facts: str
    key_quotes: str
    key_figures: str
    trustworthiness: str
    relevancy: Relevancy
    relevant_internal_links: List[str]
    relevant_external_links: List[str]
    relevant_file_links: List[str]


class PageSummarizer(abc.ABC):
    @abc.abstractmethod
    async def summarize_page(
        self, 
        url: NormalizedUrl, 
        markdown: str, 
        scraped_internal_links: List[NormalizedUrl],
        scraped_external_links: List[NormalizedUrl], 
        scraped_file_links: List[NormalizedUrl],
        custom_prompt: str | None = None
    ) -> tuple[ExtractJobResultData, LLMResponseMetadata]:
        raise NotImplementedError


class LiteLLMPageSummarizer(PageSummarizer):
    def __init__(self, structured_completion: LiteLLMStructuredCompletion):
        self.structured_completion = structured_completion

    async def summarize_page(
        self, 
        url: NormalizedUrl, 
        markdown: str, 
        scraped_internal_links: List[NormalizedUrl],
        scraped_external_links: List[NormalizedUrl], 
        scraped_file_links: List[NormalizedUrl],
        custom_prompt: str | None = None
    ) -> tuple[ExtractJobResultData, LLMResponseMetadata]:
        base_prompt = """Analyze the following markdown content for a research campaign investigating the effects of Concentrated Animal Feeding Operations (CAFOs) in Washington state. We're conducting a literature review on environmental and community impacts of CAFOs.

Please extract and structure the following information:

1. Summary: Provide a concise summary focusing on conclusions and main findings, especially any related to CAFOs, environmental impacts, community health, agricultural practices, or animal welfare.

2. Key Facts: Extract important factual information, findings, or statements that are relevant to CAFO research. Include environmental data, health outcomes, regulatory information, or agricultural statistics.

3. Key Quotes: Identify and extract relevant direct quotes from experts, officials, researchers, or community members that support the research. Include quotes about impacts, policies, or significant statements about industrial agriculture.

4. Key Figures: Extract important statistics, numbers, percentages, measurements, or quantitative data points relevant to CAFO impacts. This could include pollution levels, livestock numbers, distances, monetary figures, health statistics, etc.

5. Trustworthiness: Analyze the credibility and reliability of this source. Consider:
   - Source type (peer-reviewed research, government report, news article, blog, etc.)
   - Author credentials and institutional affiliation
   - Methodology quality (if research study)
   - Publication venue reputation
   - Presence of citations and references
   - Potential bias or conflicts of interest
   - Date and currency of information
   Provide a brief analysis of these factors affecting trustworthiness.

6. Relevancy: Classify how relevant this content is to CAFO research using one of these categories:
   - "High": Directly discusses CAFOs, concentrated animal agriculture, factory farming, or their specific environmental/health impacts
   - "Medium": Discusses related topics like livestock agriculture, environmental pollution from agriculture, rural health impacts, or regulatory frameworks that could apply to CAFOs
   - "Low": Tangentially related to agriculture, environment, or rural communities but not specifically relevant to CAFO impacts
   - "Not Relevant": No meaningful connection to CAFO research topics
   Just output one of the categories, no explanation is necessary.

7. Relevant Internal Links: From the provided list of internal links (including PDF links to the same domain), select and rank the most relevant ones for CAFO research. Consider link text, URL structure, and context from the page content. Return up to 10 most relevant internal links, ordered by relevance (most relevant first). Return empty list if none are relevant.

8. Relevant External Links: From the provided list of external links (including PDF links to external domains), select and rank the most relevant ones for CAFO research. Look for links to research institutions, government agencies, environmental organizations, agricultural bodies, or academic sources. Return up to 10 most relevant external links, ordered by relevance (most relevant first). Return empty list if none are relevant.

9. Relevant File Links: From the provided list of file links (non-PDF documents like .doc, .xls, .csv, .zip data files), select and rank the most relevant ones for CAFO research. Prioritize data files, spreadsheets, and downloadable documents. Return up to 10 most relevant file links, ordered by relevance (most relevant first). Return empty list if none are relevant.

Guidelines:
- Focus on content relevant to industrial agriculture, environmental impacts, and community effects
- Prioritize information that would be valuable for understanding CAFO impacts in Washington or similar contexts
- If the content is not directly related to CAFOs, extract information that could be applicable to environmental or community impact assessment
- Keep extractions factual and preserve important context
- If no relevant information is found for a category, note "No relevant information found" for that field
- Be objective in trustworthiness assessment - note both strengths and limitations
- Base relevancy classification on content substance, not just keywords"""

        # Build links sections
        internal_links_text = "\n".join([f"- {link}" for link in scraped_internal_links]) if scraped_internal_links else "No internal links found"
        external_links_text = "\n".join([f"- {link}" for link in scraped_external_links]) if scraped_external_links else "No external links found"
        file_links_text = "\n".join([f"- {link}" for link in scraped_file_links]) if scraped_file_links else "No file links found"
        
        prompt_to_use = custom_prompt if custom_prompt else base_prompt
        full_prompt = f"""{prompt_to_use}

Internal links found on the page:
{internal_links_text}

External links found on the page:
{external_links_text}

File links found on the page:
{file_links_text}

Markdown content for URL {url}:
{markdown}"""

        raw_result, metadata = await self.structured_completion.complete(
            full_prompt, SummaryResult
        )
        
        # Create ExtractJobResultData with converted URLs
        extract_result = ExtractJobResultData(
            summary=raw_result.summary,
            key_facts=raw_result.key_facts,
            key_quotes=raw_result.key_quotes,
            key_figures=raw_result.key_figures,
            trustworthiness=raw_result.trustworthiness,
            relevancy=raw_result.relevancy,
            relevant_internal_links=NormalizedUrl.from_string_list(raw_result.relevant_internal_links),
            relevant_external_links=NormalizedUrl.from_string_list(raw_result.relevant_external_links),
            relevant_file_links=NormalizedUrl.from_string_list(raw_result.relevant_file_links)
        )
        
        # Override the stored prompt to exclude markdown content
        metadata = LLMResponseMetadata(
            input_tokens=metadata.input_tokens,
            output_tokens=metadata.output_tokens,
            prompt=prompt_to_use,
            model=metadata.model,
            review_status=metadata.review_status,
        )

        return extract_result, metadata