import abc

from domain.values import LLMResponseMetadata, SummarizeJobResultData

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
        prompt = f"""
Analyze the following combined summaries of pages from a website and provide a structured analysis.

Guidelines for classification:

Data Origin examples:
- "Academic Institution" - Universities, research institutions
- "Government Agency" - Federal, state, local government sites
- "Commercial Organization" - Companies, businesses
- "Non-profit Organization" - NGOs, foundations, charities
- "News/Media Outlet" - News sites, journalism platforms
- "Personal/Individual" - Personal blogs, portfolios
- "Community/Forum" - Discussion forums, community sites

Source Format examples:
- "Documentation Site" - Technical docs, API references, manuals
- "Blog/Article Site" - News articles, blog posts, editorial content
- "E-commerce Platform" - Online stores, marketplaces
- "Educational Content" - Courses, tutorials, learning materials
- "Reference/Database" - Catalogs, directories, reference materials
- "Portfolio/Showcase" - Personal or company portfolios
- "Community Platform" - Forums, social platforms, discussion boards

Focus Area examples:
- "Technology/Software" - Programming, tech products, software
- "Healthcare/Medical" - Medical information, healthcare services
- "Education/Learning" - Educational content, courses, training
- "Business/Finance" - Business information, financial services
- "Science/Research" - Scientific publications, research data
- "Arts/Entertainment" - Creative content, entertainment, media
- "Government/Public" - Public services, government information

Source URL: {source_url}

Combined summaries of all pages:
{all_markdown}
"""

        return await self.structured_completion.complete(prompt, SummarizeJobResultData)
