from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.article import ArticleResponse

class StoryBase(BaseModel):
    title: str
    summary: Optional[str] = None
    what_changed: Optional[str] = None
    why_it_matters: Optional[str] = None
    topic: Optional[str] = "General"
    category: Optional[str] = "General"

class StoryCreate(StoryBase):
    pass

class StoryResponse(StoryBase):
    id: str
    first_seen: datetime
    last_updated: datetime
    earliest_published_at: Optional[datetime] = None
    latest_published_at: Optional[datetime] = None
    article_count: int
    is_demo_data: bool = False
    discrepancy_status: Optional[str] = "insufficient_evidence"
    fact_check_status: Optional[str] = "not_checked"
    articles: List[ArticleResponse] = []

    model_config = ConfigDict(from_attributes=True)


class TimelineEvent(BaseModel):
    article_id: str
    title: str
    source_name: str
    published_at: Optional[datetime]
    url: str
    author: Optional[str] = None
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class StoryTimelineResponse(BaseModel):
    story_id: str
    story_title: str
    topic: str
    total_articles: int
    earliest_published_at: Optional[datetime]
    latest_published_at: Optional[datetime]
    timeline: List[TimelineEvent]

    model_config = ConfigDict(from_attributes=True)
