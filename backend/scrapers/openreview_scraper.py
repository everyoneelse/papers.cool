"""
OpenReview paper scraper
"""
from typing import Dict, List, Optional
from datetime import datetime
import httpx
from loguru import logger

from .base_scraper import BaseScraper
from config import settings


class OpenReviewScraper(BaseScraper):
    """Scraper for OpenReview papers"""
    
    def __init__(self):
        super().__init__(rate_limit=1.0)
        self.api_url = settings.OPENREVIEW_API_URL
        
    @property
    def source_name(self) -> str:
        return "openreview"
    
    async def fetch_paper(self, paper_id: str) -> Optional[Dict]:
        """
        Fetch a single OpenReview paper by ID
        
        Args:
            paper_id: OpenReview forum ID
            
        Returns:
            Paper metadata or None
        """
        await self._rate_limit_wait()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Fetch note (paper) data
                url = f"{self.api_url}/notes"
                params = {'id': paper_id}
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                if not data.get('notes'):
                    logger.warning(f"Paper {paper_id} not found in OpenReview")
                    return None
                
                note = data['notes'][0]
                content = note.get('content', {})
                
                # Extract authors
                authors = content.get('authors', [])
                if isinstance(authors, str):
                    authors = [a.strip() for a in authors.split(',')]
                
                # Get venue/conference
                venue = note.get('invitation', '').split('/')[-1]
                
                return {
                    'id': f"{paper_id}@OpenReview",
                    'title': content.get('title', ''),
                    'authors': authors,
                    'abstract': content.get('abstract', ''),
                    'paper_url': f"https://openreview.net/forum?id={paper_id}",
                    'pdf_url': content.get('pdf') or f"https://openreview.net/pdf?id={paper_id}",
                    'published_date': datetime.fromtimestamp(note.get('cdate', 0) / 1000) if note.get('cdate') else None,
                    'updated_date': datetime.fromtimestamp(note.get('mdate', 0) / 1000) if note.get('mdate') else None,
                    'categories': [venue] if venue else [],
                    'subjects': [venue] if venue else [],
                    'venue': venue,
                    'metadata': {
                        'keywords': content.get('keywords', []),
                        'tldr': content.get('TL;DR', ''),
                    }
                }
                
        except Exception as e:
            logger.error(f"Error fetching OpenReview paper {paper_id}: {e}")
            return None
    
    async def fetch_latest(self, venue: str, date: Optional[datetime] = None) -> List[Dict]:
        """
        Fetch papers from a specific OpenReview venue
        
        Args:
            venue: Venue/conference identifier
            date: Not used for OpenReview
            
        Returns:
            List of paper metadata
        """
        await self._rate_limit_wait()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Query papers by invitation (venue)
                url = f"{self.api_url}/notes"
                params = {
                    'invitation': venue,
                    'details': 'replyCount',
                    'limit': 1000
                }
                
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                papers = []
                
                for note in data.get('notes', []):
                    content = note.get('content', {})
                    paper_id = note.get('id', '')
                    
                    if not paper_id:
                        continue
                    
                    authors = content.get('authors', [])
                    if isinstance(authors, str):
                        authors = [a.strip() for a in authors.split(',')]
                    
                    papers.append({
                        'id': f"{paper_id}@OpenReview",
                        'title': content.get('title', ''),
                        'authors': authors,
                        'abstract': content.get('abstract', ''),
                        'paper_url': f"https://openreview.net/forum?id={paper_id}",
                        'pdf_url': content.get('pdf') or f"https://openreview.net/pdf?id={paper_id}",
                        'published_date': datetime.fromtimestamp(note.get('cdate', 0) / 1000) if note.get('cdate') else None,
                        'updated_date': datetime.fromtimestamp(note.get('mdate', 0) / 1000) if note.get('mdate') else None,
                        'categories': [venue],
                        'subjects': [venue],
                        'venue': venue,
                        'metadata': {
                            'keywords': content.get('keywords', []),
                            'tldr': content.get('TL;DR', ''),
                        }
                    })
                
                logger.info(f"Fetched {len(papers)} papers from OpenReview venue {venue}")
                return papers
                
        except Exception as e:
            logger.error(f"Error fetching OpenReview venue {venue}: {e}")
            return []
