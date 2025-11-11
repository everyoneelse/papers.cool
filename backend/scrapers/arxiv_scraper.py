"""
ArXiv paper scraper
"""
import re
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import httpx
from pyquery import PyQuery as pq
from loguru import logger

from .base_scraper import BaseScraper
from config import settings


class ArxivScraper(BaseScraper):
    """Scraper for ArXiv papers"""
    
    def __init__(self):
        super().__init__(rate_limit=settings.ARXIV_RATE_LIMIT)
        self.base_url = settings.ARXIV_BASE_URL
        self.api_url = settings.ARXIV_API_URL
        
    @property
    def source_name(self) -> str:
        return "arxiv"
    
    def _normalize_arxiv_id(self, arxiv_id: str) -> str:
        """Normalize ArXiv ID to standard format"""
        # Handle old format (e.g., 1301.3781) and new format (e.g., 2401.12345)
        match = re.search(r'(\d{4})\.(\d{4,5})', arxiv_id)
        if match:
            year_month, num = match.groups()
            # Pad to 5 digits
            return f"{year_month}.{num.zfill(5)}"
        return arxiv_id
    
    async def fetch_paper(self, paper_id: str) -> Optional[Dict]:
        """
        Fetch a single ArXiv paper by ID
        
        Args:
            paper_id: ArXiv ID (e.g., "2401.12345")
            
        Returns:
            Paper metadata or None
        """
        paper_id = self._normalize_arxiv_id(paper_id)
        await self._rate_limit_wait()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Use ArXiv API
                params = {
                    'id_list': paper_id,
                    'max_results': 1
                }
                response = await client.get(self.api_url, params=params)
                response.raise_for_status()
                
                # Parse XML response
                root = ET.fromstring(response.text)
                ns = {'atom': 'http://www.w3.org/2005/Atom',
                      'arxiv': 'http://arxiv.org/schemas/atom'}
                
                entry = root.find('atom:entry', ns)
                if entry is None:
                    logger.warning(f"Paper {paper_id} not found in ArXiv API")
                    return None
                
                # Extract data
                title = entry.find('atom:title', ns)
                summary = entry.find('atom:summary', ns)
                published = entry.find('atom:published', ns)
                updated = entry.find('atom:updated', ns)
                
                authors = []
                for author in entry.findall('atom:author', ns):
                    name = author.find('atom:name', ns)
                    if name is not None:
                        authors.append(name.text)
                
                categories = []
                for category in entry.findall('atom:category', ns):
                    term = category.get('term')
                    if term:
                        categories.append(term)
                
                # Get URLs
                pdf_url = None
                paper_url = None
                for link in entry.findall('atom:link', ns):
                    if link.get('type') == 'application/pdf':
                        pdf_url = link.get('href')
                    elif link.get('type') == 'text/html':
                        paper_url = link.get('href')
                
                if not paper_url:
                    paper_url = f"{self.base_url}/abs/{paper_id}"
                if not pdf_url:
                    pdf_url = f"{self.base_url}/pdf/{paper_id}.pdf"
                
                return {
                    'id': paper_id,
                    'title': title.text.strip() if title is not None else '',
                    'authors': authors,
                    'abstract': summary.text.strip() if summary is not None else '',
                    'paper_url': paper_url,
                    'pdf_url': pdf_url,
                    'published_date': datetime.fromisoformat(published.text.replace('Z', '+00:00')) if published is not None else None,
                    'updated_date': datetime.fromisoformat(updated.text.replace('Z', '+00:00')) if updated is not None else None,
                    'categories': categories,
                    'subjects': categories,
                    'venue': None,
                    'metadata': {}
                }
                
        except Exception as e:
            logger.error(f"Error fetching ArXiv paper {paper_id}: {e}")
            return None
    
    async def fetch_latest(self, category: str, date: Optional[datetime] = None) -> List[Dict]:
        """
        Fetch latest papers for an ArXiv category
        
        Args:
            category: ArXiv category (e.g., "cs.AI")
            date: Target date (defaults to latest)
            
        Returns:
            List of paper metadata
        """
        if date is None:
            date = datetime.now()
        
        await self._rate_limit_wait()
        
        try:
            # Format date for ArXiv list URL
            date_str = date.strftime('%y%m')
            
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                # Fetch the list page
                url = f"{self.base_url}/list/{category}/{date_str}?skip=0&show=2000"
                response = await client.get(url)
                response.raise_for_status()
                
                # Parse HTML with PyQuery
                doc = pq(response.text)
                
                papers = []
                
                # Find all paper entries
                # ArXiv list format: <dt> contains metadata, <dd> contains title/authors
                dts = doc('#articles dt')
                dds = doc('#articles dd')
                
                for dt, dd in zip(dts.items(), dds.items()):
                    try:
                        # Extract paper ID
                        arxiv_id_elem = dt('a[title="Abstract"]')
                        if not arxiv_id_elem:
                            continue
                        
                        paper_id = arxiv_id_elem.attr('id')
                        if not paper_id:
                            continue
                        
                        paper_id = self._normalize_arxiv_id(paper_id)
                        
                        # Extract title
                        title_elem = dd('.list-title')
                        title = title_elem.text().replace('Title:', '').strip() if title_elem else ''
                        
                        # Extract authors
                        authors_elem = dd('.list-authors')
                        authors = []
                        if authors_elem:
                            author_links = authors_elem('a')
                            authors = [pq(a).text().strip() for a in author_links]
                        
                        # Extract subjects/categories
                        subjects_elem = dd('.list-subjects')
                        subjects = []
                        if subjects_elem:
                            subjects_text = subjects_elem.text().replace('Subjects:', '').strip()
                            subjects = [s.strip() for s in subjects_text.split(';')]
                        
                        # Get abstract (requires additional request, skip for list view)
                        # We'll fetch it when individual paper is accessed
                        
                        paper_url = f"{self.base_url}/abs/{paper_id}"
                        pdf_url = f"{self.base_url}/pdf/{paper_id}.pdf"
                        
                        papers.append({
                            'id': paper_id,
                            'title': title,
                            'authors': authors,
                            'abstract': '',  # Fetch separately if needed
                            'paper_url': paper_url,
                            'pdf_url': pdf_url,
                            'published_date': date,
                            'updated_date': date,
                            'categories': subjects,
                            'subjects': subjects,
                            'venue': None,
                            'metadata': {}
                        })
                        
                    except Exception as e:
                        logger.error(f"Error parsing paper entry: {e}")
                        continue
                
                logger.info(f"Fetched {len(papers)} papers from ArXiv {category} for {date_str}")
                return papers
                
        except Exception as e:
            logger.error(f"Error fetching ArXiv list for {category}: {e}")
            return []
    
    async def fetch_category_papers(self, categories: List[str], exclude_categories: List[str] = None,
                                   date: Optional[datetime] = None) -> List[Dict]:
        """
        Fetch papers matching multiple categories with exclusions
        
        Args:
            categories: List of categories to include (OR logic)
            exclude_categories: List of categories to exclude
            date: Target date
            
        Returns:
            List of paper metadata
        """
        if exclude_categories is None:
            exclude_categories = []
        
        # Fetch all papers from included categories
        all_papers = []
        seen_ids = set()
        
        for category in categories:
            papers = await self.fetch_latest(category, date)
            for paper in papers:
                paper_id = paper['id']
                if paper_id not in seen_ids:
                    # Check if any excluded category is in paper's categories
                    paper_cats = set(paper.get('categories', []))
                    excluded = any(exc in paper_cats for exc in exclude_categories)
                    
                    if not excluded:
                        all_papers.append(paper)
                        seen_ids.add(paper_id)
        
        return all_papers
    
    async def search_papers(self, query: str, max_results: int = 100) -> List[Dict]:
        """
        Search ArXiv papers by query
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            List of paper metadata
        """
        await self._rate_limit_wait()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {
                    'search_query': f'all:{query}',
                    'start': 0,
                    'max_results': max_results,
                    'sortBy': 'relevance',
                    'sortOrder': 'descending'
                }
                
                response = await client.get(self.api_url, params=params)
                response.raise_for_status()
                
                # Parse XML response
                root = ET.fromstring(response.text)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                
                papers = []
                for entry in root.findall('atom:entry', ns):
                    # Extract paper ID from URL
                    id_elem = entry.find('atom:id', ns)
                    if id_elem is not None:
                        paper_id = id_elem.text.split('/abs/')[-1]
                        paper_id = self._normalize_arxiv_id(paper_id)
                        
                        title = entry.find('atom:title', ns)
                        summary = entry.find('atom:summary', ns)
                        published = entry.find('atom:published', ns)
                        
                        authors = []
                        for author in entry.findall('atom:author', ns):
                            name = author.find('atom:name', ns)
                            if name is not None:
                                authors.append(name.text)
                        
                        categories = []
                        for category in entry.findall('atom:category', ns):
                            term = category.get('term')
                            if term:
                                categories.append(term)
                        
                        papers.append({
                            'id': paper_id,
                            'title': title.text.strip() if title is not None else '',
                            'authors': authors,
                            'abstract': summary.text.strip() if summary is not None else '',
                            'paper_url': f"{self.base_url}/abs/{paper_id}",
                            'pdf_url': f"{self.base_url}/pdf/{paper_id}.pdf",
                            'published_date': datetime.fromisoformat(published.text.replace('Z', '+00:00')) if published is not None else None,
                            'categories': categories,
                            'subjects': categories,
                        })
                
                return papers
                
        except Exception as e:
            logger.error(f"Error searching ArXiv: {e}")
            return []
