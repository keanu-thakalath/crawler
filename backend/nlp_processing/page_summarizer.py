import abc
from dataclasses import dataclass

from domain.types import NormalizedUrl
from domain.values import LLMResponseMetadata, Relevancy

from .structured_completion import LiteLLMStructuredCompletion


@dataclass
class SummaryResult:
    summary: str
    key_facts: str
    key_quotes: str
    key_figures: str
    trustworthiness: str
    relevancy: Relevancy


class PageSummarizer(abc.ABC):
    @abc.abstractmethod
    async def summarize_page(
        self, url: NormalizedUrl, markdown: str, custom_prompt: str | None = None
    ) -> tuple[SummaryResult, LLMResponseMetadata]:
        raise NotImplementedError


class LiteLLMPageSummarizer(PageSummarizer):
    def __init__(self, structured_completion: LiteLLMStructuredCompletion):
        self.structured_completion = structured_completion

    async def summarize_page(
        self, url: NormalizedUrl, markdown: str, custom_prompt: str | None = None
    ) -> tuple[SummaryResult, LLMResponseMetadata]:
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

Guidelines:
- Focus on content relevant to industrial agriculture, environmental impacts, and community effects
- Prioritize information that would be valuable for understanding CAFO impacts in Washington or similar contexts
- If the content is not directly related to CAFOs, extract information that could be applicable to environmental or community impact assessment
- Keep extractions factual and preserve important context
- If no relevant information is found for a category, note "No relevant information found" for that field
- Be objective in trustworthiness assessment - note both strengths and limitations
- Base relevancy classification on content substance, not just keywords"""

        prompt_to_use = custom_prompt if custom_prompt else base_prompt
        full_prompt = f"{prompt_to_use}\n\nMarkdown content for URL {url}:\n{markdown}"

        raw_result, metadata = await self.structured_completion.complete(
            full_prompt, SummaryResult
        )
        
        # Override the stored prompt to exclude markdown content
        metadata = LLMResponseMetadata(
            input_tokens=metadata.input_tokens,
            output_tokens=metadata.output_tokens,
            prompt=prompt_to_use,
            model=metadata.model,
            review_status=metadata.review_status,
        )

        return raw_result, metadata