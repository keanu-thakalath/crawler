# Backend Setup

## Prerequisites

1. **Python** ≥3.12
2. [**RabbitMQ** server running locally](https://docs.astral.sh/uv/getting-started/installation/)
3. [**uv** package manager](https://docs.astral.sh/uv/getting-started/installation/)

## Setup

1. **Install dependencies:**

   ```bash
   cd backend
   uv sync
   ```

2. **Create `.env` file:**

   ```bash
   # Crawlbase API Configuration
   CRAWLBASE_TOKEN=your_crawlbase_token_here

   # LiteLLM / Anthropic API Configuration
   ANTHROPIC_API_KEY=your_anthropic_api_key_here

   # Celery Configuration
   CELERY_BROKER=local_rabbitmq_server
   CELERY_BACKEND=db+sqlite:///celery_results.db

   # Database Configuration
   DATABASE_URL=sqlite+aiosqlite:///crawler.sqlite

   # Auth configuration
   USER_TOKEN=your_token_here
   ```

   **Get API Keys:**

   - **Crawlbase**: Sign up at [crawlbase.com](https://crawlbase.com)
   - **Anthropic**: Sign up at [console.anthropic.com](https://console.anthropic.com)

3. **Start the application:**

   ```bash
   uv run litestar run --debug --reload
   ```

   ```bash
   uv run celery -A tasks worker --pool solo --loglevel=INFO
   ```

## After Running

- **API Documentation**: [http://localhost:8000/schema](http://localhost:8000/schema)
- **Backend API**: [http://localhost:8000](http://localhost:8000)

The start script will run both the Litestar web server and Celery worker. Press `Ctrl+C` to stop both services.
