import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.providers.news import NewsAPIProvider, RSSNewsProvider

client = TestClient(app)

MOCK_NEPAL_FLOOD_NEWSAPI = {
    "status": "ok",
    "totalResults": 2,
    "articles": [
        {
            "source": {"id": "reuters", "name": "Reuters"},
            "author": "Kathmandu Bureau",
            "title": "Nepal Floods Force Thousands to Evacuate",
            "description": "Torrential monsoon rains have triggered severe flooding in southern Nepal.",
            "url": "https://reuters.com/world/asia-pacific/nepal-floods-2026",
            "urlToImage": "https://reuters.com/images/nepal-floods.jpg",
            "publishedAt": "2026-09-04T20:00:00Z",
            "content": "Full story on Nepal monsoon floods..."
        },
        {
            "source": {"id": "bbc-news", "name": "BBC News"},
            "author": "BBC Asia",
            "title": "Nepal Flood Crisis: Emergency Relief Operations Underway",
            "description": "Rescue teams deploy across affected districts in Nepal following flash floods.",
            "url": "https://bbc.com/news/world-asia-689123",
            "urlToImage": "https://bbc.com/images/rescue.jpg",
            "publishedAt": "2026-09-04T18:00:00Z",
            "content": "BBC report on Nepal disaster response..."
        }
    ]
}


def test_search_api_live_discovery():
    """Test searching for arbitrary topic 'Nepal flood' triggers NewsAPI live discovery and returns articles & stories."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_NEPAL_FLOOD_NEWSAPI

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        response = client.get("/api/search?q=Nepal%20flood")
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "Nepal flood"
        assert data["article_count"] > 0
        assert data["story_count"] > 0

        # Check article titles match
        titles = [a["title"] for a in data["articles"]]
        assert any("Nepal" in t for t in titles)


def test_search_api_empty_query():
    """Test searching with whitespace-only or empty query."""
    response = client.get("/api/search?q=%20%20")
    assert response.status_code == 200
    data = response.json()
    assert data["article_count"] == 0
    assert data["story_count"] == 0


def test_search_api_provider_fallback_on_error():
    """Test live search gracefully falls back to database/RSS search when provider encounters an exception."""
    with patch.object(
        NewsAPIProvider,
        "fetch_articles",
        new_callable=AsyncMock,
        side_effect=Exception("API limit exceeded")
    ):
        response = client.get("/api/search?q=OpenAI")
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "OpenAI"
        assert "articles" in data
        assert "stories" in data
