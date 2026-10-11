import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from app.services.deduplication import DeduplicationService

class ClusteringService:
    """Service responsible for story clustering of related news articles into story events."""

    def __init__(self, similarity_threshold: float = 0.30):
        self.similarity_threshold = similarity_threshold
        self.dedup_service = DeduplicationService()



    @staticmethod
    def _to_naive_datetime(dt_val: Any) -> Optional[datetime]:
        """Convert datetime or ISO string to naive UTC datetime for consistent SQLite comparisons."""
        if dt_val is None:
            return None
        if isinstance(dt_val, str):
            clean_str = dt_val.strip()
            if not clean_str:
                return None
            try:
                dt = datetime.fromisoformat(clean_str.replace("Z", "+00:00"))
                if dt.tzinfo is not None:
                    dt = dt.astimezone(timezone.utc)
                return dt.replace(tzinfo=None)
            except Exception:
                return None
        if isinstance(dt_val, datetime):
            if dt_val.tzinfo is not None:
                dt_val = dt_val.astimezone(timezone.utc)
            return dt_val.replace(tzinfo=None)
        return None

    def compute_story_similarity(self, article: Dict[str, Any], story: Dict[str, Any]) -> float:
        """Calculate similarity between an article and a story's representative title and content."""
        art_text = f"{article.get('title', '')} {article.get('description', '')}"
        story_text = f"{story.get('title', '')} {story.get('summary', '')}"

        # Title similarity score
        title_sim = self.dedup_service.cosine_similarity_tfidf(
            article.get("normalized_title", article.get("title", "").lower()),
            story.get("normalized_title", story.get("title", "").lower())
        )

        # Combined text Jaccard similarity score
        text_sim = self.dedup_service.jaccard_similarity(art_text, story_text)

        # Max of title similarity or combined text similarity
        return max(title_sim, text_sim)

    def cluster_articles(
        self,
        articles: List[Dict[str, Any]],
        existing_stories: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Group input articles into story clusters.

        Returns:
            Tuple[updated_articles, active_stories]
        """
        stories_map: Dict[str, Dict[str, Any]] = {s["id"]: dict(s) for s in existing_stories}

        for article in articles:
            best_story_id: Optional[str] = None
            highest_score: float = 0.0

            for story_id, story in stories_map.items():
                score = self.compute_story_similarity(article, story)
                if score > highest_score and score >= self.similarity_threshold:
                    highest_score = score
                    best_story_id = story_id

            pub_time = self._to_naive_datetime(article.get("published_at"))

            if best_story_id:
                # Assign article to matching story
                article["story_id"] = best_story_id
                target_story = stories_map[best_story_id]
                target_story["article_count"] = target_story.get("article_count", 0) + 1
                
                # Normalize existing story timestamps for naive comparison
                earliest = self._to_naive_datetime(target_story.get("earliest_published_at"))
                latest = self._to_naive_datetime(target_story.get("latest_published_at"))

                # Update story timeline bounds if pub_time is available
                if pub_time is not None:
                    if earliest is None or pub_time < earliest:
                        target_story["earliest_published_at"] = pub_time
                    if latest is None or pub_time > latest:
                        target_story["latest_published_at"] = pub_time

                target_story["last_updated"] = datetime.now(timezone.utc).replace(tzinfo=None)

            else:
                # Create a new Story cluster
                new_story_id = f"story_{uuid.uuid4().hex[:12]}"
                article["story_id"] = new_story_id

                now_utc_naive = datetime.now(timezone.utc).replace(tzinfo=None)
                new_story = {
                    "id": new_story_id,
                    "title": article["title"],
                    "normalized_title": article.get("normalized_title", article["title"].lower()),
                    "summary": article.get("description", ""),
                    "topic": article.get("topic", "General"),
                    "category": article.get("topic", "General"),
                    "first_seen": now_utc_naive,
                    "last_updated": now_utc_naive,
                    "earliest_published_at": pub_time,
                    "latest_published_at": pub_time,
                    "article_count": 1,
                    "is_demo_data": article.get("is_demo_data", False)
                }
                stories_map[new_story_id] = new_story

        return articles, list(stories_map.values())
