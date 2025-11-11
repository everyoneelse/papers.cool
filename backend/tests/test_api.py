"""
Tests for API endpoints
"""
import pytest
from httpx import AsyncClient
from main import app


@pytest.mark.asyncio
async def test_root():
    """Test root endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'ok'
        assert 'app' in data


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'


@pytest.mark.asyncio
async def test_get_arxiv_paper():
    """Test getting ArXiv paper"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/papers/arxiv/2005.14165")
        assert response.status_code == 200
        data = response.json()
        assert 'title' in data
        assert 'authors' in data


@pytest.mark.asyncio
async def test_search():
    """Test search endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/search/?query=transformer&max_results=10")
        assert response.status_code == 200
        data = response.json()
        assert 'results' in data
        assert 'count' in data


@pytest.mark.asyncio
async def test_feed():
    """Test feed endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/feeds/arxiv/cs.AI")
        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/atom+xml; charset=utf-8'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
