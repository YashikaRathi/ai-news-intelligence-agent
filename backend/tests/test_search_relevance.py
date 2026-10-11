import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from app.main import app
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models.article import Article
from app.models.story import Story
from app.services.search import SearchService

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_search_test_data():
    """Populate database with a rich set of realistic articles to test search relevance and regression safety."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Story 1: Nepal Floods
    s_nepal = Story(
        id="story_nepal_1",
        title="Nepal Floods Force Evacuations Across Southern Districts",
        summary="Monsoon rains trigger flash floods and emergency operations across Nepal.",
        topic="Natural Disasters",
        category="Disaster",
        first_seen=now - timedelta(days=2),
        last_updated=now - timedelta(days=1),
        article_count=2,
    )

    # Story 2: OpenAI GPT-5
    s_ai = Story(
        id="story_ai_1",
        title="OpenAI Releases Frontier Model GPT-5",
        summary="OpenAI announces GPT-5 model with advanced reasoning capabilities and benchmarks.",
        topic="Artificial Intelligence",
        category="Technology",
        first_seen=now - timedelta(days=3),
        last_updated=now - timedelta(hours=5),
        article_count=3,
    )

    # Story 3: TSMC Chipmaking
    s_tsmc = Story(
        id="story_tsmc_1",
        title="TSMC Starts 1.4nm Chip Production for AI Accelerators",
        summary="Semiconductor foundry TSMC begins risk fabrication for 1.4nm silicon.",
        topic="Hardware",
        category="Semiconductors",
        first_seen=now - timedelta(days=4),
        last_updated=now - timedelta(days=2),
        article_count=1,
    )

    db.add_all([s_nepal, s_ai, s_tsmc])

    # Article 1: Nepal Floods (Reuters)
    a1 = Article(
        id="art_nepal_reuters",
        title="Nepal Floods Force Thousands to Evacuate",
        normalized_title="nepal floods force thousands to evacuate",
        description="Torrential monsoon rains have triggered severe flooding in southern Nepal.",
        url="https://reuters.com/nepal-floods-2026",
        canonical_url="https://reuters.com/nepal-floods-2026",
        source_name="Reuters",
        author="Kathmandu Bureau",
        published_at=now - timedelta(days=2),
        topic="Natural Disasters",
        story_id="story_nepal_1",
        is_duplicate=False
    )

    # Article 2: Nepal Flood Relief (BBC)
    a2 = Article(
        id="art_nepal_bbc",
        title="Nepal Flood Crisis: Emergency Relief Operations Underway",
        normalized_title="nepal flood crisis emergency relief operations underway",
        description="Rescue teams deploy across affected districts in Nepal following flash floods.",
        url="https://bbc.com/nepal-rescue-2026",
        canonical_url="https://bbc.com/nepal-rescue-2026",
        source_name="BBC News",
        author="BBC Asia",
        published_at=now - timedelta(days=1),
        topic="Natural Disasters",
        story_id="story_nepal_1",
        is_duplicate=False
    )

    # Article 3: OpenAI GPT-5 (TechCrunch, Sarah Perez)
    a3 = Article(
        id="art_ai_tc",
        title="OpenAI Unveils Next-Gen AI Model GPT-5 with Enhanced Reasoning Capabilities",
        normalized_title="openai unveils nextgen ai model gpt5 with enhanced reasoning capabilities",
        description="OpenAI officially announced GPT-5, featuring breakthrough multi-modal reasoning.",
        url="https://techcrunch.com/openai-gpt5",
        canonical_url="https://techcrunch.com/openai-gpt5",
        source_name="TechCrunch",
        author="Sarah Perez",
        published_at=now - timedelta(hours=6),
        topic="Artificial Intelligence",
        story_id="story_ai_1",
        is_duplicate=False
    )

    # Article 4: OpenAI GPT-5 (BBC)
    a4 = Article(
        id="art_ai_bbc",
        title="OpenAI announces new AI model GPT-5 with advanced reasoning",
        normalized_title="openai announces new ai model gpt5 with advanced reasoning",
        description="Artificial intelligence leader OpenAI introduced its latest frontier model.",
        url="https://bbc.com/gpt5-launch",
        canonical_url="https://bbc.com/gpt5-launch",
        source_name="BBC News",
        author="James Clayton",
        published_at=now - timedelta(hours=4),
        topic="Artificial Intelligence",
        story_id="story_ai_1",
        is_duplicate=False
    )

    # Article 5: Syndicated Duplicate of Article 3
    a5 = Article(
        id="art_ai_dup",
        title="OpenAI Unveils Next-Gen AI Model GPT-5 with Enhanced Reasoning Capabilities",
        normalized_title="openai unveils nextgen ai model gpt5 with enhanced reasoning capabilities",
        description="Duplicate syndication feed copy.",
        url="https://syndicated.net/openai-gpt5",
        canonical_url="https://syndicated.net/openai-gpt5",
        source_name="Syndicated Tech",
        author="Staff Reporter",
        published_at=now - timedelta(hours=5),
        topic="Artificial Intelligence",
        story_id="story_ai_1",
        is_duplicate=True,
        duplicate_of_id="art_ai_tc"
    )

    # Article 6: TSMC 1.4nm
    a6 = Article(
        id="art_tsmc_reuters",
        title="TSMC Begins 1.4nm Chip Production to Power Next-Gen AI Hardware",
        normalized_title="tsmc begins 14nm chip production to power nextgen ai hardware",
        description="Taiwan Semiconductor Manufacturing Company (TSMC) pilot risk fabrication for 1.4nm node.",
        url="https://reuters.com/tsmc-14nm",
        canonical_url="https://reuters.com/tsmc-14nm",
        source_name="Reuters",
        author="Yimou Lee",
        published_at=now - timedelta(days=2),
        topic="Hardware",
        story_id="story_tsmc_1",
        is_duplicate=False
    )

    db.add_all([a1, a2, a3, a4, a5, a6])
    db.commit()
    db.close()

    mock_provider = MagicMock()
    mock_provider.fetch_articles = AsyncMock(return_value=[])
    with patch("app.api.search.get_news_provider", return_value=mock_provider), \
         patch.dict("os.environ", {"DEMO_MODE": "true"}):
        yield


def test_exact_article_title_search():
    """Exact article-title search must rank the exact matching article at #1."""
    response = client.get("/api/search?q=Nepal%20Floods%20Force%20Thousands%20to%20Evacuate")
    assert response.status_code == 200
    data = response.json()
    assert data["article_count"] >= 1
    top_article = data["articles"][0]
    assert top_article["id"] == "art_nepal_reuters"
    assert top_article["title"] == "Nepal Floods Force Thousands to Evacuate"


def test_substring_immunity_for_acronym_ai():
    """Searching for 'AI' must NOT match 'rains' in the Nepal Floods article description."""
    response = client.get("/api/search?q=AI")
    assert response.status_code == 200
    data = response.json()
    assert data["article_count"] >= 1

    # Verify every returned article genuinely relates to AI
    for art in data["articles"]:
        assert "Nepal" not in art["title"]
        assert "Floods" not in art["title"]
        assert any(term in (art["title"] + " " + art["description"]).lower() for term in ["ai", "gpt", "model", "artificial"])


def test_author_search():
    """Searching for an author's name must return articles written by that author."""
    response = client.get("/api/search?q=Sarah%20Perez")
    assert response.status_code == 200
    data = response.json()
    assert data["article_count"] >= 1
    assert data["articles"][0]["id"] == "art_ai_tc"
    assert data["articles"][0]["author"] == "Sarah Perez"


def test_organization_and_source_search():
    """Searching for an organization or source name must prioritize that publisher."""
    response = client.get("/api/search?q=Kathmandu%20Bureau")
    assert response.status_code == 200
    data = response.json()
    assert data["article_count"] >= 1
    assert data["articles"][0]["id"] == "art_nepal_reuters"


def test_multiword_topic_conjunction():
    """Multiword search for 'Nepal floods emergency' returns matching event articles."""
    response = client.get("/api/search?q=Nepal%20floods%20emergency")
    assert response.status_code == 200
    data = response.json()
    assert data["article_count"] >= 1
    # Both Nepal articles should be found, AI articles should not be included
    for art in data["articles"]:
        assert "Nepal" in art["title"]


def test_case_and_punctuation_insensitivity():
    """Queries with uppercase, lowercase, or punctuation must return the same relevant results."""
    res_lower = client.get("/api/search?q=nepal%20flood").json()
    res_upper = client.get("/api/search?q=NEPAL%20FLOOD").json()
    res_punct = client.get("/api/search?q=Nepal%20Flood!").json()

    assert res_lower["article_count"] == res_upper["article_count"] == res_punct["article_count"]
    titles_lower = [a["title"] for a in res_lower["articles"]]
    titles_upper = [a["title"] for a in res_upper["articles"]]
    titles_punct = [a["title"] for a in res_punct["articles"]]
    assert titles_lower == titles_upper == titles_punct


def test_duplicate_articles_not_crowding_results():
    """Syndicated duplicate copies (is_duplicate=True) must not be returned in search results."""
    response = client.get("/api/search?q=OpenAI%20GPT-5")
    assert response.status_code == 200
    data = response.json()
    returned_ids = [a["id"] for a in data["articles"]]
    assert "art_ai_dup" not in returned_ids
    assert "art_ai_tc" in returned_ids


def test_unrelated_query_returns_clean_zero_results():
    """Queries with no relevance must return article_count == 0 instead of unrelated popular articles."""
    response = client.get("/api/search?q=quantum%20cooking%20recipe")
    assert response.status_code == 200
    data = response.json()
    assert data["article_count"] == 0
    assert data["story_count"] == 0
    assert len(data["articles"]) == 0
    assert len(data["stories"]) == 0


def test_story_clusters_ranked_by_relevance():
    """Story clusters must be ranked by relevance, with the exact headline cluster at #1."""
    response = client.get("/api/search?q=TSMC%201.4nm%20chip")
    assert response.status_code == 200
    data = response.json()
    assert data["story_count"] >= 1
    assert data["stories"][0]["id"] == "story_tsmc_1"
