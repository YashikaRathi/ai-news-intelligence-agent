import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.db.session import engine
from app.providers.llm import DemoLLMProvider, get_llm_provider

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db_and_enable_demo_mode():
    """Autouse fixture ensuring clean DB tables and DEMO_MODE=true for offline test execution."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with patch.dict("os.environ", {"DEMO_MODE": "true"}):
        yield


@pytest.mark.asyncio
async def test_demo_llm_provider_story_intelligence():
    provider = DemoLLMProvider()
    headline = "OpenAI Unveils GPT-5"
    topic = "artificial intelligence"
    articles = [
        {
            "id": "art_1",
            "title": "OpenAI Unveils GPT-5",
            "description": "Breakthrough multi-modal model announced.",
            "source_name": "TechCrunch",
            "url": "https://techcrunch.com/gpt5",
            "published_at": "2026-09-04T12:00:00Z"
        },
        {
            "id": "art_2",
            "title": "OpenAI announces new AI model GPT-5",
            "description": "Updated announcement from BBC.",
            "source_name": "BBC News",
            "url": "https://bbc.com/gpt5",
            "published_at": "2026-09-04T14:00:00Z"
        }
    ]

    res = await provider.analyze_story_intelligence(headline, topic, articles)

    assert res["is_demo"] is True
    assert "what_happened" in res
    assert "what_changed" in res
    assert "why_it_matters" in res
    assert len(res["evidence"]) == 2
    assert len(res["source_comparison"]) == 2
    assert res["evidence"][0]["article_id"] == "art_1"


@pytest.mark.asyncio
async def test_rag_question_answering():
    provider = DemoLLMProvider()
    context_articles = [
        {
            "id": "art_100",
            "title": "TSMC Begins 1.4nm Process Node",
            "description": "TSMC has commenced pilot risk production for 1.4nm chips for AI hardware.",
            "source_name": "Reuters",
            "url": "https://reuters.com/tsmc-14nm"
        }
    ]

    # Test grounded Q&A
    res = await provider.answer_rag_question("What process node is TSMC starting?", context_articles)
    assert "1.4nm" in res["answer"] or "TSMC" in res["answer"]
    assert len(res["sources"]) > 0

    # Test missing evidence handling
    empty_res = await provider.answer_rag_question("What is the temperature on Mars?", [])
    assert empty_res["answer"] == "I couldn't find enough evidence in the available coverage to answer that reliably."
    assert len(empty_res["sources"]) == 0


def test_story_intelligence_api():
    # Ingest news first
    client.get("/api/news?limit=10")
    stories_res = client.get("/api/stories")
    stories = stories_res.json()
    assert len(stories) > 0

    target_story_id = stories[0]["id"]

    # Test GET /api/ai/stories/{story_id}/intelligence
    intel_res = client.get(f"/api/ai/stories/{target_story_id}/intelligence")
    assert intel_res.status_code == 200
    intel_data = intel_res.json()

    assert intel_data["story_id"] == target_story_id
    assert "what_happened" in intel_data
    assert "what_changed" in intel_data
    assert "why_it_matters" in intel_data
    assert "evidence" in intel_data
    assert isinstance(intel_data["evidence"], list)
    assert "source_comparison" in intel_data
    assert isinstance(intel_data["source_comparison"], list)
    assert intel_data["is_demo"] is True


def test_ai_chat_api():
    # Ingest news first
    client.get("/api/news?limit=10")
    stories_res = client.get("/api/stories")
    stories = stories_res.json()
    target_story_id = stories[0]["id"]

    # Test POST /api/ai/chat with story_id
    chat_payload = {
        "story_id": target_story_id,
        "question": "What is the key development in this story?"
    }
    chat_res = client.post("/api/ai/chat", json=chat_payload)
    assert chat_res.status_code == 200
    chat_data = chat_res.json()

    assert "answer" in chat_data
    assert "sources" in chat_data
    assert isinstance(chat_data["sources"], list)
    assert chat_data["is_demo"] is True


def test_ai_summarize_api():
    # Ingest news first
    client.get("/api/news?limit=10")

    sum_res = client.post("/api/ai/summarize", json={})
    assert sum_res.status_code == 200
    sum_data = sum_res.json()
    assert "what_happened" in sum_data
    assert "evidence" in sum_data


@pytest.mark.asyncio
async def test_different_questions_produce_different_answers():
    provider = DemoLLMProvider()
    articles = [
        {
            "id": "art_1",
            "title": "Nepal Flood Crisis: Emergency Operations Underway",
            "description": "Rescue teams deploy across affected districts.",
            "source_name": "BBC News",
            "url": "https://bbc.com/news/nepal-1",
            "published_at": "2026-09-04T10:00:00Z"
        },
        {
            "id": "art_2",
            "title": "Death Toll Rises in Nepal Flash Floods",
            "description": "Updated report on casualty count and aid distribution.",
            "source_name": "Reuters",
            "url": "https://reuters.com/nepal-2",
            "published_at": "2026-09-04T15:00:00Z"
        }
    ]

    q1_resp = await provider.answer_rag_question("What is the latest development?", articles)
    q2_resp = await provider.answer_rag_question("Why is this important?", articles)
    q3_resp = await provider.answer_rag_question("What changed from earlier reports?", articles)
    q4_resp = await provider.answer_rag_question("Which sources reported this?", articles)
    q5_resp = await provider.answer_rag_question("What could happen next?", articles)

    ans1 = q1_resp["answer"]
    ans2 = q2_resp["answer"]
    ans3 = q3_resp["answer"]
    ans4 = q4_resp["answer"]
    ans5 = q5_resp["answer"]

    # All answers must be distinct and non-empty
    assert ans1 != ans2
    assert ans2 != ans3
    assert ans3 != ans4
    assert ans4 != ans5

    # Check question-specific keywords
    assert "LATEST DEVELOPMENT" in ans1
    assert "SIGNIFICANCE & IMPACT" in ans2
    assert "TIMELINE SHIFT" in ans3
    assert "SOURCE COVERAGE SUMMARY" in ans4
    assert "predict" in ans5 or "future" in ans5

    # Verify exact stored URLs in sources
    urls = [s["url"] for s in q1_resp["sources"]]
    assert "https://bbc.com/news/nepal-1" in urls
    assert "https://reuters.com/nepal-2" in urls

    # Verify deduplication
    assert len(q1_resp["sources"]) == 2

