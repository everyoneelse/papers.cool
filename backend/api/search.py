"""
API routes for search operations
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from database import get_db
from models import SearchLog
from utils.search_engine import SearchEngine
from scrapers import ArxivScraper

router = APIRouter(prefix="/search", tags=["search"])

search_engine = SearchEngine()
arxiv_scraper = ArxivScraper()


@router.get("/")
async def search_papers(
    query: str = Query(..., description="Search query"),
    max_results: int = Query(100, le=1000),
    venue: Optional[str] = None,
    categories: Optional[str] = None,
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Full-text search across all papers
    
    Args:
        query: Search query string
        max_results: Maximum results to return
        venue: Filter by venue
        categories: Filter by categories (comma-separated)
        user_id: User ID for logging
    """
    # Parse categories
    category_list = None
    if categories:
        category_list = [c.strip() for c in categories.split(',')]
    
    # Perform search
    results = search_engine.search(
        query,
        max_results=max_results,
        filter_venue=venue,
        filter_categories=category_list
    )
    
    # Log search
    if user_id:
        log = SearchLog(
            query=query,
            user_id=user_id,
            result_count=len(results)
        )
        db.add(log)
        await db.commit()
    
    return {
        "query": query,
        "count": len(results),
        "results": results
    }


@router.get("/arxiv")
async def search_arxiv(
    query: str = Query(..., description="Search query"),
    max_results: int = Query(100, le=1000)
):
    """
    Search ArXiv papers using ArXiv API
    
    This provides an alternative to local search by directly querying ArXiv
    """
    papers = await arxiv_scraper.search_papers(query, max_results)
    
    return {
        "query": query,
        "count": len(papers),
        "results": papers
    }


@router.get("/suggestions")
async def get_search_suggestions(
    query: str = Query(..., description="Partial query"),
    limit: int = Query(10, le=20),
    db: AsyncSession = Depends(get_db)
):
    """Get search suggestions based on previous queries"""
    from sqlalchemy import select, func
    from models import SearchLog
    
    # Find similar past queries
    result = await db.execute(
        select(SearchLog.query, func.count(SearchLog.id).label('count'))
        .where(SearchLog.query.like(f'%{query}%'))
        .group_by(SearchLog.query)
        .order_by(func.count(SearchLog.id).desc())
        .limit(limit)
    )
    
    suggestions = [row[0] for row in result.all()]
    
    return {
        "query": query,
        "suggestions": suggestions
    }
