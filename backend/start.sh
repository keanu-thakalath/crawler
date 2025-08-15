#!/bin/bash

# Start the web crawler demo application and celery worker with visible output

# Function to handle cleanup when script is interrupted
cleanup() {
    echo -e "\n\nShutting down services..."
    kill $CELERY_PID 2>/dev/null
    kill $LITESTAR_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo "Starting services with visible output..."
echo "Press Ctrl+C to stop both services."
echo "======================================"

# Start Celery worker with prefix for its output
(uv run celery -A tasks.crawl_tasks worker --pool solo --loglevel=INFO 2>&1 | sed 's/^/[CELERY] /') &
CELERY_PID=$!

# Start Litestar with prefix for its output  
(uv run litestar run --debug --reload 2>&1 | sed 's/^/[LITESTAR] /') &
LITESTAR_PID=$!

echo "Celery PID: $CELERY_PID"
echo "Litestar PID: $LITESTAR_PID"
echo "======================================"

# Wait for both processes
wait