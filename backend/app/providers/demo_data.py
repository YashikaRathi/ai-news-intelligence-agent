from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

def get_demo_articles(topic: str = "artificial intelligence") -> List[Dict[str, Any]]:
    """Return deterministic sample RSS-style articles for DEMO_MODE or offline testing."""
    now = datetime.now(timezone.utc)
    
    raw_demo = [
        # Cluster 1: OpenAI GPT-5 Release
        {
            "title": "OpenAI Unveils Next-Gen AI Model GPT-5 with Enhanced Reasoning Capabilities",
            "description": "OpenAI has officially announced GPT-5, featuring breakthrough multi-modal reasoning and dynamic benchmark performance across scientific tasks.",
            "url": "https://techcrunch.com/2026/09/04/openai-unveils-gpt-5-reasoning-model/?utm_source=rss&utm_medium=feed",
            "source_name": "TechCrunch",
            "author": "Sarah Perez",
            "published_at": (now - timedelta(hours=6)).isoformat(),
            "image_url": "https://images.unsplash.com/photo-1677442136019-21780efad99a",
            "topic": "artificial intelligence"
        },
        {
            "title": "OpenAI announces new AI model GPT-5 with advanced reasoning",
            "description": "Artificial intelligence leader OpenAI introduced its latest frontier model, GPT-5, promising significant speedups and automated workflow execution.",
            "url": "https://www.bbc.com/news/technology-2026-gpt5-launch?fbclid=12345",
            "source_name": "BBC News",
            "author": "James Clayton",
            "published_at": (now - timedelta(hours=4)).isoformat(),
            "image_url": "https://images.unsplash.com/photo-1620712943543-bcc4688e7485",
            "topic": "artificial intelligence"
        },
        {
            "title": "OpenAI Unveils Next-Gen AI Model GPT-5 with Enhanced Reasoning Capabilities",
            "description": "Duplicate story published across syndicated media feed.",
            "url": "https://syndicated-news.net/openai-unveils-gpt-5-reasoning-model",
            "source_name": "Syndicated Tech",
            "author": "Staff Reporter",
            "published_at": (now - timedelta(hours=5)).isoformat(),
            "image_url": "https://images.unsplash.com/photo-1677442136019-21780efad99a",
            "topic": "artificial intelligence"
        },

        # Cluster 2: Global Semiconductor & Chip Manufacturing Breakthrough
        {
            "title": "TSMC Begins 1.4nm Chip Production to Power Next-Gen AI Hardware",
            "description": "Taiwan Semiconductor Manufacturing Company (TSMC) has commenced pilot risk production for its 1.4nm process node, targeting AI accelerator chips.",
            "url": "https://www.reuters.com/technology/tsmc-1-4nm-chip-production-ai-2026-09-04/?gclid=xyz987",
            "source_name": "Reuters",
            "author": "Yimou Lee",
            "published_at": (now - timedelta(hours=12)).isoformat(),
            "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475",
            "topic": "hardware"
        },
        {
            "title": "TSMC Starts 1.4nm Process Node for Future AI Processors",
            "description": "Semiconductor giant TSMC announced the initial fabrication phase for 1.4nm silicon designed for next-generation datacenter GPUs.",
            "url": "https://www.theguardian.com/technology/2026/sep/04/tsmc-chipmaking-1-4nm-ai-processors",
            "source_name": "The Guardian",
            "author": "Alex Hern",
            "published_at": (now - timedelta(hours=10)).isoformat(),
            "image_url": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b",
            "topic": "hardware"
        },

        # Cluster 3: Space Exploration / NASA Artemis Mission
        {
            "title": "NASA Artemis IV Mission Prepares for Lunar Base Gateway Assembly",
            "description": "NASA engineers have completed final launch readiness reviews for the Artemis IV mission to assemble the Gateway space station in lunar orbit.",
            "url": "https://www.npr.org/2026/09/04/nasa-artemis-iv-lunar-base-launch",
            "source_name": "NPR",
            "author": "Geoff Brumfiel",
            "published_at": (now - timedelta(hours=18)).isoformat(),
            "image_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa",
            "topic": "space"
        },
        {
            "title": "NASA Prepares Artemis IV Mission for Moon Gateway Assembly",
            "description": "Astronauts and ground crews at Kennedy Space Center enter final simulation phase ahead of Artemis IV lunar orbit deployment.",
            "url": "https://news.google.com/articles/nasa-artemis-4-moon-gateway-prep",
            "source_name": "Google News / Space",
            "author": "NASA Press",
            "published_at": (now - timedelta(hours=15)).isoformat(),
            "image_url": "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa",
            "topic": "space"
        }
    ]

    import re
    topic_clean = topic.strip().lower()
    if not topic_clean or topic_clean in ["general", "all", "news"]:
        return raw_demo

    topic_words = [w for w in re.split(r'\W+', topic_clean) if len(w) > 2]

    filtered = []
    for a in raw_demo:
        combined = f"{a['title']} {a.get('description', '')} {a.get('topic', '')}".lower()
        if topic_clean in combined:
            filtered.append(a)
        elif topic_words and any(w in combined for w in topic_words):
            filtered.append(a)

    return filtered
