# Import the app from the api directory
from api.app import app

# This allows the app to be run with `uv run litestar run`
__all__ = ["app"]