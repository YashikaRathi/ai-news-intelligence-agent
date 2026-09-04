from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ArticleBase(BaseModel):
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    url: str
    canonical_url: Optional[str] = None
    source_name: str
    author: Optional[str] = None
    image_url: Optional[str] = None
    published_at: Optional[datetime] = None
    topic: Optional[str] = "General"

class ArticleCreate(ArticleBase):
    normalized_title: Optional[str] = None

class ArticleResponse(ArticleBase):
    id: str
    story_id: Optional[str] = None
    is_duplicate: bool = False
    duplicate_of_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
