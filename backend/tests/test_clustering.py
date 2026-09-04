from datetime import datetime, timezone
from app.services.clustering import ClusteringService

def test_story_clustering():
    service = ClusteringService(similarity_threshold=0.35)

    now = datetime.now(timezone.utc)
    articles = [
        {
            "id": "art_1",
            "title": "OpenAI Unveils Next-Gen AI Model GPT-5",
            "normalized_title": "openai unveils nextgen ai model gpt5",
            "description": "OpenAI announces GPT-5 with enhanced reasoning.",
            "topic": "AI",
            "published_at": now.isoformat()
        },
        {
            "id": "art_2",
            "title": "OpenAI announces new AI model GPT-5 with advanced reasoning",
            "normalized_title": "openai announces new ai model gpt5 with advanced reasoning",
            "description": "Artificial intelligence leader OpenAI introduced GPT-5.",
            "topic": "AI",
            "published_at": now.isoformat()
        },
        {
            "id": "art_3",
            "title": "NASA Artemis IV Mission Prepares for Lunar Launch",
            "normalized_title": "nasa artemis iv mission prepares for lunar launch",
            "description": "NASA engineers prepare Artemis IV mission.",
            "topic": "Space",
            "published_at": now.isoformat()
        }
    ]

    clustered_articles, stories = service.cluster_articles(articles, [])

    assert len(stories) == 2  # 2 distinct stories: OpenAI GPT-5 & NASA Artemis IV
    
    # Check that art_1 and art_2 share the same story_id
    art1_obj = next(a for a in clustered_articles if a["id"] == "art_1")
    art2_obj = next(a for a in clustered_articles if a["id"] == "art_2")
    art3_obj = next(a for a in clustered_articles if a["id"] == "art_3")

    assert art1_obj["story_id"] == art2_obj["story_id"]
    assert art1_obj["story_id"] != art3_obj["story_id"]
