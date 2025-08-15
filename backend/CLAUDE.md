# Crawler Demo - Development Guide

## System Overview

This is a web crawling, scraping, and content analysis system built with:

- **Backend**: Python with SQLAlchemy for database operations
- **Task Queue**: Celery for async job processing
- **API**: Litestar for REST endpoints
- **LLM Processing**: LiteLLM with Claude for content analysis
- **Database**: SQLite for data persistence

## Job Processing Pipeline

The system processes URLs through a multi-stage pipeline:

1. **CRAWL** → Discovers pages from a source URL
2. **SCRAPE** → Extracts HTML and converts to markdown
3. **EXTRACT** → Uses LLM to extract links and generate page summaries
4. **SUMMARIZE** → Analyzes all page summaries to classify the source

## Step-by-Step Guide: Adding New Fields to Jobs

When you need to add new fields or modify job processing, follow these steps:

### 1. Update Database Models (`database/models.py`)

- Add new fields to the relevant job model (e.g., `ExtractJob`, `ScrapeJob`, `SummarizeJob`)
- Use appropriate SQLAlchemy types (`Text` for long strings, `Integer` for numbers, etc.)
- Example:
  ```python
  class ExtractJob(Base):
      summary: Mapped[str] = mapped_column(Text)  # New field
  ```

### 2. Update LLM Processors (`llm_processor.py`)

- Modify the LLM prompt to request the new data
- Update the expected JSON structure in prompts
- Ensure error handling includes new fields with default values
- Example:
  ```python
  prompt = f"""Return JSON with this structure:
  {{
      "existing_field": "...",
      "new_field": "..."  // Add new field here
  }}"""
  ```

### 3. Update Job Processing Logic (`jobs/scraping.py`)

- Modify the job creation to store new field values
- Update database queries if needed (e.g., changing from scrape to extract results)
- Example:
  ```python
  extract_result = ExtractJob(
      page_job_id=extract_job.id,
      summary=structured_data.get("summary", "")  # Store new field
  )
  ```

### 4. Update API Response Models (`api/models.py`)

- Add new fields to the corresponding response dataclass
- Example:
  ```python
  @dataclass
  class ExtractJobResponse:
      summary: str  # New field
  ```

### 5. Update API Endpoints (`api/app.py`)

- Modify the endpoint to return the new field in the response
- Example:
  ```python
  return ExtractJobResponse(
      id=extract_job.id,
      summary=extract_job.summary,  # Include new field
  )
  ```

## Key Files and Their Purposes

- **`database/models.py`**: SQLAlchemy ORM models for all entities
- **`jobs/scraping.py`**: Core job processing logic (scrape, extract, summarize)
- **`llm_processor.py`**: LLM integration for content analysis
- **`api/models.py`**: Pydantic/dataclass models for API responses
- **`api/app.py`**: Litestar API endpoints
- **`tasks/`**: Celery task definitions
- **`celery_config.py`**: Celery configuration

## Common Development Patterns

### Adding New Job Types

1. Add enum value to `JobType` in `database/models.py`
2. Create new job result model if needed
3. Add processing function to `jobs/scraping.py`
4. Create API endpoint for retrieving results
5. Add corresponding response model

### Modifying LLM Processing

1. Update prompts in `llm_processor.py`
2. Test with sample content to ensure JSON parsing works
3. Update error handling to include new fields
4. Consider prompt length limits and token costs

### Database Schema Changes

1. Update models in `database/models.py`
2. The system uses `create_all=True` so new tables/columns are auto-created
3. For production, consider proper migrations

## Testing Commands

Run these commands to test the system:

```bash
# Start Celery worker
celery -A tasks.crawl_tasks worker --loglevel=info

# Start API server
uvicorn api.app:app --reload

# Reset database (development only)
curl -X DELETE http://localhost:8000/reset

# Queue a crawl job
curl -X POST http://localhost:8000/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

## Debugging Tips

- Check Celery logs for job processing errors
- Use database browser to inspect job statuses and results
- API provides `/sources/jobs` and `/pages/jobs` endpoints for monitoring
- Individual job results available at `/jobs/{type}/{job_id}`

## Recent Changes

- **Extract Job Enhancement**: Added `summary` field to capture page-level summaries
- **Source Analysis Optimization**: Modified to use page summaries instead of full markdown for better performance
- **LLM Prompt Updates**: Enhanced prompts to generate both link extraction and content summaries
