from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.story import Story
from app.models.article import Article
from app.schemas.story import StoryResponse, StoryTimelineResponse, TimelineEvent

from app.services.search import SearchService

router = APIRouter(prefix="/stories", tags=["Stories & Clusters"])

@router.get("", response_model=List[StoryResponse])
def get_stories(
    topic: Optional[str] = Query(None, description="Filter stories by topic"),
    freshness: Optional[str] = Query("all", description="Freshness filter: 1h, 6h, 24h, 7d, all"),
    sort_by: Optional[str] = Query("latest", description="Sort by 'latest' (newest publication time) or 'updated'"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Retrieve story clusters ordered by original publication time (or latest update) with optional freshness window."""
    query = db.query(Story).options(joinedload(Story.articles))
    if topic and topic.strip() and topic.strip().lower() not in ["general", "all", "news"]:
        query = query.filter(Story.topic.ilike(f"%{topic.strip()}%"))

    cutoff = SearchService.get_freshness_cutoff(freshness)
    if cutoff:
        query = query.filter(Story.latest_published_at.isnot(None), Story.latest_published_at >= cutoff)

    # Sort strictly by newest article publication timestamp for news freshness
    if sort_by == "updated":
        stories = query.order_by(Story.last_updated.desc()).limit(limit).all()
    else:
        stories = query.order_by(Story.latest_published_at.desc()).limit(limit).all()

    return stories

@router.get("/{story_id}", response_model=StoryResponse)
def get_story(story_id: str, db: Session = Depends(get_db)):
    """Retrieve details for a specific story cluster."""
    story = db.query(Story).options(joinedload(Story.articles)).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail=f"Story with ID '{story_id}' not found.")
    return story

@router.get("/{story_id}/timeline", response_model=StoryTimelineResponse)
def get_story_timeline(story_id: str, db: Session = Depends(get_db)):
    """Retrieve chronological coverage timeline for a specific story cluster."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail=f"Story with ID '{story_id}' not found.")

    articles = (
        db.query(Article)
        .filter(Article.story_id == story_id)
        .order_by(Article.published_at.asc())  # Chronological order: earliest to latest
        .all()
    )

    timeline_events = [
        TimelineEvent(
            article_id=art.id,
            title=art.title,
            source_name=art.source_name,
            published_at=art.published_at,
            url=art.url,
            author=art.author,
            image_url=art.image_url,
        )
        for art in articles
    ]

    return StoryTimelineResponse(
        story_id=story.id,
        story_title=story.title,
        topic=story.topic,
        total_articles=len(timeline_events),
        earliest_published_at=story.earliest_published_at,
        latest_published_at=story.latest_published_at,
        timeline=timeline_events,
    )
