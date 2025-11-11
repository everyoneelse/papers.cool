"""
Script to update papers from various sources
Run this script periodically (e.g., daily) to fetch latest papers
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from loguru import logger
from sqlalchemy import select

from database import AsyncSessionLocal
from models import Paper
from scrapers import ArxivScraper, OpenReviewScraper
from utils.search_engine import SearchEngine


async def update_arxiv_papers(categories: list[str]):
    """Update ArXiv papers for specified categories"""
    scraper = ArxivScraper()
    search_engine = SearchEngine()
    
    logger.info(f"Updating ArXiv papers for categories: {categories}")
    
    async with AsyncSessionLocal() as db:
        all_papers = []
        
        for category in categories:
            logger.info(f"Fetching papers for {category}...")
            papers = await scraper.fetch_latest(category)
            logger.info(f"Found {len(papers)} papers in {category}")
            
            for paper_data in papers:
                # Check if paper already exists
                result = await db.execute(
                    select(Paper).where(Paper.id == paper_data['id'])
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    logger.debug(f"Paper {paper_data['id']} already exists, skipping")
                    continue
                
                # Add new paper
                paper = Paper(**paper_data)
                db.add(paper)
                all_papers.append(paper_data)
                logger.info(f"Added paper: {paper_data['title'][:50]}...")
        
        # Commit to database
        await db.commit()
        logger.info(f"Added {len(all_papers)} new papers to database")
        
        # Update search index
        if all_papers:
            search_engine.add_papers_batch(all_papers)
            logger.info("Updated search index")


async def update_openreview_papers(venues: list[str]):
    """Update OpenReview papers for specified venues"""
    scraper = OpenReviewScraper()
    search_engine = SearchEngine()
    
    logger.info(f"Updating OpenReview papers for venues: {venues}")
    
    async with AsyncSessionLocal() as db:
        all_papers = []
        
        for venue in venues:
            logger.info(f"Fetching papers for {venue}...")
            papers = await scraper.fetch_latest(venue)
            logger.info(f"Found {len(papers)} papers in {venue}")
            
            for paper_data in papers:
                result = await db.execute(
                    select(Paper).where(Paper.id == paper_data['id'])
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    continue
                
                paper = Paper(**paper_data)
                db.add(paper)
                all_papers.append(paper_data)
        
        await db.commit()
        logger.info(f"Added {len(all_papers)} new papers to database")
        
        if all_papers:
            search_engine.add_papers_batch(all_papers)


async def main():
    """Main update routine"""
    logger.info("=" * 50)
    logger.info(f"Starting paper update at {datetime.now()}")
    logger.info("=" * 50)
    
    # ArXiv categories to monitor
    arxiv_categories = [
        "cs.AI",    # Artificial Intelligence
        "cs.LG",    # Machine Learning
        "cs.CL",    # Computation and Language
        "cs.CV",    # Computer Vision
        "cs.NE",    # Neural and Evolutionary Computing
        "cs.RO",    # Robotics
        "stat.ML",  # Machine Learning (Statistics)
    ]
    
    # Update ArXiv
    await update_arxiv_papers(arxiv_categories)
    
    # Optional: Update OpenReview (uncomment and add venues)
    # openreview_venues = [
    #     "ICLR.cc/2024/Conference/-/Blind_Submission",
    # ]
    # await update_openreview_papers(openreview_venues)
    
    logger.info("=" * 50)
    logger.info(f"Paper update completed at {datetime.now()}")
    logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
