"""
Database models for Cool Papers
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Float, Boolean, Index
from sqlalchemy.sql import func
from datetime import datetime
from database import Base


class Paper(Base):
    """Paper model for storing paper metadata"""
    __tablename__ = "papers"
    
    id = Column(String(100), primary_key=True, index=True)  # e.g., "2401.12345" or "abc123@OpenReview"
    source = Column(String(50), nullable=False, index=True)  # "arxiv", "openreview", "acl", etc.
    
    # Basic Info
    title = Column(Text, nullable=False)
    authors = Column(JSON, nullable=False)  # List of author names
    abstract = Column(Text)
    
    # URLs
    paper_url = Column(String(500))
    pdf_url = Column(String(500))
    
    # Dates
    published_date = Column(DateTime, index=True)
    updated_date = Column(DateTime)
    
    # Categories/Subjects
    categories = Column(JSON)  # List of categories (e.g., ["cs.AI", "cs.LG"])
    subjects = Column(JSON)  # For conferences
    
    # Venue (for conference papers)
    venue = Column(String(100), index=True)  # e.g., "ICML.2024"
    
    # Full text (extracted from PDF)
    full_text = Column(Text)
    
    # Statistics
    view_count = Column(Integer, default=0)
    pdf_click_count = Column(Integer, default=0)
    kimi_click_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Additional metadata
    metadata = Column(JSON)  # For storing extra fields
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_source_published', 'source', 'published_date'),
        Index('idx_venue', 'venue'),
    )


class UserActivity(Base):
    """Track user activity for recommendations"""
    __tablename__ = "user_activities"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), index=True)  # Can be session ID or user ID
    paper_id = Column(String(100), index=True)
    action = Column(String(50))  # "view", "pdf_click", "kimi_click", "star"
    timestamp = Column(DateTime, default=func.now(), index=True)
    
    __table_args__ = (
        Index('idx_user_paper', 'user_id', 'paper_id'),
    )


class CachedSummary(Base):
    """Cache for AI-generated summaries (Kimi, etc.)"""
    __tablename__ = "cached_summaries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(100), unique=True, index=True)
    summary_zh = Column(Text)  # Chinese summary
    summary_en = Column(Text)  # English summary
    faq = Column(JSON)  # Frequently asked questions
    generated_at = Column(DateTime, default=func.now())
    model = Column(String(50))  # Model used for generation


class SearchLog(Base):
    """Search query logs for analytics"""
    __tablename__ = "search_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(String(500), index=True)
    user_id = Column(String(100))
    result_count = Column(Integer)
    timestamp = Column(DateTime, default=func.now(), index=True)


class Feed(Base):
    """RSS/Atom feed generation metadata"""
    __tablename__ = "feeds"
    
    id = Column(String(100), primary_key=True)  # e.g., "arxiv.cs.AI"
    title = Column(String(200))
    description = Column(Text)
    link = Column(String(500))
    last_updated = Column(DateTime, default=func.now())
    paper_ids = Column(JSON)  # List of recent paper IDs
