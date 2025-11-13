"""
Continuous task to fetch daily arXiv papers for specified categories.
持续性任务：获取每天上传的指定分类的 arXiv 论文

This script:
- Fetches papers from multiple arXiv categories daily
- Handles API failures with retries
- Saves papers to JSON files (title, authors, abstract, categories, url)
- Runs continuously, checking for new papers at specified intervals
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from src.config import ArxivSettings
from src.services.arxiv.client import ArxivClient
from src.schemas.arxiv.paper import ArxivPaper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ArXiv categories to monitor (from streamlit_app.py)
ARXIV_CATEGORIES = {
    "Artificial Intelligence (cs.AI)": "cs.AI",
    "Computation and Language (cs.CL)": "cs.CL",
    "Computer Vision (cs.CV)": "cs.CV",
    "Machine Learning (cs.LG)": "cs.LG",
    "Neural and Evolutionary Computing (cs.NE)": "cs.NE",
    "Computational Complexity (cs.CC)": "cs.CC",
    "Statistics - Machine Learning (stat.ML)": "stat.ML",
}

# Configuration
DEFAULT_OUTPUT_DIR = "./papers_data"
CHECK_INTERVAL_HOURS = 6  # Check for new papers every 6 hours
MAX_RETRY_ATTEMPTS = 5
RETRY_DELAY_SECONDS = 60


class DailyPapersFetcher:
    """Fetches daily arXiv papers for multiple categories."""

    def __init__(
        self,
        output_dir: str = DEFAULT_OUTPUT_DIR,
        categories: Optional[List[str]] = None,
    ):
        """
        Initialize the daily papers fetcher.

        Args:
            output_dir: Directory to save JSON files
            categories: List of category codes to monitor (default: all categories)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Use all categories if not specified
        self.categories = categories or list(ARXIV_CATEGORIES.values())
        
        logger.info(f"Initialized DailyPapersFetcher with categories: {self.categories}")
        logger.info(f"Output directory: {self.output_dir}")

    async def fetch_papers_for_category(
        self,
        category: str,
        from_date: str,
        to_date: str,
        retry_attempts: int = MAX_RETRY_ATTEMPTS,
    ) -> List[Dict]:
        """
        Fetch papers for a single category with retry logic.

        Args:
            category: arXiv category code (e.g., "cs.AI")
            from_date: Start date (YYYYMMDD)
            to_date: End date (YYYYMMDD)
            retry_attempts: Maximum number of retry attempts

        Returns:
            List of paper dictionaries with essential fields
        """
        for attempt in range(1, retry_attempts + 1):
            try:
                logger.info(f"[{category}] Attempt {attempt}/{retry_attempts}: Fetching papers from {from_date} to {to_date}")
                
                # Create client for this category
                settings = ArxivSettings(search_category=category)
                client = ArxivClient(settings)
                
                # Fetch all papers in date range
                papers, results = await client.fetch_all_papers_in_date_range(
                    from_date=from_date,
                    to_date=to_date,
                    max_per_page=100,  # Reasonable page size
                    sort_by="submittedDate",
                    sort_order="descending",
                )
                
                logger.info(f"[{category}] Successfully fetched {len(papers)} papers")
                
                # Convert to simplified format (only essential fields)
                simplified_papers = []
                for paper in papers:
                    simplified_papers.append({
                        "arxiv_id": paper.arxiv_id,
                        "title": paper.title,
                        "authors": paper.authors,
                        "abstract": paper.abstract,
                        "categories": paper.categories,
                        "published_date": paper.published_date,
                        "url": f"https://arxiv.org/abs/{paper.arxiv_id}",
                        "pdf_url": paper.pdf_url,
                    })
                
                return simplified_papers
                
            except Exception as e:
                logger.error(f"[{category}] Attempt {attempt}/{retry_attempts} failed: {e}")
                
                if attempt < retry_attempts:
                    wait_time = RETRY_DELAY_SECONDS * attempt  # Exponential backoff
                    logger.info(f"[{category}] Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"[{category}] Failed after {retry_attempts} attempts")
                    return []

    async def fetch_papers_for_date(
        self,
        date: datetime,
        categories: Optional[List[str]] = None,
    ) -> Dict[str, List[Dict]]:
        """
        Fetch papers for all categories on a specific date.

        Args:
            date: Date to fetch papers for
            categories: List of categories to fetch (default: all configured categories)

        Returns:
            Dictionary mapping category codes to paper lists
        """
        date_str = date.strftime("%Y%m%d")
        categories_to_fetch = categories or self.categories
        
        logger.info(f"Fetching papers for date {date_str} across {len(categories_to_fetch)} categories")
        
        # Fetch papers for all categories concurrently
        tasks = [
            self.fetch_papers_for_category(
                category=category,
                from_date=date_str,
                to_date=date_str,
            )
            for category in categories_to_fetch
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Build result dictionary
        papers_by_category = {}
        for category, papers in zip(categories_to_fetch, results):
            papers_by_category[category] = papers
            logger.info(f"[{category}] Retrieved {len(papers)} papers for {date_str}")
        
        return papers_by_category

    def save_papers_to_json(
        self,
        papers_by_category: Dict[str, List[Dict]],
        date: datetime,
    ) -> Path:
        """
        Save papers to a JSON file.

        Args:
            papers_by_category: Dictionary mapping categories to paper lists
            date: Date the papers were published

        Returns:
            Path to the saved JSON file
        """
        date_str = date.strftime("%Y-%m-%d")
        output_file = self.output_dir / f"papers_{date_str}.json"
        
        # Combine all papers from all categories
        all_papers = []
        for category, papers in papers_by_category.items():
            all_papers.extend(papers)
        
        # Remove duplicates (papers can appear in multiple categories)
        unique_papers = {}
        for paper in all_papers:
            arxiv_id = paper["arxiv_id"]
            if arxiv_id not in unique_papers:
                unique_papers[arxiv_id] = paper
        
        papers_list = list(unique_papers.values())
        
        # Save to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(papers_list, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(papers_list)} unique papers to {output_file}")
        return output_file

    async def fetch_and_save_daily(self, date: Optional[datetime] = None):
        """
        Fetch papers for a specific date and save to JSON.

        Args:
            date: Date to fetch papers for (default: today)
        """
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime("%Y-%m-%d")
        logger.info(f"=" * 80)
        logger.info(f"Starting daily fetch for {date_str}")
        logger.info(f"=" * 80)
        
        # Check if we already have data for this date
        output_file = self.output_dir / f"papers_{date_str}.json"
        if output_file.exists():
            logger.info(f"Papers for {date_str} already exist at {output_file}")
            logger.info(f"Skipping fetch (delete file to re-fetch)")
            return output_file
        
        # Fetch papers
        papers_by_category = await self.fetch_papers_for_date(date)
        
        # Save to JSON
        saved_file = self.save_papers_to_json(papers_by_category, date)
        
        # Summary
        total_papers = sum(len(papers) for papers in papers_by_category.values())
        logger.info(f"Daily fetch complete for {date_str}:")
        logger.info(f"  - Total papers fetched: {total_papers}")
        logger.info(f"  - Categories: {len(papers_by_category)}")
        logger.info(f"  - Output file: {saved_file}")
        
        return saved_file

    async def run_continuously(
        self,
        check_interval_hours: int = CHECK_INTERVAL_HOURS,
    ):
        """
        Run continuously, fetching papers at regular intervals.

        Args:
            check_interval_hours: Hours between checks for new papers
        """
        logger.info(f"Starting continuous mode (checking every {check_interval_hours} hours)")
        logger.info(f"Categories: {self.categories}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Press Ctrl+C to stop")
        
        while True:
            try:
                # Fetch papers for today
                await self.fetch_and_save_daily()
                
                # Also check yesterday (in case we missed it)
                yesterday = datetime.now() - timedelta(days=1)
                await self.fetch_and_save_daily(yesterday)
                
                # Wait before next check
                logger.info(f"Waiting {check_interval_hours} hours until next check...")
                await asyncio.sleep(check_interval_hours * 3600)
                
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, stopping...")
                break
            except Exception as e:
                logger.error(f"Error in continuous mode: {e}")
                logger.info(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
                await asyncio.sleep(RETRY_DELAY_SECONDS)


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fetch daily arXiv papers for specified categories"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for JSON files (default: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--categories",
        type=str,
        nargs="+",
        default=None,
        help=f"Categories to fetch (default: all). Available: {', '.join(ARXIV_CATEGORIES.values())}"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Fetch papers for specific date (YYYY-MM-DD). If not provided, runs continuously"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=CHECK_INTERVAL_HOURS,
        help=f"Hours between checks in continuous mode (default: {CHECK_INTERVAL_HOURS})"
    )
    
    args = parser.parse_args()
    
    # Create fetcher
    fetcher = DailyPapersFetcher(
        output_dir=args.output_dir,
        categories=args.categories,
    )
    
    # Run once or continuously
    if args.date:
        # Fetch for specific date
        try:
            date = datetime.strptime(args.date, "%Y-%m-%d")
            await fetcher.fetch_and_save_daily(date)
        except ValueError:
            logger.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD")
            return
    else:
        # Run continuously
        await fetcher.run_continuously(check_interval_hours=args.interval)


if __name__ == "__main__":
    asyncio.run(main())
