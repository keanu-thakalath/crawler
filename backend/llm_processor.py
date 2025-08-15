from litellm import completion
from dotenv import load_dotenv
from celery.utils.log import get_task_logger
from typing import Dict
import json
from urllib.parse import urlparse, urljoin

load_dotenv()
logger = get_task_logger(__name__)


def extract_page_links(markdown: str, source_url: str) -> Dict:
    """
    Extract links from markdown content and generate a summary using LiteLLM.
    
    Args:
        markdown: The markdown content to process
        source_url: The source URL to determine internal vs external links
        
    Returns:
        Dictionary containing relevant internal, external, file links, and a content summary
    """
    try:
        prompt = f"""
Analyze the following markdown content and extract relevant links, plus provide a summary. Return a JSON object with this structure:

{{
    "internal_links": ["list of internal/relative links that are relevant"],
    "external_links": ["list of external links that are relevant"],
    "file_links": ["list of links that appear to be files (PDFs, docs, images, etc.)"],
    "summary": "A concise 1-2 sentence summary of the main content and purpose of this page"
}}

Guidelines:
- Only include links that are relevant to the content (no login pages, social media, contact forms, privacy policies, terms of service)
- Internal links are relative URLs or URLs that belong to the same domain
- External links are URLs to different domains that provide valuable content
- File links are URLs that point to downloadable files like PDFs, Word docs, Excel files, images, etc.
- Look for links with file extensions like .pdf, .doc, .docx, .xls, .xlsx, .ppt, .pptx, .zip, .png, .jpg, .jpeg, .gif, .svg, etc.
- Exclude navigation, footer, and header links unless they're content-relevant
- Focus on links to articles, resources, documentation, or related content

Markdown content:
{markdown}
"""

        llm_response = completion(
            model="anthropic/claude-3-5-sonnet-20241022",
            messages=[
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
        )
        
        response_content = llm_response.choices[0].message.content
        
        # Extract JSON from response (handle cases where LLM adds extra text)
        start_idx = response_content.find('{')
        end_idx = response_content.rfind('}') + 1
        
        if (start_idx == -1 or end_idx == 0):
            raise Exception('Could not parse JSON object from LLM response')
        
        json_str = response_content[start_idx:end_idx]
        structured_data = json.loads(json_str)
        structured_data = _categorize_links_by_domain(structured_data, source_url)
        
        # Add token usage data
        structured_data["input_tokens"] = llm_response.usage.prompt_tokens
        structured_data["output_tokens"] = llm_response.usage.completion_tokens
        
        return structured_data
        
    except Exception as e:
        logger.error(f'Error extracting structured data from {source_url}: {e}')
        return {"internal_links": [], "external_links": [], "file_links": [], "summary": "", "input_tokens": 0, "output_tokens": 0}


def _categorize_links_by_domain(structured_data: Dict, source_url: str) -> Dict:
    """Helper function to properly categorize links based on domain and format URLs."""
    try:
        source_domain = urlparse(source_url).netloc
        parsed_base = urlparse(source_url)
        domain_only_base = f"{parsed_base.scheme}://{parsed_base.netloc}/"
        
        all_links = structured_data.get("internal_links", []) + structured_data.get("external_links", [])
        file_links = structured_data.get("file_links", [])
        
        internal_links = []
        external_links = []
        formatted_file_links = []
        
        # Process regular links
        for link in all_links:
            # Convert relative URLs to absolute URLs
            if not link.startswith(('http://', 'https://')):
                link = urljoin(domain_only_base, link)
            
            if source_domain in link:
                # Same domain links are internal
                internal_links.append(link)
            else:
                # Different domain links are external
                external_links.append(link)
        
        # Process file links and format them
        for file_link in file_links:
            # Convert relative URLs to absolute URLs
            if not file_link.startswith(('http://', 'https://')):
                file_link = urljoin(domain_only_base, file_link)
            formatted_file_links.append(file_link)
        
        return {
            "internal_links": list(set(internal_links)),
            "external_links": list(set(external_links)),
            "file_links": list(set(formatted_file_links)),
            "summary": structured_data.get("summary", ""),
            "input_tokens": structured_data.get("input_tokens", 0),
            "output_tokens": structured_data.get("output_tokens", 0)
        }
    except Exception:
        # If parsing fails, return original data
        return structured_data


def analyze_source_content(all_markdown: str, source_url: str) -> Dict:
    """
    Analyze the complete content of a source to extract summary and classification.
    
    Args:
        all_markdown: Concatenated markdown content from all pages in the source
        source_url: The source URL being analyzed
        
    Returns:
        Dictionary containing summary, data_origin, source_format, and focus_area
    """
    try:
        prompt = f"""
Analyze the following combined summaries of pages from a website and provide a structured analysis. Return a JSON object with this structure:

{{
    "summary": "A comprehensive 2-3 sentence summary of the main content and purpose",
    "data_origin": "Classification of the source origin",
    "source_format": "Classification of the content format",
    "focus_area": "Classification of the main focus area"
}}

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

        llm_response = completion(
            model="anthropic/claude-3-5-sonnet-20241022",
            messages=[
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
        )
        
        response_content = llm_response.choices[0].message.content
        
        # Extract JSON from response
        start_idx = response_content.find('{')
        end_idx = response_content.rfind('}') + 1
        
        if start_idx != -1 and end_idx != 0:
            json_str = response_content[start_idx:end_idx]
            analysis_data = json.loads(json_str)
            # Add token usage data
            analysis_data["input_tokens"] = llm_response.usage.prompt_tokens
            analysis_data["output_tokens"] = llm_response.usage.completion_tokens
        else:
            analysis_data = {
                "summary": "Unable to analyze content",
                "data_origin": "Unknown",
                "source_format": "Unknown", 
                "focus_area": "Unknown",
                "input_tokens": 0,
                "output_tokens": 0
            }
            
        return analysis_data
        
    except Exception as e:
        error_msg = f'Error analyzing source content from {source_url}: {e}'
        logger.error(error_msg)
        return {
            "summary": "Error occurred during analysis",
            "data_origin": "Unknown",
            "source_format": "Unknown",
            "focus_area": "Unknown",
            "input_tokens": 0,
            "output_tokens": 0
        }