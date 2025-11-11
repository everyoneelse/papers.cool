"""
API routes for paper operations
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List, Optional
from datetime import datetime, timedelta

from database import get_db
from models import Paper, UserActivity
from scrapers import ArxivScraper, OpenReviewScraper, ACLScraper
from scrapers.pmlr_scraper import PMLRScraper
from utils.pdf_processor import PDFProcessor
from utils.search_engine import SearchEngine
from loguru import logger

router = APIRouter(prefix="/papers", tags=["papers"])

# Initialize scrapers
arxiv_scraper = ArxivScraper()
openreview_scraper = OpenReviewScraper()
acl_scraper = ACLScraper()
pmlr_scraper = PMLRScraper()

# Initialize utilities
pdf_processor = PDFProcessor()
search_engine = SearchEngine()


@router.get("/arxiv/{paper_id}")
async def get_arxiv_paper(
    paper_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a single ArXiv paper by ID"""
    # Check database first
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    
    if paper:
        # Update view count
        paper.view_count += 1
        await db.commit()
        return paper
    
    # Not in database, fetch from ArXiv
    logger.info(f"Fetching paper {paper_id} from ArXiv")
    paper_data = await arxiv_scraper.fetch_paper(paper_id)
    
    if not paper_data:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Save to database
    paper = Paper(**paper_data)
    db.add(paper)
    await db.commit()
    await db.refresh(paper)
    
    # Add to search index
    search_engine.add_paper(paper_data)
    
    return paper


@router.get("/arxiv/list/{category}")
async def get_arxiv_category_papers(
    category: str,
    date: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get papers from ArXiv category"""
    # Parse date
    target_date = None
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        except:
            raise HTTPException(status_code=400, detail="Invalid date format, use YYYY-MM-DD")
    else:
        target_date = datetime.now()
    
    # Check if we have data in database for this date
    date_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    date_end = date_start + timedelta(days=1)
    
    result = await db.execute(
        select(Paper)
        .where(Paper.source == "arxiv")
        .where(Paper.categories.contains([category]))
        .where(Paper.published_date >= date_start)
        .where(Paper.published_date < date_end)
        .order_by(desc(Paper.published_date))
        .offset(skip)
        .limit(limit)
    )
    papers = result.scalars().all()
    
    # If no papers in database, fetch from ArXiv
    if not papers:
        logger.info(f"Fetching papers for {category} from ArXiv")
        paper_list = await arxiv_scraper.fetch_latest(category, target_date)
        
        # Save to database
        for paper_data in paper_list:
            paper = Paper(**paper_data)
            db.add(paper)
        
        await db.commit()
        
        # Add to search index
        search_engine.add_papers_batch(paper_list)
        
        # Re-fetch from database
        result = await db.execute(
            select(Paper)
            .where(Paper.source == "arxiv")
            .where(Paper.categories.contains([category]))
            .where(Paper.published_date >= date_start)
            .where(Paper.published_date < date_end)
            .order_by(desc(Paper.published_date))
            .offset(skip)
            .limit(limit)
        )
        papers = result.scalars().all()
    
    return {
        "category": category,
        "date": target_date.strftime("%Y-%m-%d"),
        "count": len(papers),
        "papers": papers
    }


@router.get("/arxiv/combined")
async def get_arxiv_combined_papers(
    include: str = Query(..., description="Categories to include (comma-separated)"),
    exclude: Optional[str] = Query(None, description="Categories to exclude (comma-separated)"),
    date: Optional[str] = None,
    skip: int = 0,
    limit: int = 200,
    db: AsyncSession = Depends(get_db)
):
    """Get papers from multiple ArXiv categories with exclusions"""
    # Parse categories
    include_cats = [c.strip() for c in include.split(',')]
    exclude_cats = [c.strip() for c in exclude.split(',')] if exclude else []
    
    # Parse date
    target_date = datetime.now() if not date else datetime.strptime(date, "%Y-%m-%d")
    
    # Fetch papers with category union/difference
    paper_list = await arxiv_scraper.fetch_category_papers(
        include_cats,
        exclude_cats,
        target_date
    )
    
    # Save new papers to database
    for paper_data in paper_list:
        result = await db.execute(select(Paper).where(Paper.id == paper_data['id']))
        existing = result.scalar_one_or_none()
        
        if not existing:
            paper = Paper(**paper_data)
            db.add(paper)
    
    await db.commit()
    
    return {
        "include_categories": include_cats,
        "exclude_categories": exclude_cats,
        "date": target_date.strftime("%Y-%m-%d"),
        "count": len(paper_list),
        "papers": paper_list[skip:skip+limit]
    }


@router.get("/venue/{venue_id}")
async def get_venue_papers(
    venue_id: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get papers from a specific venue/conference"""
    # Check database first
    result = await db.execute(
        select(Paper)
        .where(Paper.venue == venue_id)
        .order_by(desc(Paper.published_date))
        .offset(skip)
        .limit(limit)
    )
    papers = result.scalars().all()
    
    return {
        "venue": venue_id,
        "count": len(papers),
        "papers": papers
    }


@router.get("/{source}/{paper_id}")
async def get_paper_generic(
    source: str,
    paper_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a paper from any source"""
    full_id = f"{paper_id}@{source.upper()}" if '@' not in paper_id else paper_id
    
    # Check database
    result = await db.execute(select(Paper).where(Paper.id == full_id))
    paper = result.scalar_one_or_none()
    
    if paper:
        paper.view_count += 1
        await db.commit()
        return paper
    
    # Fetch from source
    scraper = None
    if source.lower() == "openreview":
        scraper = openreview_scraper
        paper_data = await scraper.fetch_paper(paper_id.replace('@OpenReview', ''))
    elif source.lower() == "acl":
        scraper = acl_scraper
        paper_data = await scraper.fetch_paper(paper_id.replace('@ACL', ''))
    elif source.lower() == "pmlr":
        scraper = pmlr_scraper
        # Parse volume from paper_id if present
        parts = paper_id.split('@')
        volume = parts[1] if len(parts) > 1 else None
        paper_data = await scraper.fetch_paper(parts[0], volume)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported source: {source}")
    
    if not paper_data:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Save to database
    paper = Paper(**paper_data)
    db.add(paper)
    await db.commit()
    await db.refresh(paper)
    
    # Add to search index
    search_engine.add_paper(paper_data)
    
    return paper


@router.post("/papers/{paper_id}/click")
async def track_paper_click(
    paper_id: str,
    action: str = Query(..., description="Action type: pdf_click or kimi_click"),
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Track paper click (PDF or Kimi)"""
    # Update paper statistics
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if action == "pdf_click":
        paper.pdf_click_count += 1
    elif action == "kimi_click":
        paper.kimi_click_count += 1
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    # Log user activity
    if user_id:
        activity = UserActivity(
            user_id=user_id,
            paper_id=paper_id,
            action=action
        )
        db.add(activity)
    
    await db.commit()
    
    return {"status": "success"}


@router.get("/papers/{paper_id}/full_text")
async def get_paper_full_text(
    paper_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Extract full text from paper PDF"""
    # Get paper
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Check if already extracted
    if paper.full_text:
        return {"paper_id": paper_id, "full_text": paper.full_text}
    
    # Extract from PDF
    if not paper.pdf_url:
        raise HTTPException(status_code=400, detail="No PDF URL available")
    
    logger.info(f"Extracting full text from {paper.pdf_url}")
    full_text = await pdf_processor.extract_text(paper.pdf_url)
    
    if not full_text:
        raise HTTPException(status_code=500, detail="Failed to extract text from PDF")
    
    # Save to database
    paper.full_text = full_text
    await db.commit()
    
    # Update search index
    search_engine.add_paper({
        'id': paper.id,
        'title': paper.title,
        'authors': paper.authors,
        'abstract': paper.abstract,
        'full_text': full_text,
        'categories': paper.categories,
        'venue': paper.venue,
        'published_date': paper.published_date
    })
    
    return {"paper_id": paper_id, "full_text": full_text}
