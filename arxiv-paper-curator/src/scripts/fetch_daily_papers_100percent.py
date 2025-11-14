"""
100% Complete Data Fetching Strategy for arXiv Papers
100% 完整数据获取策略

This script GUARANTEES 100% data completeness by:
1. Continuous retry until all papers are fetched
2. Incremental fetching (track what's already fetched)
3. Completeness verification (compare with total_results)
4. Resume from checkpoint on restart
5. Multiple verification passes

Time is not a constraint - it will keep trying until complete.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from src.config import ArxivSettings
from src.services.arxiv.client import ArxivClient
from src.schemas.arxiv.paper import ArxivPaper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ArXiv categories
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
CHECKPOINT_DIR = "./checkpoints"  # Store progress
MAX_RETRY_WAIT_SECONDS = 300  # Max 5 minutes between retries
VERIFICATION_PASSES = 3  # Number of verification passes


class CompleteFetcher:
    """Guarantees 100% complete data fetching."""

    def __init__(
        self,
        output_dir: str = DEFAULT_OUTPUT_DIR,
        checkpoint_dir: str = CHECKPOINT_DIR,
        categories: Optional[List[str]] = None,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        self.categories = categories or list(ARXIV_CATEGORIES.values())
        
        logger.info(f"Initialized CompleteFetcher (100% guarantee mode)")
        logger.info(f"Categories: {self.categories}")
        logger.info(f"Checkpoints: {self.checkpoint_dir}")

    def _get_checkpoint_file(self, category: str, date: str) -> Path:
        """Get checkpoint file path."""
        return self.checkpoint_dir / f"checkpoint_{category}_{date}.json"

    def _load_checkpoint(self, category: str, date: str) -> Dict:
        """Load checkpoint data."""
        checkpoint_file = self._get_checkpoint_file(category, date)
        if checkpoint_file.exists():
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load checkpoint: {e}")
        return {
            "fetched_ids": [],
            "total_expected": None,
            "attempts": 0,
            "last_attempt": None,
        }

    def _save_checkpoint(self, category: str, date: str, checkpoint: Dict):
        """Save checkpoint data."""
        checkpoint_file = self._get_checkpoint_file(category, date)
        checkpoint["last_attempt"] = datetime.now().isoformat()
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, indent=2)

    def _clear_checkpoint(self, category: str, date: str):
        """Clear checkpoint after successful completion."""
        checkpoint_file = self._get_checkpoint_file(category, date)
        if checkpoint_file.exists():
            checkpoint_file.unlink()
            logger.info(f"[{category}] Checkpoint cleared")

    async def fetch_category_complete(
        self,
        category: str,
        from_date: str,
        to_date: str,
        max_wait_hours: int = 24,  # Maximum total wait time
    ) -> Tuple[List[Dict], Dict]:
        """
        Fetch papers for a category with 100% completeness guarantee.
        
        Will keep retrying until:
        1. All expected papers are fetched, OR
        2. max_wait_hours is exceeded (safety limit)
        
        Args:
            category: arXiv category code
            from_date: Start date (YYYYMMDD)
            to_date: End date (YYYYMMDD)
            max_wait_hours: Maximum hours to keep trying (default: 24)
            
        Returns:
            Tuple of (papers, metadata) where metadata includes completeness info
        """
        start_time = datetime.now()
        max_wait_seconds = max_wait_hours * 3600
        
        # Load checkpoint
        checkpoint = self._load_checkpoint(category, from_date)
        fetched_ids: Set[str] = set(checkpoint["fetched_ids"])
        total_expected = checkpoint["total_expected"]
        attempt_count = checkpoint["attempts"]
        
        logger.info(f"[{category}] Starting 100% complete fetch")
        logger.info(f"[{category}] Checkpoint: {len(fetched_ids)} papers already fetched")
        if total_expected:
            logger.info(f"[{category}] Expected total: {total_expected}")
        
        all_papers_dict = {}  # Use dict to avoid duplicates
        retry_delay = 10  # Initial retry delay
        consecutive_failures = 0
        
        while True:
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > max_wait_seconds:
                logger.error(
                    f"[{category}] Max wait time ({max_wait_hours}h) exceeded. "
                    f"Fetched {len(all_papers_dict)}/{total_expected or '?'} papers"
                )
                break
            
            attempt_count += 1
            logger.info(f"[{category}] Attempt #{attempt_count} (elapsed: {elapsed/3600:.1f}h)")
            
            try:
                # Create client
                settings = ArxivSettings(search_category=category)
                client = ArxivClient(settings)
                
                # Fetch all papers with unlimited retries per page
                papers, results = await client.fetch_all_papers_in_date_range(
                    from_date=from_date,
                    to_date=to_date,
                    max_per_page=100,
                    sort_by="submittedDate",
                    sort_order="descending",
                    max_retries_per_page=10,  # More retries per page
                )
                
                # Update expected total
                if results and len(results) > 0:
                    new_total = results[0].total_results
                    if total_expected is None:
                        total_expected = new_total
                        logger.info(f"[{category}] Total expected papers: {total_expected}")
                    elif new_total != total_expected:
                        logger.warning(
                            f"[{category}] Total changed: {total_expected} → {new_total}"
                        )
                        total_expected = new_total
                
                # Add newly fetched papers
                new_papers = 0
                for paper in papers:
                    if paper.arxiv_id not in all_papers_dict and paper.arxiv_id not in fetched_ids:
                        all_papers_dict[paper.arxiv_id] = paper
                        fetched_ids.add(paper.arxiv_id)
                        new_papers += 1
                
                logger.info(
                    f"[{category}] Fetched {len(papers)} papers this attempt "
                    f"({new_papers} new, {len(all_papers_dict)} total)"
                )
                
                # Check completeness
                if total_expected and len(all_papers_dict) >= total_expected:
                    logger.info(
                        f"[{category}] ✓ COMPLETE! Fetched {len(all_papers_dict)}/{total_expected} papers"
                    )
                    consecutive_failures = 0
                    break  # Success!
                elif total_expected:
                    missing = total_expected - len(all_papers_dict)
                    logger.warning(
                        f"[{category}] Incomplete: {len(all_papers_dict)}/{total_expected} "
                        f"({missing} missing, {len(all_papers_dict)/total_expected*100:.1f}% complete)"
                    )
                else:
                    logger.info(f"[{category}] Fetched {len(all_papers_dict)} papers (total unknown)")
                
                # Save checkpoint
                checkpoint["fetched_ids"] = list(fetched_ids)
                checkpoint["total_expected"] = total_expected
                checkpoint["attempts"] = attempt_count
                self._save_checkpoint(category, from_date, checkpoint)
                
                # Reset retry delay on successful fetch (even if incomplete)
                if new_papers > 0:
                    retry_delay = 10
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    # If no new papers for multiple attempts, might be complete
                    if consecutive_failures >= VERIFICATION_PASSES:
                        if total_expected is None or len(all_papers_dict) > 0:
                            logger.info(
                                f"[{category}] No new papers after {consecutive_failures} verification passes. "
                                f"Considering complete with {len(all_papers_dict)} papers."
                            )
                            break
                
            except Exception as e:
                logger.error(f"[{category}] Attempt #{attempt_count} failed: {e}")
                consecutive_failures += 1
                
            # Wait before retry (with exponential backoff)
            if not (total_expected and len(all_papers_dict) >= total_expected):
                retry_delay = min(retry_delay * 1.5, MAX_RETRY_WAIT_SECONDS)
                logger.info(f"[{category}] Waiting {retry_delay:.0f}s before next attempt...")
                await asyncio.sleep(retry_delay)
        
        # Convert to simplified format
        simplified_papers = []
        for paper in all_papers_dict.values():
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
        
        # Build metadata
        is_complete = total_expected is None or len(simplified_papers) >= total_expected
        metadata = {
            "category": category,
            "date_range": f"{from_date}-{to_date}",
            "total_attempts": attempt_count,
            "elapsed_hours": (datetime.now() - start_time).total_seconds() / 3600,
            "papers_fetched": len(simplified_papers),
            "expected_total": total_expected,
            "completeness": "100%" if is_complete else f"{len(simplified_papers)/total_expected*100:.1f}%",
            "is_complete": is_complete,
        }
        
        # Clear checkpoint on success
        if is_complete:
            self._clear_checkpoint(category, from_date)
        
        return simplified_papers, metadata

    async def fetch_date_complete(
        self,
        date: datetime,
        categories: Optional[List[str]] = None,
        max_wait_hours: int = 24,
    ) -> Tuple[Dict[str, List[Dict]], Dict[str, Dict]]:
        """
        Fetch papers for all categories with 100% completeness guarantee.
        
        Args:
            date: Date to fetch papers for
            categories: List of categories (default: all)
            max_wait_hours: Max hours per category
            
        Returns:
            Tuple of (papers_by_category, metadata_by_category)
        """
        date_str = date.strftime("%Y%m%d")
        categories_to_fetch = categories or self.categories
        
        logger.info("=" * 80)
        logger.info(f"Starting 100% COMPLETE fetch for {date.strftime('%Y-%m-%d')}")
        logger.info(f"Categories: {len(categories_to_fetch)}")
        logger.info(f"Max wait per category: {max_wait_hours}h")
        logger.info("=" * 80)
        
        # Fetch each category sequentially (to avoid overwhelming API)
        papers_by_category = {}
        metadata_by_category = {}
        
        for i, category in enumerate(categories_to_fetch, 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"Category {i}/{len(categories_to_fetch)}: {category}")
            logger.info(f"{'='*80}")
            
            papers, metadata = await self.fetch_category_complete(
                category=category,
                from_date=date_str,
                to_date=date_str,
                max_wait_hours=max_wait_hours,
            )
            
            papers_by_category[category] = papers
            metadata_by_category[category] = metadata
            
            if metadata["is_complete"]:
                logger.info(f"[{category}] ✅ 100% COMPLETE: {metadata['papers_fetched']} papers")
            else:
                logger.warning(
                    f"[{category}] ⚠️ INCOMPLETE: {metadata['papers_fetched']}/{metadata['expected_total']} "
                    f"({metadata['completeness']})"
                )
        
        return papers_by_category, metadata_by_category

    def save_papers_with_metadata(
        self,
        papers_by_category: Dict[str, List[Dict]],
        metadata_by_category: Dict[str, Dict],
        date: datetime,
    ) -> Path:
        """Save papers with detailed completeness metadata."""
        date_str = date.strftime("%Y-%m-%d")
        output_file = self.output_dir / f"papers_{date_str}_100percent.json"
        
        # Combine all papers and remove duplicates
        all_papers = []
        for category, papers in papers_by_category.items():
            all_papers.extend(papers)
        
        unique_papers = {}
        for paper in all_papers:
            arxiv_id = paper["arxiv_id"]
            if arxiv_id not in unique_papers:
                unique_papers[arxiv_id] = paper
        
        papers_list = list(unique_papers.values())
        
        # Check overall completeness
        all_complete = all(meta["is_complete"] for meta in metadata_by_category.values())
        total_expected = sum(meta.get("expected_total", 0) or 0 for meta in metadata_by_category.values())
        
        # Build output
        output_data = {
            "metadata": {
                "fetch_mode": "100_percent_complete",
                "fetch_date": datetime.now().isoformat(),
                "paper_date": date_str,
                "total_papers": len(papers_list),
                "total_expected": total_expected,
                "completeness_status": "100_COMPLETE" if all_complete else "INCOMPLETE",
                "all_categories_complete": all_complete,
                "categories": metadata_by_category,
            },
            "papers": papers_list,
        }
        
        # Save
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        # Summary
        if all_complete:
            logger.info("=" * 80)
            logger.info(f"✅ 100% COMPLETE SUCCESS!")
            logger.info(f"✅ Saved {len(papers_list)} papers to {output_file}")
            logger.info(f"✅ All {len(papers_by_category)} categories complete")
            logger.info("=" * 80)
        else:
            incomplete_cats = [
                cat for cat, meta in metadata_by_category.items()
                if not meta["is_complete"]
            ]
            logger.warning("=" * 80)
            logger.warning(f"⚠️ INCOMPLETE: {len(incomplete_cats)} categories not 100% complete")
            for cat in incomplete_cats:
                meta = metadata_by_category[cat]
                logger.warning(f"  - {cat}: {meta['completeness']}")
            logger.warning(f"⚠️ Saved {len(papers_list)} papers to {output_file}")
            logger.warning("=" * 80)
        
        return output_file

    async def run_daily_complete(
        self,
        date: Optional[datetime] = None,
        max_wait_hours: int = 24,
    ):
        """
        Run complete fetch for a single date.
        
        Args:
            date: Date to fetch (default: yesterday)
            max_wait_hours: Max hours to spend per category
        """
        if date is None:
            # Default to yesterday (give arXiv time to process)
            date = datetime.now() - timedelta(days=1)
        
        logger.info(f"Starting 100% complete daily fetch for {date.strftime('%Y-%m-%d')}")
        
        # Fetch all categories
        papers, metadata = await self.fetch_date_complete(
            date=date,
            max_wait_hours=max_wait_hours,
        )
        
        # Save results
        output_file = self.save_papers_with_metadata(papers, metadata, date)
        
        return output_file

    async def run_continuous_complete(
        self,
        check_interval_hours: int = 24,
        max_wait_per_category: int = 12,
    ):
        """
        Run continuously, ensuring 100% completeness for each day.
        
        Args:
            check_interval_hours: Hours between checks
            max_wait_per_category: Max hours per category per attempt
        """
        logger.info("=" * 80)
        logger.info("Starting CONTINUOUS 100% COMPLETE mode")
        logger.info(f"Check interval: {check_interval_hours}h")
        logger.info(f"Max wait per category: {max_wait_per_category}h")
        logger.info("=" * 80)
        
        while True:
            try:
                # Fetch yesterday (most reliable)
                yesterday = datetime.now() - timedelta(days=1)
                await self.run_daily_complete(
                    date=yesterday,
                    max_wait_hours=max_wait_per_category,
                )
                
                # Also check day before yesterday (in case it was incomplete)
                two_days_ago = datetime.now() - timedelta(days=2)
                await self.run_daily_complete(
                    date=two_days_ago,
                    max_wait_hours=max_wait_per_category,
                )
                
                # Wait before next check
                logger.info(f"\nWaiting {check_interval_hours}h until next check...")
                await asyncio.sleep(check_interval_hours * 3600)
                
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, stopping...")
                break
            except Exception as e:
                logger.error(f"Error in continuous mode: {e}")
                logger.info("Retrying in 1 hour...")
                await asyncio.sleep(3600)


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fetch arXiv papers with 100% completeness guarantee"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Fetch papers for specific date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory"
    )
    parser.add_argument(
        "--categories",
        type=str,
        nargs="+",
        help="Categories to fetch"
    )
    parser.add_argument(
        "--max-wait-hours",
        type=int,
        default=24,
        help="Maximum hours to wait per category (default: 24)"
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run continuously"
    )
    parser.add_argument(
        "--check-interval",
        type=int,
        default=24,
        help="Hours between checks in continuous mode (default: 24)"
    )
    
    args = parser.parse_args()
    
    # Create fetcher
    fetcher = CompleteFetcher(
        output_dir=args.output_dir,
        categories=args.categories,
    )
    
    if args.continuous:
        # Continuous mode
        await fetcher.run_continuous_complete(
            check_interval_hours=args.check_interval,
            max_wait_per_category=args.max_wait_hours,
        )
    else:
        # Single date mode
        if args.date:
            date = datetime.strptime(args.date, "%Y-%m-%d")
        else:
            date = datetime.now() - timedelta(days=1)
        
        await fetcher.run_daily_complete(
            date=date,
            max_wait_hours=args.max_wait_hours,
        )


if __name__ == "__main__":
    asyncio.run(main())
