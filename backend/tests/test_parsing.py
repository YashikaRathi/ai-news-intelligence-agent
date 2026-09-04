import pytest
from unittest.mock import AsyncMock, patch
from app.providers.news import RSSNewsProvider

@pytest.mark.asyncio
async def test_rss_feed_parsing_fallback():
    provider = RSSNewsProvider()
    
    # Enable DEMO_MODE for deterministic test execution
    with patch.dict("os.environ", {"DEMO_MODE": "true"}):
        articles = await provider.fetch_articles(topic="artificial intelligence", limit=10)
        assert isinstance(articles, list)
        assert len(articles) > 0
        first = articles[0]
        assert "title" in first
        assert "url" in first
        assert "source_name" in first
        assert "published_at" in first
