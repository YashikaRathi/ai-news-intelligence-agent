from datetime import datetime, timedelta, timezone
from app.services.clustering import ClusteringService

def test_story_timeline_ordering():
    service = ClusteringService()
    now = datetime.now(timezone.utc)

    art_earlier = {
        "id": "art_earlier",
        "title": "TSMC Begins 1.4nm Chip Production",
        "normalized_title": "tsmc begins 14nm chip production",
        "published_at": (now - timedelta(hours=10)).isoformat(),
        "topic": "hardware"
    }

    art_later = {
        "id": "art_later",
        "title": "TSMC Starts 1.4nm Process Node for Future AI Processors",
        "normalized_title": "tsmc starts 14nm process node for future ai processors",
        "published_at": (now - timedelta(hours=2)).isoformat(),
        "topic": "hardware"
    }

    clustered, stories = service.cluster_articles([art_earlier, art_later], [])
    
    assert len(stories) == 1
    story = stories[0]
    assert story["earliest_published_at"] < story["latest_published_at"]
