"""
API routes for RSS/Atom feeds
"""
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timedelta
from feedgen.feed import FeedGenerator

from database import get_db
from models import Paper

router = APIRouter(prefix="/feeds", tags=["feeds"])


@router.get("/arxiv/{category}")
async def get_arxiv_feed(
    category: str,
    days: int = 7,
    db: AsyncSession = Depends(get_db)
):
    """Generate Atom feed for ArXiv category"""
    # Get recent papers
    since_date = datetime.now() - timedelta(days=days)
    
    result = await db.execute(
        select(Paper)
        .where(Paper.source == "arxiv")
        .where(Paper.categories.contains([category]))
        .where(Paper.published_date >= since_date)
        .order_by(desc(Paper.published_date))
        .limit(100)
    )
    papers = result.scalars().all()
    
    # Generate feed
    fg = FeedGenerator()
    fg.id(f'https://papers.cool/arxiv/{category}')
    fg.title(f'Cool Papers - ArXiv {category}')
    fg.link(href=f'https://papers.cool/arxiv/{category}', rel='alternate')
    fg.description(f'Latest papers from ArXiv {category}')
    fg.language('en')
    fg.updated(datetime.now())
    
    for paper in papers:
        fe = fg.add_entry()
        fe.id(paper.paper_url or f'https://papers.cool/arxiv/{paper.id}')
        fe.title(paper.title)
        fe.link(href=paper.paper_url or f'https://papers.cool/arxiv/{paper.id}')
        fe.description(paper.abstract or '')
        fe.author({'name': ', '.join(paper.authors[:3])})
        if paper.published_date:
            fe.published(paper.published_date)
            fe.updated(paper.updated_date or paper.published_date)
    
    # Return Atom feed
    atom_str = fg.atom_str(pretty=True)
    return Response(content=atom_str, media_type='application/atom+xml')


@router.get("/venue/{venue_id}")
async def get_venue_feed(
    venue_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Generate Atom feed for venue/conference"""
    # Get papers from venue
    result = await db.execute(
        select(Paper)
        .where(Paper.venue == venue_id)
        .order_by(desc(Paper.published_date))
        .limit(100)
    )
    papers = result.scalars().all()
    
    # Generate feed
    fg = FeedGenerator()
    fg.id(f'https://papers.cool/venue/{venue_id}')
    fg.title(f'Cool Papers - {venue_id}')
    fg.link(href=f'https://papers.cool/venue/{venue_id}', rel='alternate')
    fg.description(f'Papers from {venue_id}')
    fg.language('en')
    fg.updated(datetime.now())
    
    for paper in papers:
        fe = fg.add_entry()
        fe.id(paper.paper_url or f'https://papers.cool/venue/{paper.id}')
        fe.title(paper.title)
        fe.link(href=paper.paper_url or f'https://papers.cool/venue/{paper.id}')
        fe.description(paper.abstract or '')
        fe.author({'name': ', '.join(paper.authors[:3]) if paper.authors else 'Unknown'})
        if paper.published_date:
            fe.published(paper.published_date)
            fe.updated(paper.updated_date or paper.published_date)
    
    # Return Atom feed
    atom_str = fg.atom_str(pretty=True)
    return Response(content=atom_str, media_type='application/atom+xml')


@router.get("/latest")
async def get_latest_feed(
    days: int = 7,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Generate Atom feed for all latest papers"""
    since_date = datetime.now() - timedelta(days=days)
    
    result = await db.execute(
        select(Paper)
        .where(Paper.published_date >= since_date)
        .order_by(desc(Paper.published_date))
        .limit(limit)
    )
    papers = result.scalars().all()
    
    # Generate feed
    fg = FeedGenerator()
    fg.id('https://papers.cool/latest')
    fg.title('Cool Papers - Latest Papers')
    fg.link(href='https://papers.cool', rel='alternate')
    fg.description('Latest papers from all sources')
    fg.language('en')
    fg.updated(datetime.now())
    
    for paper in papers:
        fe = fg.add_entry()
        fe.id(paper.paper_url or f'https://papers.cool/{paper.source}/{paper.id}')
        fe.title(paper.title)
        fe.link(href=paper.paper_url or f'https://papers.cool/{paper.source}/{paper.id}')
        fe.description(paper.abstract or '')
        fe.author({'name': ', '.join(paper.authors[:3]) if paper.authors else 'Unknown'})
        if paper.published_date:
            fe.published(paper.published_date)
            fe.updated(paper.updated_date or paper.published_date)
        
        # Add categories as tags
        if paper.categories:
            for cat in paper.categories[:5]:
                fe.category(term=cat)
    
    # Return Atom feed
    atom_str = fg.atom_str(pretty=True)
    return Response(content=atom_str, media_type='application/atom+xml')
