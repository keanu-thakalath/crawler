"""
REPL Helper for Database Exploration (Sync Version)

Usage:
    >>> from repl_helper import *
    >>> session = get_session()
    >>> # Now you can query the database
    >>> result = session.execute(select(Job))
    >>> jobs = result.scalars().all()

Available imports:
- All domain models (Job, Page, Source, etc.)
- All job result types (ScrapeJobResult, ExtractJobResult, etc.)
- SQLAlchemy core (select, update, delete, etc.)
- Session factory function get_session()
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, select, update, delete, insert, and_, or_, text
from sqlalchemy.orm import sessionmaker, Session, selectinload, joinedload

# Database setup
from database.models import Models

# Domain models
from domain.entities import (
    Job, Page, Source, 
    ScrapeJob, ExtractJob, SummarizeJob, CrawlJob,
    PageJob, SourceJob
)

# Value objects and results
from domain.values import (
    JobError,
    ScrapeJobResult,
    ExtractJobResult, 
    SummarizeJobResult,
    CrawlJobResult,
    LLMResponseMetadata,
    DataOrigin,
    SourceFormat,
    FocusArea,
    ReviewStatus
)

from domain.types import NormalizedUrl

# Load environment
load_dotenv()

# Global session factory
_session_factory = None
_engine = None

def setup():
    """Initialize the database connection"""
    global _session_factory, _engine
    if _session_factory is None:
        # Convert async URL to sync if needed
        database_url = os.getenv("DATABASE_URL")
        print(f"Original DATABASE_URL: {database_url}")
        
        if database_url:
            # Handle different async database URLs
            if database_url.startswith("postgresql+asyncpg://"):
                database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
            elif database_url.startswith("sqlite+aiosqlite://"):
                database_url = database_url.replace("sqlite+aiosqlite://", "sqlite://")
            elif "aiosqlite" in database_url:
                # Handle other aiosqlite variations
                database_url = database_url.replace("+aiosqlite", "")
        
        print(f"Converted DATABASE_URL: {database_url}")
        _engine = create_engine(database_url)
        Models.start_mappers()
        _session_factory = sessionmaker(_engine, expire_on_commit=False)
    return _session_factory, _engine

def get_session() -> Session:
    """Get a database session for querying"""
    session_factory, _ = setup()
    return session_factory()

def close_engine():
    """Close the database engine"""
    global _engine
    if _engine:
        _engine.dispose()

# Convenience functions
def query_jobs(limit: int = 10):
    """Quick query to get recent jobs"""
    session = get_session()
    try:
        result = session.execute(
            select(Job).order_by(Job.created_at.desc()).limit(limit)
        )
        return result.scalars().all()
    finally:
        session.close()

def query_pages(limit: int = 10):
    """Quick query to get pages"""
    session = get_session()
    try:
        result = session.execute(select(Page).limit(limit))
        return result.scalars().all()
    finally:
        session.close()

def query_sources(limit: int = 10):
    """Quick query to get sources"""
    session = get_session()
    try:
        result = session.execute(select(Source).limit(limit))
        return result.scalars().all()
    finally:
        session.close()

def query_extract_results(limit: int = 10):
    """Quick query to get extract job results"""
    session = get_session()
    try:
        result = session.execute(
            select(ExtractJobResult).order_by(ExtractJobResult.created_at.desc()).limit(limit)
        )
        return result.scalars().all()
    finally:
        session.close()

def query_scrape_results(limit: int = 10):
    """Quick query to get scrape job results"""
    session = get_session()
    try:
        result = session.execute(
            select(ScrapeJobResult).order_by(ScrapeJobResult.created_at.desc()).limit(limit)
        )
        return result.scalars().all()
    finally:
        session.close()

def example_usage():
    """Show example database queries"""
    print("=== REPL Helper Examples ===")
    
    # Get a session
    session = get_session()
    
    try:
        # Count jobs
        result = session.execute(select(Job))
        jobs = result.scalars().all()
        print(f"Total jobs: {len(jobs)}")
        
        # Count extract results
        result = session.execute(select(ExtractJobResult))
        extract_results = result.scalars().all()
        print(f"Extract job results: {len(extract_results)}")
        
        # Show recent extract results with key data
        if extract_results:
            recent_extract = extract_results[-1]
            print("\nMost recent extract result:")
            print(f"  Summary: {recent_extract.summary[:100]}...")
            print(f"  Key facts: {recent_extract.key_facts[:100]}...")
            print(f"  Model: {recent_extract.model}")
            print(f"  Tokens: {recent_extract.input_tokens}/{recent_extract.output_tokens}")
    
    finally:
        session.close()

# Auto-setup when imported
setup()

print("REPL Helper loaded! Use 'get_session()' to start querying.")
print("Quick functions: query_jobs(), query_pages(), query_sources(), query_extract_results()")
print("Run 'example_usage()' to see examples.")