"""
Scrapers package for fetching papers from various sources
"""
from .arxiv_scraper import ArxivScraper
from .openreview_scraper import OpenReviewScraper
from .acl_scraper import ACLScraper

__all__ = ['ArxivScraper', 'OpenReviewScraper', 'ACLScraper']
