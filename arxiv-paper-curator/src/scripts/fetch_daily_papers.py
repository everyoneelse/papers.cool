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
    ) -> tuple[List[Dict], bool, Optional[str]]:
        """
        Fetch papers for a single category with retry logic.

        Args:
            category: arXiv category code (e.g., "cs.AI")
            from_date: Start date (YYYYMMDD)
            to_date: End date (YYYYMMDD)
            retry_attempts: Maximum number of retry attempts

        Returns:
            Tuple of (papers, success, error_message):
                - papers: List of paper dictionaries with essential fields (may be partial)
                - success: True if fully successful, False if had errors
                - error_message: Error description if failed, None if successful
        """
        best_result = []  # Keep track of the best (longest) result we got
        last_error = None
        
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
                    max_retries_per_page=5,  # Allow retries per page
                )
                
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
                
                # Check if we got all expected papers
                if results and len(results) > 0:
                    expected_total = results[0].total_results
                    if len(simplified_papers) >= expected_total:
                        logger.info(f"[{category}] Successfully fetched ALL {len(simplified_papers)}/{expected_total} papers")
                        return simplified_papers, True, None
                    else:
                        logger.warning(
                            f"[{category}] Partially fetched {len(simplified_papers)}/{expected_total} papers "
                            f"({len(simplified_papers)/expected_total*100:.1f}%)"
                        )
                        # Keep this result if it's better than previous attempts
                        if len(simplified_papers) > len(best_result):
                            best_result = simplified_papers
                        
                        # If we got most of the papers (>90%), consider it good enough
                        if len(simplified_papers) / expected_total > 0.9:
                            logger.info(f"[{category}] Got >90% of papers, accepting as complete")
                            return simplified_papers, True, None
                else:
                    # No results metadata, but we got some papers
                    if simplified_papers:
                        logger.info(f"[{category}] Fetched {len(simplified_papers)} papers (total unknown)")
                        return simplified_papers, True, None
                
                # If we got here, we have partial results - will retry
                last_error = f"Incomplete fetch: got {len(simplified_papers)}/{expected_total if results else 'unknown'} papers"
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"[{category}] Attempt {attempt}/{retry_attempts} failed: {e}")
                
                if attempt < retry_attempts:
                    wait_time = RETRY_DELAY_SECONDS * attempt  # Exponential backoff
                    logger.info(f"[{category}] Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
        
        # All retries exhausted
        if best_result:
            logger.warning(
                f"[{category}] Failed to fetch all papers after {retry_attempts} attempts. "
                f"Returning best partial result: {len(best_result)} papers"
            )
            return best_result, False, f"Partial fetch: {last_error}"
        else:
            logger.error(f"[{category}] Failed completely after {retry_attempts} attempts: {last_error}")
            return [], False, f"Complete failure: {last_error}"

    async def fetch_papers_for_date(
        self,
        date: datetime,
        categories: Optional[List[str]] = None,
    ) -> tuple[Dict[str, List[Dict]], Dict[str, str]]:
        """
        Fetch papers for all categories on a specific date.

        Args:
            date: Date to fetch papers for
            categories: List of categories to fetch (default: all configured categories)

        Returns:
            Tuple of (papers_by_category, failed_categories):
                - papers_by_category: Dictionary mapping category codes to paper lists
                - failed_categories: Dictionary mapping failed category codes to error messages
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
        
        # Build result dictionaries
        papers_by_category = {}
        failed_categories = {}
        partial_categories = {}
        
        for category, (papers, success, error_msg) in zip(categories_to_fetch, results):
            papers_by_category[category] = papers
            
            if success:
                logger.info(f"[{category}] ✓ Successfully retrieved {len(papers)} papers for {date_str}")
            elif papers:
                logger.warning(f"[{category}] ⚠ Partially retrieved {len(papers)} papers for {date_str}: {error_msg}")
                partial_categories[category] = error_msg
            else:
                logger.error(f"[{category}] ✗ Failed to retrieve papers for {date_str}: {error_msg}")
                failed_categories[category] = error_msg
        
        # Summary
        success_count = len(categories_to_fetch) - len(failed_categories) - len(partial_categories)
        if failed_categories:
            logger.error(f"Summary: {success_count} succeeded, {len(partial_categories)} partial, {len(failed_categories)} failed")
        elif partial_categories:
            logger.warning(f"Summary: {success_count} succeeded, {len(partial_categories)} partial")
        else:
            logger.info(f"Summary: All {success_count} categories fetched successfully!")
        
        return papers_by_category, failed_categories

    def save_papers_to_json(
        self,
        papers_by_category: Dict[str, List[Dict]],
        date: datetime,
        failed_categories: Optional[Dict[str, str]] = None,
    ) -> Path:
        """
        Save papers to a JSON file with metadata about fetch status.

        Args:
            papers_by_category: Dictionary mapping categories to paper lists
            date: Date the papers were published
            failed_categories: Dictionary of failed/partial categories with error messages

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
        
        # Build metadata
        metadata = {
            "fetch_date": datetime.now().isoformat(),
            "paper_date": date_str,
            "total_papers": len(papers_list),
            "categories_fetched": list(papers_by_category.keys()),
            "papers_per_category": {cat: len(papers) for cat, papers in papers_by_category.items()},
        }
        
        if failed_categories:
            metadata["failed_categories"] = failed_categories
            metadata["fetch_status"] = "partial"
        else:
            metadata["fetch_status"] = "complete"
        
        # Build final output
        output_data = {
            "metadata": metadata,
            "papers": papers_list,
        }
        
        # Save to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        status_msg = "complete" if not failed_categories else f"partial ({len(failed_categories)} categories had issues)"
        logger.info(f"Saved {len(papers_list)} unique papers to {output_file} (status: {status_msg})")
        return output_file

    async def fetch_and_save_daily(self, date: Optional[datetime] = None, force_refetch: bool = False):
        """
        Fetch papers for a specific date and save to JSON.

        Args:
            date: Date to fetch papers for (default: today)
            force_refetch: Force re-fetch even if file exists
        """
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime("%Y-%m-%d")
        logger.info(f"=" * 80)
        logger.info(f"Starting daily fetch for {date_str}")
        logger.info(f"=" * 80)
        
        # Check if we already have data for this date
        output_file = self.output_dir / f"papers_{date_str}.json"
        if output_file.exists() and not force_refetch:
            # Check if previous fetch was partial
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    # Check for old format (list) or new format (dict with metadata)
                    if isinstance(existing_data, dict) and 'metadata' in existing_data:
                        fetch_status = existing_data['metadata'].get('fetch_status', 'unknown')
                        if fetch_status == 'partial':
                            failed_cats = existing_data['metadata'].get('failed_categories', {})
                            logger.warning(f"Previous fetch was partial. Failed categories: {list(failed_cats.keys())}")
                            logger.info(f"Attempting to re-fetch failed categories...")
                            # Will continue to re-fetch
                        else:
                            logger.info(f"Papers for {date_str} already exist at {output_file} (status: complete)")
                            logger.info(f"Use force_refetch=True to re-fetch")
                            return output_file
                    else:
                        # Old format, assume complete
                        logger.info(f"Papers for {date_str} already exist at {output_file}")
                        logger.info(f"Use force_refetch=True to re-fetch")
                        return output_file
            except Exception as e:
                logger.warning(f"Error reading existing file: {e}. Will re-fetch.")
        
        # Fetch papers
        papers_by_category, failed_categories = await self.fetch_papers_for_date(date)
        
        # Save to JSON
        saved_file = self.save_papers_to_json(papers_by_category, date, failed_categories)
        
        # Summary
        total_papers = sum(len(papers) for papers in papers_by_category.values())
        logger.info(f"="*80)
        logger.info(f"Daily fetch complete for {date_str}:")
        logger.info(f"  - Total papers fetched: {total_papers}")
        logger.info(f"  - Categories: {len(papers_by_category)}")
        logger.info(f"  - Output file: {saved_file}")
        
        if failed_categories:
            logger.warning(f"  ⚠ Warning: {len(failed_categories)} categories had issues:")
            for cat, error in failed_categories.items():
                logger.warning(f"    - {cat}: {error}")
            logger.warning(f"  You may want to re-run this date later to get missing papers")
        else:
            logger.info(f"  ✓ All categories fetched successfully!")
        
        logger.info(f"="*80)
        
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
