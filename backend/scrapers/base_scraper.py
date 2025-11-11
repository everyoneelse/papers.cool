"""
Base scraper class for all paper sources
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
from loguru import logger


class BaseScraper(ABC):
    """Abstract base class for paper scrapers"""
    
    def __init__(self, rate_limit: float = 1.0):
        """
        Initialize scraper
        
        Args:
            rate_limit: Minimum seconds between requests
        """
        self.rate_limit = rate_limit
        self.last_request_time = 0.0
        
    async def _rate_limit_wait(self):
        """Wait if necessary to respect rate limits"""
        if self.rate_limit > 0:
            elapsed = asyncio.get_event_loop().time() - self.last_request_time
            if elapsed < self.rate_limit:
                await asyncio.sleep(self.rate_limit - elapsed)
            self.last_request_time = asyncio.get_event_loop().time()
    
    @abstractmethod
    async def fetch_paper(self, paper_id: str) -> Optional[Dict]:
        """
        Fetch a single paper by ID
        
        Args:
            paper_id: Paper identifier
            
        Returns:
            Paper metadata dict or None if not found
        """
        pass
    
    @abstractmethod
    async def fetch_latest(self, category: str, date: Optional[datetime] = None) -> List[Dict]:
        """
        Fetch latest papers for a category
        
        Args:
            category: Category identifier
            date: Target date (defaults to latest)
            
        Returns:
            List of paper metadata dicts
        """
        pass
    
    def normalize_paper(self, raw_data: Dict) -> Dict:
        """
        Normalize paper data to common format
        
        Args:
            raw_data: Raw data from source
            
        Returns:
            Normalized paper dict
        """
        return {
            'id': raw_data.get('id'),
            'source': self.source_name,
            'title': raw_data.get('title', '').strip(),
            'authors': raw_data.get('authors', []),
            'abstract': raw_data.get('abstract', '').strip(),
            'paper_url': raw_data.get('paper_url'),
            'pdf_url': raw_data.get('pdf_url'),
            'published_date': raw_data.get('published_date'),
            'updated_date': raw_data.get('updated_date'),
            'categories': raw_data.get('categories', []),
            'subjects': raw_data.get('subjects', []),
            'venue': raw_data.get('venue'),
            'metadata': raw_data.get('metadata', {})
        }
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the name of this paper source"""
        pass
