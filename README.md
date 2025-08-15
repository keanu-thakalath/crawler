# Web Crawler & Content Analysis

## Technologies

**Frontend:**

- [**SolidJS** with **SolidStart**](https://docs.solidjs.com/solid-start/) - Reactive web framework
- **TypeScript** - Type-safe JavaScript

**Backend:**

- [**Litestar**](https://litestar.dev/) - Modern async Python web framework
- [**Celery**](https://docs.celeryq.dev/en/v5.5.3/getting-started/introduction.html) - Distributed task processing
- [**SQLAlchemy**](https://www.sqlalchemy.org/) - Type-safe database ORM
- [**LiteLLM**](https://docs.litellm.ai/docs/) - Unified LLM interface

**Infrastructure:**

- **RabbitMQ** - Message broker
- **SQLite** - Database
- **Crawlbase** - Web crawling service

## Core Tenets

### 1. Ethical Scraping

- **Respect robots.txt**: Honor website crawling policies and rate limits
- **Rate limiting**: Built-in delays and batch processing prevent overwhelming target servers
- **Identify yourself**: Use user agents to provide website administrators with a way to contact you

### 2. Ethical LLM Usage

- **Human-in-the-loop workflow**: All AI processing results must be presented to users for review and validation
- **Token usage tracking**: Full visibility into AI processing costs and resource consumption

### 3. Type Safety

- **End-to-end TypeScript**: Frontend uses full TypeScript with strict typing
- **Python type hints**: Backend leverages Python 3.12+ type annotations throughout
- **Database schema validation**: SQLAlchemy models with typed relationships and constraints

## Quick Start

1. **Backend**: Follow setup in `backend/README.md`
2. **Frontend**: Follow setup in `frontend/README.md`
3. **Access**: Open http://localhost:3000 to start crawling
