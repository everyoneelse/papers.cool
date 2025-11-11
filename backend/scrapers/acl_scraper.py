"""
ACL Anthology scraper
"""
from typing import Dict, List, Optional
from datetime import datetime
import httpx
from pyquery import PyQuery as pq
from loguru import logger

from .base_scraper import BaseScraper
from config import settings


class ACLScraper(BaseScraper):
    """Scraper for ACL Anthology papers"""
    
    def __init__(self):
        super().__init__(rate_limit=1.0)
        self.base_url = settings.ACL_BASE_URL
        
    @property
    def source_name(self) -> str:
        return "acl"
    
    async def fetch_paper(self, paper_id: str) -> Optional[Dict]:
        """
        Fetch a single ACL paper by ID
        
        Args:
            paper_id: ACL paper ID (e.g., "2023.acl-long.123")
            
        Returns:
            Paper metadata or None
        """
        await self._rate_limit_wait()
        
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                # Fetch paper page
                url = f"{self.base_url}/{paper_id}/"
                response = await client.get(url)
                response.raise_for_status()
                
                doc = pq(response.text)
                
                # Extract title
                title = doc('#title').text().strip()
                
                # Extract authors
                authors = []
                for author in doc('#main span[class*="author"]').items():
                    name = author.text().strip()
                    if name:
                        authors.append(name)
                
                # Extract abstract
                abstract = doc('.acl-abstract span').text().strip()
                
                # Extract venue
                venue_elem = doc('.acl-paper-link-block a[title="Anthology venue page"]')
                venue = venue_elem.text().strip() if venue_elem else ''
                
                # Get PDF URL
                pdf_elem = doc('a.badge-primary[href$=".pdf"]')
                pdf_url = pdf_elem.attr('href') if pdf_elem else f"{self.base_url}/{paper_id}.pdf"
                if not pdf_url.startswith('http'):
                    pdf_url = f"{self.base_url}{pdf_url}"
                
                # Extract year from paper ID
                year_match = paper_id.split('.')[0]
                try:
                    year = int(year_match)
                    published_date = datetime(year, 1, 1)
                except:
                    published_date = None
                
                return {
                    'id': f"{paper_id}@ACL",
                    'title': title,
                    'authors': authors,
                    'abstract': abstract,
                    'paper_url': url,
                    'pdf_url': pdf_url,
                    'published_date': published_date,
                    'updated_date': published_date,
                    'categories': [venue] if venue else [],
                    'subjects': [venue] if venue else [],
                    'venue': venue,
                    'metadata': {}
                }
                
        except Exception as e:
            logger.error(f"Error fetching ACL paper {paper_id}: {e}")
            return None
    
    async def fetch_latest(self, venue: str, date: Optional[datetime] = None) -> List[Dict]:
        """
        Fetch papers from ACL venue
        
        Args:
            venue: Venue identifier (e.g., "2023.acl")
            date: Not used
            
        Returns:
            List of paper metadata
        """
        await self._rate_limit_wait()
        
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                # Fetch venue page
                url = f"{self.base_url}/volumes/{venue}/"
                response = await client.get(url)
                response.raise_for_status()
                
                doc = pq(response.text)
                papers = []
                
                # Find all paper links
                for link in doc('p.d-sm-flex strong a').items():
                    paper_id = link.attr('href')
                    if paper_id:
                        # Remove leading slash
                        paper_id = paper_id.strip('/')
                        
                        # Fetch individual paper (could be optimized to parse from list)
                        paper = await self.fetch_paper(paper_id.replace('@ACL', ''))
                        if paper:
                            papers.append(paper)
                
                logger.info(f"Fetched {len(papers)} papers from ACL venue {venue}")
                return papers
                
        except Exception as e:
            logger.error(f"Error fetching ACL venue {venue}: {e}")
            return []
