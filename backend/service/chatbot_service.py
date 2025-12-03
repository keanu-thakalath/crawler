from typing import List, Tuple
from domain.values import ExtractJobResult, SummarizeJobResult
from nlp_processing.function_registry import FunctionProvider
from service.unit_of_work import UnitOfWork


class ChatbotService(FunctionProvider):
    """Service layer implementation for chatbot function calls."""
    
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
    
    async def list_crawled_sources(self) -> List[Tuple[str, str, str, str, str, str]]:
        """
        List crawled sources with metadata.
        Returns: List[(source_url, summary, data_origin, source_format, focus_area, dataset_presence)]
        """
        # Get sources that have completed summarize jobs
        sources = await self.uow.sources.get_crawled_sources()
        
        result = []
        for source in sources:
            # Find the completed summarize job for this source
            summarize_job = None
            for job in source.jobs:
                if isinstance(job.outcome, SummarizeJobResult):
                    summarize_job = job.outcome
                    break
            
            if summarize_job:
                result.append((
                    str(source.url),
                    summarize_job.summary,
                    summarize_job.data_origin.value,
                    summarize_job.source_format.value,
                    summarize_job.focus_area.value,
                    summarize_job.dataset_presence.value
                ))
        
        return result
    
    async def read_sources(self, source_urls: List[str]) -> List[Tuple[str, str, str, str]]:
        """
        Read detailed information from specified sources.
        Returns: List[(source_url, key_facts, key_quotes, key_figures)]
        """
        result = []
        
        for source_url in source_urls:
            try:
                source = await self.uow.sources.get(source_url)
                if not source:
                    # Source not found, add error entry
                    result.append((
                        source_url,
                        "Error: Source not found",
                        "Error: Source not found",
                        "Error: Source not found"
                    ))
                    continue
                
                # Collect information from both source-level and page-level jobs
                all_key_facts = []
                all_key_quotes = []
                all_key_figures = []
                
                # Check source-level summarize job
                for job in source.jobs:
                    if isinstance(job.outcome, SummarizeJobResult):
                        if job.outcome.key_facts.strip():
                            all_key_facts.append(f"Source Summary:\n{job.outcome.key_facts}")
                        if job.outcome.key_quotes.strip():
                            all_key_quotes.append(f"Source Summary:\n{job.outcome.key_quotes}")
                        if job.outcome.key_figures.strip():
                            all_key_figures.append(f"Source Summary:\n{job.outcome.key_figures}")
                
                # Check page-level extract jobs
                for page in source.pages:
                    for job in page.jobs:
                        if isinstance(job.outcome, ExtractJobResult):
                            page_url_display = str(page.url)
                            if job.outcome.key_facts.strip():
                                all_key_facts.append(f"Page ({page_url_display}):\n{job.outcome.key_facts}")
                            if job.outcome.key_quotes.strip():
                                all_key_quotes.append(f"Page ({page_url_display}):\n{job.outcome.key_quotes}")
                            if job.outcome.key_figures.strip():
                                all_key_figures.append(f"Page ({page_url_display}):\n{job.outcome.key_figures}")
                
                # Combine all information
                combined_key_facts = "\n\n".join(all_key_facts) if all_key_facts else "No key facts found"
                combined_key_quotes = "\n\n".join(all_key_quotes) if all_key_quotes else "No key quotes found"
                combined_key_figures = "\n\n".join(all_key_figures) if all_key_figures else "No key figures found"
                
                result.append((
                    source_url,
                    combined_key_facts,
                    combined_key_quotes,
                    combined_key_figures
                ))
                
            except Exception as e:
                # Handle any errors gracefully
                result.append((
                    source_url,
                    f"Error retrieving source: {str(e)}",
                    f"Error retrieving source: {str(e)}",
                    f"Error retrieving source: {str(e)}"
                ))
        
        return result