import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.db.base import Base
from app.db.session import engine

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db_and_enable_demo_mode():
    """Autouse fixture re-creating DB tables and enabling DEMO_MODE for clean offline test runs."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with patch.dict("os.environ", {"DEMO_MODE": "true"}):
        yield

def test_health_api():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "sqlite"


def test_news_ingestion_api():
    response = client.get("/api/news?topic=artificial%20intelligence&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    article = data[0]
    assert "id" in article
    assert "title" in article
    assert "url" in article
    assert "source_name" in article


def test_stories_api():
    # Trigger news endpoint first to populate database
    client.get("/api/news?limit=10")

    response = client.get("/api/stories")
    assert response.status_code == 200
    stories = response.json()
    assert isinstance(stories, list)
    assert len(stories) > 0

    target_story = stories[0]
    story_id = target_story["id"]

    # Test GET /stories/{story_id}
    detail_res = client.get(f"/api/stories/{story_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["id"] == story_id

    # Test GET /stories/{story_id}/timeline
    timeline_res = client.get(f"/api/stories/{story_id}/timeline")
    assert timeline_res.status_code == 200
    timeline_data = timeline_res.json()
    assert timeline_data["story_id"] == story_id
    assert "timeline" in timeline_data
    assert isinstance(timeline_data["timeline"], list)


def test_search_api():
    # Trigger news endpoint first to populate database
    client.get("/api/news?limit=10")

    response = client.get("/api/search?q=OpenAI")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "OpenAI"
    assert "articles" in data
    assert "stories" in data
