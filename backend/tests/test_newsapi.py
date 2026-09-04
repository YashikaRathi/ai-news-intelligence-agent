import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.providers.news import NewsAPIProvider, RSSNewsProvider, get_news_provider
from app.services.ingestion import IngestionService

MOCK_NEWSAPI_EVERYTHING_RESPONSE = {
    "status": "ok",
    "totalResults": 2,
    "articles": [
        {
            "source": {"id": "techcrunch", "name": "TechCrunch"},
            "author": "Jane Doe",
            "title": "OpenAI Announces Next-Gen Reasoning Model",
            "description": "OpenAI unveiled its latest AI model featuring breakthrough capabilities.",
            "url": "https://techcrunch.com/2026/09/04/openai-next-gen-model/?utm_source=rss",
            "urlToImage": "https://techcrunch.com/wp-content/uploads/2026/09/ai-model.jpg",
            "publishedAt": "2026-09-04T18:30:00Z",
            "content": "Full article text content goes here..."
        },
        {
            "source": {"id": None, "name": "Reuters"},
            "author": "John Smith",
            "title": "Global Tech Summit Focuses on AI Regulation",
            "description": "World leaders gather to discuss AI safety frameworks.",
            "url": "https://reuters.com/technology/ai-summit-2026",
            "urlToImage": "https://reuters.com/images/summit.jpg",
            "publishedAt": "2026-09-04T12:00:00Z",
            "content": "Reuters report from the tech summit."
        },
        {
            "source": {"id": "removed", "name": "[Removed]"},
            "author": None,
            "title": "[Removed]",
            "description": "[Removed]",
            "url": "https://removed.com",
            "urlToImage": None,
            "publishedAt": "1970-01-01T00:00:00Z",
            "content": "[Removed]"
        }
    ]
}


@pytest.mark.asyncio
async def test_newsapi_provider_valid_response():
    """Test fetching and parsing valid NewsAPI response."""
    provider = NewsAPIProvider(api_key="mock_key")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_NEWSAPI_EVERYTHING_RESPONSE

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        articles = await provider.fetch_articles(topic="artificial intelligence", limit=10)

        # Removed article should be filtered out
        assert len(articles) == 2
        assert articles[0]["title"] == "OpenAI Announces Next-Gen Reasoning Model"
        assert articles[0]["source_name"] == "TechCrunch"
        assert articles[0]["image_url"] == "https://techcrunch.com/wp-content/uploads/2026/09/ai-model.jpg"
        assert articles[0]["published_at"] == "2026-09-04T18:30:00Z"

        assert articles[1]["title"] == "Global Tech Summit Focuses on AI Regulation"
        assert articles[1]["source_name"] == "Reuters"
        assert articles[1]["image_url"] == "https://reuters.com/images/summit.jpg"


@pytest.mark.asyncio
async def test_newsapi_normalization():
    """Test passing raw NewsAPI articles through IngestionService normalization."""
    provider = NewsAPIProvider(api_key="mock_key")
    ingestion = IngestionService()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_NEWSAPI_EVERYTHING_RESPONSE

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        raw_articles = await provider.fetch_articles(topic="AI", limit=5)

    normalized = [ingestion.normalize_article(raw) for raw in raw_articles]

    assert len(normalized) == 2
    # Check tracking parameter removal in canonical_url
    assert normalized[0]["canonical_url"] == "https://techcrunch.com/2026/09/04/openai-next-gen-model"
    assert normalized[0]["normalized_title"] == "openai announces nextgen reasoning model"
    assert normalized[0]["image_url"] == "https://techcrunch.com/wp-content/uploads/2026/09/ai-model.jpg"


@pytest.mark.asyncio
async def test_newsapi_empty_response_fallback():
    """Test that empty NewsAPI response gracefully falls back to RSS provider."""
    provider = NewsAPIProvider(api_key="mock_key")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "ok", "totalResults": 0, "articles": []}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        with patch.object(
            RSSNewsProvider,
            "fetch_articles",
            new_callable=AsyncMock,
            return_value=[{"title": "RSS Fallback Article", "url": "https://bbc.com/news/1"}]
        ) as mock_rss:
            articles = await provider.fetch_articles(topic="test", limit=5)
            assert len(articles) == 1
            assert articles[0]["title"] == "RSS Fallback Article"
            mock_rss.assert_called_once()


@pytest.mark.asyncio
async def test_newsapi_api_error_fallback():
    """Test that API key error (HTTP 401) causes automatic fallback to RSS."""
    provider = NewsAPIProvider(api_key="invalid_key")

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.json.return_value = {"status": "error", "code": "apiKeyInvalid", "message": "Your API key is invalid."}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        with patch.object(
            RSSNewsProvider,
            "fetch_articles",
            new_callable=AsyncMock,
            return_value=[{"title": "RSS Article After 401", "url": "https://rss.com/1"}]
        ) as mock_rss:
            articles = await provider.fetch_articles(topic="test", limit=5)
            assert len(articles) == 1
            assert articles[0]["title"] == "RSS Article After 401"
            mock_rss.assert_called_once()


@pytest.mark.asyncio
async def test_newsapi_missing_key_fallback(monkeypatch):
    """Test that missing API key instantly falls back to RSS without making HTTP call."""
    monkeypatch.delenv("NEWS_API_KEY", raising=False)
    provider = NewsAPIProvider(api_key="")

    with patch.object(
        RSSNewsProvider,
        "fetch_articles",
        new_callable=AsyncMock,
        return_value=[{"title": "RSS Article No Key", "url": "https://rss.com/2"}]
    ) as mock_rss:
        articles = await provider.fetch_articles(topic="test", limit=5)
        assert len(articles) == 1
        assert articles[0]["title"] == "RSS Article No Key"
        mock_rss.assert_called_once()



def test_provider_factory_selection(monkeypatch):
    """Test get_news_provider factory selection logic under different env configurations."""
    # 1. DEMO_MODE active
    monkeypatch.setenv("DEMO_MODE", "true")
    provider = get_news_provider()
    assert isinstance(provider, RSSNewsProvider)

    # 2. DEMO_MODE false, NEWS_PROVIDER=newsapi, NEWS_API_KEY valid
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("NEWS_PROVIDER", "newsapi")
    monkeypatch.setenv("NEWS_API_KEY", "test_key_123")
    provider = get_news_provider()
    assert isinstance(provider, NewsAPIProvider)
    assert provider.api_key == "test_key_123"

    # 3. DEMO_MODE false, NEWS_PROVIDER=newsapi, NEWS_API_KEY missing
    monkeypatch.delenv("NEWS_API_KEY", raising=False)
    provider = get_news_provider()
    assert isinstance(provider, RSSNewsProvider)

    # 4. DEMO_MODE false, NEWS_PROVIDER=rss
    monkeypatch.setenv("NEWS_PROVIDER", "rss")
    provider = get_news_provider()
    assert isinstance(provider, RSSNewsProvider)
