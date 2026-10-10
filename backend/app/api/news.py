from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.article import Article
from app.models.story import Story
from app.schemas.article import ArticleResponse
from app.providers.news import get_news_provider
from app.services.ingestion import IngestionService
from app.services.deduplication import DeduplicationService
from app.services.clustering import ClusteringService

router = APIRouter(prefix="/news", tags=["News Ingestion & Articles"])

ingestion_service = IngestionService()
dedup_service = DeduplicationService()
clustering_service = ClusteringService()

@router.get("", response_model=List[ArticleResponse])
async def get_news(
    topic: Optional[str] = Query(None, description="Topic filter (e.g. artificial intelligence)"),
    sort: Optional[str] = Query("latest", description="Sort or mode: latest, popular, top"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Fetch news from NewsAPI (or RSS fallback), execute normalization, deduplication, and story clustering, and store in SQLite."""
    provider = get_news_provider()
    raw_articles = await provider.fetch_articles(topic=topic, limit=limit, sort=sort)

    
    # 1. Normalize
    normalized_list = [ingestion_service.normalize_article(raw) for raw in raw_articles]

    # 2. Query existing DB articles & stories
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

    # 3. Deduplicate
    deduped_list = dedup_service.process_duplicates(normalized_list, existing_articles_dict)

    # 4. Cluster into Stories
    clustered_articles, updated_stories = clustering_service.cluster_articles(deduped_list, existing_stories_dict)

    # 5. Persist/Update Stories in DB
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
                topic=s_data.get("topic", "General"),
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

    # 6. Persist Articles in DB
    from app.services.credibility import CredibilityVerificationService
    cred_service = CredibilityVerificationService()

    existing_ids = {a.id for a in db.query(Article.id).all()}
    for a_data in clustered_articles:
        if a_data["id"] not in existing_ids:
            domain = cred_service.extract_domain(a_data.get("url") or a_data.get("canonical_url"))
            rating = cred_service.evaluate_publisher(domain)

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
                topic=a_data.get("topic"),
                publisher_domain=domain,
                credibility_status=rating.rating,
                fact_check_status="not_checked",
                is_duplicate=a_data.get("is_duplicate", False),
                duplicate_of_id=a_data.get("duplicate_of_id"),
                story_id=a_data.get("story_id"),
                checksum=a_data.get("checksum"),
            )
            db.add(article_obj)
            existing_ids.add(a_data["id"])

    db.commit()

    # Query latest articles from DB
    query = db.query(Article)
    if topic:
        query = query.filter(Article.topic.ilike(f"%{topic}%"))
    
    results = query.order_by(Article.published_at.desc()).limit(limit).all()
    return results


@router.get("/top", response_model=List[ArticleResponse])
async def get_top_news(
    topic: Optional[str] = Query(None, description="Topic filter"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Fetch top/trending headlines."""
    return await get_news(topic=topic, sort="top", limit=limit, db=db)

