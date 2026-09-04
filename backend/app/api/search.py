import logging
from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.session import get_db
from app.models.article import Article
from app.models.story import Story
from app.schemas.article import ArticleResponse
from app.schemas.story import StoryResponse
from app.providers.news import get_news_provider
from app.services.ingestion import IngestionService
from app.services.deduplication import DeduplicationService
from app.services.clustering import ClusteringService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])

ingestion_service = IngestionService()
dedup_service = DeduplicationService()
clustering_service = ClusteringService()

@router.get("")
async def search_news(
    q: str = Query(..., min_length=1, description="Search query string"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Search articles and story clusters by executing live news discovery (NewsAPI/RSS), normalization, deduplication, story clustering, and SQLite persistence."""
    clean_query = q.strip()
    if not clean_query:
        return {
            "query": q,
            "article_count": 0,
            "story_count": 0,
            "articles": [],
            "stories": []
        }

    # 1. Trigger live news discovery for searched topic/query
    try:
        provider = get_news_provider()
        raw_articles = await provider.fetch_articles(topic=clean_query, limit=limit, sort="latest")

        if raw_articles:
            # 2. Normalize
            normalized_list = [ingestion_service.normalize_article(raw) for raw in raw_articles]

            # 3. Query existing DB articles & stories
            existing_db_articles = db.query(Article).all()
            existing_articles_dict = [
                {
                    "id": a.id,
                    "title": a.title,
                    "normalized_title": a.normalized_title,
                    "canonical_url": a.canonical_url,
                    "is_duplicate": a.is_duplicate,
                    "description": a.description
                }
                for a in existing_db_articles
            ]

            existing_db_stories = db.query(Story).all()
            existing_stories_dict = [
                {
                    "id": s.id,
                    "title": s.title,
                    "normalized_title": s.title.lower(),
                    "summary": s.summary,
                    "topic": s.topic,
                    "earliest_published_at": s.earliest_published_at,
                    "latest_published_at": s.latest_published_at,
                    "article_count": s.article_count
                }
                for s in existing_db_stories
            ]

            # 4. Deduplicate
            deduped_list = dedup_service.process_duplicates(normalized_list, existing_articles_dict)

            # 5. Cluster into Stories
            clustered_articles, updated_stories = clustering_service.cluster_articles(deduped_list, existing_stories_dict)

            # 6. Persist/Update Stories in DB
            story_db_map = {s.id: s for s in db.query(Story).all()}
            for s_data in updated_stories:
                s_id = s_data["id"]
                if s_id in story_db_map:
                    st = story_db_map[s_id]
                    st.article_count = s_data.get("article_count", st.article_count)
                    st.earliest_published_at = s_data.get("earliest_published_at", st.earliest_published_at)
                    st.latest_published_at = s_data.get("latest_published_at", st.latest_published_at)
                    st.last_updated = s_data.get("last_updated", st.last_updated)
                else:
                    new_st = Story(
                        id=s_id,
                        title=s_data["title"],
                        summary=s_data.get("summary", ""),
                        topic=clean_query,
                        category=s_data.get("category", "General"),
                        first_seen=s_data.get("first_seen"),
                        last_updated=s_data.get("last_updated"),
                        earliest_published_at=s_data.get("earliest_published_at"),
                        latest_published_at=s_data.get("latest_published_at"),
                        article_count=s_data.get("article_count", 1),
                        is_demo_data=s_data.get("is_demo_data", False)
                    )
                    db.add(new_st)

            db.commit()

            # 7. Persist Articles in DB
            existing_ids = {a.id for a in db.query(Article.id).all()}
            for a_data in clustered_articles:
                if a_data["id"] not in existing_ids:
                    article_obj = Article(
                        id=a_data["id"],
                        title=a_data["title"],
                        normalized_title=a_data["normalized_title"],
                        description=a_data.get("description"),
                        content=a_data.get("content"),
                        url=a_data["url"],
                        canonical_url=a_data["canonical_url"],
                        source_name=a_data["source_name"],
                        author=a_data.get("author"),
                        image_url=a_data.get("image_url"),
                        published_at=a_data.get("published_at"),
                        topic=a_data.get("topic") or clean_query,
                        is_duplicate=a_data.get("is_duplicate", False),
                        duplicate_of_id=a_data.get("duplicate_of_id"),
                        story_id=a_data.get("story_id"),
                        checksum=a_data.get("checksum"),
                    )
                    db.add(article_obj)
                    existing_ids.add(a_data["id"])

            db.commit()
    except Exception as exc:
        logger.warning(f"Live news discovery during search failed ({exc}). Falling back to local database search.")

    # 8. Query SQLite database for matching articles and stories
    keywords = [w.strip() for w in clean_query.split() if len(w.strip()) > 1]

    art_filters = [
        Article.title.ilike(f"%{clean_query}%"),
        Article.description.ilike(f"%{clean_query}%"),
        Article.source_name.ilike(f"%{clean_query}%"),
        Article.topic.ilike(f"%{clean_query}%")
    ]
    for kw in keywords:
        art_filters.append(Article.title.ilike(f"%{kw}%"))
        art_filters.append(Article.description.ilike(f"%{kw}%"))

    matched_articles = (
        db.query(Article)
        .filter(or_(*art_filters))
        .order_by(Article.published_at.desc())
        .limit(limit)
        .all()
    )

    story_filters = [
        Story.title.ilike(f"%{clean_query}%"),
        Story.summary.ilike(f"%{clean_query}%"),
        Story.topic.ilike(f"%{clean_query}%")
    ]
    for kw in keywords:
        story_filters.append(Story.title.ilike(f"%{kw}%"))
        story_filters.append(Story.summary.ilike(f"%{kw}%"))

    matched_stories = (
        db.query(Story)
        .filter(or_(*story_filters))
        .order_by(Story.last_updated.desc())
        .limit(limit)
        .all()
    )

    article_responses = [ArticleResponse.model_validate(art) for art in matched_articles]
    story_responses = [StoryResponse.model_validate(st) for st in matched_stories]

    return {
        "query": q,
        "article_count": len(article_responses),
        "story_count": len(story_responses),
        "articles": article_responses,
        "stories": story_responses
    }

