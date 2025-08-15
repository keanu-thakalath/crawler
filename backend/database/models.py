from typing import List, Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Integer, Text
from enum import Enum

class Base(DeclarativeBase):
    pass

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"

class JobType(Enum):
    CRAWL = "crawl"
    SCRAPE = "scrape"
    EXTRACT = "extract"
    SUMMARIZE = "summarize"

# Core entities - no optional fields
class Source(Base):
    __tablename__ = "sources"
    
    url: Mapped[str] = mapped_column(unique=True, primary_key=True)
    pages: Mapped[List["Page"]] = relationship(back_populates="source", lazy="joined")
    
    # Job relationships
    source_jobs: Mapped[List["SourceJob"]] = relationship(back_populates="source")

class Page(Base):
    __tablename__ = "pages"

    url: Mapped[str] = mapped_column(unique=True, primary_key=True)
    source_url: Mapped[str] = mapped_column(ForeignKey("sources.url"))
    source: Mapped["Source"] = relationship(back_populates="pages")
    
    # Job relationships
    page_jobs: Mapped[List["PageJob"]] = relationship(back_populates="page")

# Central job tracking tables
class PageJob(Base):
    __tablename__ = "page_jobs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    page_url: Mapped[int] = mapped_column(ForeignKey("pages.url"))
    job_type: Mapped[JobType] = mapped_column()
    status: Mapped[JobStatus] = mapped_column(default=JobStatus.PENDING)
    
    # Relationships
    page: Mapped["Page"] = relationship(back_populates="page_jobs")
    scrape_jobs: Mapped[List["ScrapeJob"]] = relationship(back_populates="page_job")
    extract_jobs: Mapped[List["ExtractJob"]] = relationship(back_populates="page_job")

class SourceJob(Base):
    __tablename__ = "source_jobs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_url: Mapped[str] = mapped_column(ForeignKey("sources.url"))
    job_type: Mapped[JobType] = mapped_column()
    status: Mapped[JobStatus] = mapped_column(default=JobStatus.PENDING)
    
    # Relationships
    source: Mapped["Source"] = relationship(back_populates="source_jobs")
    summarize_jobs: Mapped[List["SummarizeJob"]] = relationship(back_populates="source_job")

# Job result tables - complete objects with all required fields
class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    page_job_id: Mapped[int] = mapped_column(ForeignKey("page_jobs.id"))
    markdown: Mapped[str] = mapped_column(Text)
    html: Mapped[str] = mapped_column(Text)
    
    # Relationships
    page_job: Mapped["PageJob"] = relationship(back_populates="scrape_jobs")

class ExtractJob(Base):
    __tablename__ = "extract_jobs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True) 
    page_job_id: Mapped[int] = mapped_column(ForeignKey("page_jobs.id"))
    summary: Mapped[str] = mapped_column(Text)
    input_tokens: Mapped[int] = mapped_column(Integer)
    output_tokens: Mapped[int] = mapped_column(Integer)
    
    # Relationships
    page_job: Mapped["PageJob"] = relationship(back_populates="extract_jobs")
    files: Mapped[List["File"]] = relationship(back_populates="extract_job")

class SummarizeJob(Base):
    __tablename__ = "summarize_jobs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_job_id: Mapped[int] = mapped_column(ForeignKey("source_jobs.id"))
    summary: Mapped[str] = mapped_column(Text)
    data_origin: Mapped[str] = mapped_column()
    source_format: Mapped[str] = mapped_column()
    focus_area: Mapped[str] = mapped_column()
    input_tokens: Mapped[int] = mapped_column(Integer)
    output_tokens: Mapped[int] = mapped_column(Integer)
    
    # Relationships
    source_job: Mapped["SourceJob"] = relationship(back_populates="summarize_jobs")

class File(Base):
    __tablename__ = "files"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column()
    extract_job_id: Mapped[int] = mapped_column(ForeignKey("extract_jobs.id"))
    extract_job: Mapped["ExtractJob"] = relationship(back_populates="files")