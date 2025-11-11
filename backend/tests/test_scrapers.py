"""
Tests for paper scrapers
"""
import pytest
import asyncio
from scrapers import ArxivScraper, OpenReviewScraper


@pytest.mark.asyncio
async def test_arxiv_scraper_fetch_paper():
    """Test fetching a single ArXiv paper"""
    scraper = ArxivScraper()
    
    # Test with a well-known paper (GPT-3)
    paper = await scraper.fetch_paper("2005.14165")
    
    assert paper is not None
    assert paper['id'] == "2005.14165"
    assert "GPT" in paper['title'] or "Language Models" in paper['title']
    assert len(paper['authors']) > 0
    assert len(paper['abstract']) > 0
    assert paper['paper_url'].startswith("https://arxiv.org")
    assert paper['pdf_url'].endswith(".pdf")


@pytest.mark.asyncio
async def test_arxiv_scraper_fetch_latest():
    """Test fetching latest papers from category"""
    scraper = ArxivScraper()
    
    papers = await scraper.fetch_latest("cs.AI")
    
    assert len(papers) > 0
    assert all('id' in p for p in papers)
    assert all('title' in p for p in papers)
    assert all('authors' in p for p in papers)


@pytest.mark.asyncio
async def test_arxiv_scraper_search():
    """Test ArXiv search"""
    scraper = ArxivScraper()
    
    papers = await scraper.search_papers("transformer attention", max_results=10)
    
    assert len(papers) > 0
    assert len(papers) <= 10


@pytest.mark.asyncio
async def test_openreview_scraper():
    """Test OpenReview scraper"""
    scraper = OpenReviewScraper()
    
    # Note: This test may fail if the paper ID changes or is removed
    # You should replace with a valid OpenReview ID
    # paper = await scraper.fetch_paper("valid_openreview_id")
    # assert paper is not None
    
    # Just test that the scraper initializes correctly
    assert scraper.source_name == "openreview"
    assert scraper.api_url is not None


@pytest.mark.asyncio
async def test_arxiv_normalize_id():
    """Test ArXiv ID normalization"""
    scraper = ArxivScraper()
    
    # Old format (4 digits)
    assert scraper._normalize_arxiv_id("1301.3781") == "1301.03781"
    
    # New format (5 digits)
    assert scraper._normalize_arxiv_id("2401.12345") == "2401.12345"
    
    # With version
    assert scraper._normalize_arxiv_id("2401.12345v1") == "2401.12345"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
