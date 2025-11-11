"""
PMLR (Proceedings of Machine Learning Research) scraper
"""
from typing import Dict, List, Optional
from datetime import datetime
import httpx
from pyquery import PyQuery as pq
from loguru import logger

from .base_scraper import BaseScraper
from config import settings


class PMLRScraper(BaseScraper):
    """Scraper for PMLR papers"""
    
    def __init__(self):
        super().__init__(rate_limit=1.0)
        self.base_url = settings.PMLR_BASE_URL
        
    @property
    def source_name(self) -> str:
        return "pmlr"
    
    async def fetch_paper(self, paper_id: str, volume: str = None) -> Optional[Dict]:
        """
        Fetch a single PMLR paper
        
        Args:
            paper_id: Paper ID (e.g., "smith20a")
            volume: Volume ID (e.g., "v119")
            
        Returns:
            Paper metadata or None
        """
        if not volume:
            # Try to extract from full ID
            if '@' in paper_id:
                parts = paper_id.split('@')
                if len(parts) >= 2:
                    paper_id = parts[0]
                    volume = parts[1]
        
        if not volume:
            logger.error(f"Volume required for PMLR paper {paper_id}")
            return None
        
        await self._rate_limit_wait()
        
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                # Fetch paper page
                url = f"{self.base_url}/{volume}/{paper_id}.html"
                response = await client.get(url)
                response.raise_for_status()
                
                doc = pq(response.text)
                
                # Extract title
                title = doc('#main-container h1').text().strip()
                
                # Extract authors
                authors = []
                for author in doc('.authors span[itemprop="author"]').items():
                    name = author.text().strip()
                    if name:
                        authors.append(name)
                
                # Extract abstract
                abstract = doc('#abstract').text().strip()
                
                # Get PDF URL
                pdf_elem = doc('a[href$=".pdf"]')
                pdf_url = pdf_elem.attr('href') if pdf_elem else f"{self.base_url}/{volume}/{paper_id}/{paper_id}.pdf"
                if not pdf_url.startswith('http'):
                    pdf_url = f"{self.base_url}/{volume}/{pdf_url}"
                
                # Extract venue/conference name
                venue_elem = doc('.proceedings')
                venue = venue_elem.text().strip() if venue_elem else volume
                
                # Extract year from volume or page
                year_elem = doc('span.year')
                year = None
                if year_elem:
                    try:
                        year = int(year_elem.text().strip())
                    except:
                        pass
                
                published_date = datetime(year, 1, 1) if year else None
                
                return {
                    'id': f"{paper_id}@{volume}@PMLR",
                    'title': title,
                    'authors': authors,
                    'abstract': abstract,
                    'paper_url': url,
                    'pdf_url': pdf_url,
                    'published_date': published_date,
                    'updated_date': published_date,
                    'categories': [venue],
                    'subjects': [venue],
                    'venue': venue,
                    'metadata': {'volume': volume}
                }
                
        except Exception as e:
            logger.error(f"Error fetching PMLR paper {paper_id} from {volume}: {e}")
            return None
    
    async def fetch_latest(self, volume: str, date: Optional[datetime] = None) -> List[Dict]:
        """
        Fetch all papers from a PMLR volume
        
        Args:
            volume: Volume ID (e.g., "v119")
            date: Not used
            
        Returns:
            List of paper metadata
        """
        await self._rate_limit_wait()
        
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                # Fetch volume index page
                url = f"{self.base_url}/{volume}/"
                response = await client.get(url)
                response.raise_for_status()
                
                doc = pq(response.text)
                papers = []
                
                # Find all paper links
                for link in doc('.paper a[href$=".html"]').items():
                    href = link.attr('href')
                    if href:
                        # Extract paper ID from URL
                        paper_id = href.replace('.html', '').split('/')[-1]
                        
                        # Fetch individual paper
                        paper = await self.fetch_paper(paper_id, volume)
                        if paper:
                            papers.append(paper)
                
                logger.info(f"Fetched {len(papers)} papers from PMLR volume {volume}")
                return papers
                
        except Exception as e:
            logger.error(f"Error fetching PMLR volume {volume}: {e}")
            return []
