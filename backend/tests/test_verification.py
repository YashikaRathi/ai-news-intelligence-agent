import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.db.session import engine
from app.services.verification import VerificationService

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db_and_enable_demo_mode():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with patch.dict("os.environ", {"DEMO_MODE": "true"}):
        yield


def test_verification_service_unit():
    service = VerificationService()
    
    articles = [
        {
            "id": "a1",
            "title": "Major breakthrough in quantum computing announced",
            "description": "Tech giant achieves quantum supremacy benchmark.",
            "source_name": "Reuters",
            "url": "https://reuters.com/quantum"
        },
        {
            "id": "a2",
            "title": "Quantum computing milestone reached",
            "description": "BBC reports on new quantum hardware.",
            "source_name": "BBC News",
            "url": "https://bbc.com/quantum"
        },
        {
            "id": "a3",
            "title": "New quantum chip tested in lab",
            "description": "TechCrunch analysis of quantum chip architecture.",
            "source_name": "TechCrunch",
            "url": "https://techcrunch.com/quantum"
        }
    ]

    res = service.verify_story("s123", "Major breakthrough in quantum computing", articles)

    assert res.story_id == "s123"
    assert res.trust_score.score >= 80
    assert res.trust_score.corroboration_score >= 85
    assert len(res.publisher_credibility) == 3
    assert len(res.claim_checks) > 0
    assert res.total_sources == 3
    assert res.total_articles == 3


def test_verification_api_endpoint():
    # Ingest news first
    client.get("/api/news?limit=10")
    stories_res = client.get("/api/stories")
    stories = stories_res.json()
    assert len(stories) > 0

    target_story_id = stories[0]["id"]

    # Test GET /api/ai/stories/{story_id}/verification
    ver_res = client.get(f"/api/ai/stories/{target_story_id}/verification")
    assert ver_res.status_code == 200
    ver_data = ver_res.json()

    assert ver_data["story_id"] == target_story_id
    assert "trust_score" in ver_data
    assert "publisher_credibility" in ver_data
    assert "claim_checks" in ver_data
    assert ver_data["trust_score"]["score"] >= 0
