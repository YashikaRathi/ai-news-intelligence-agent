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
    source_updated_at: Optional[datetime] = None
    topic: Optional[str] = "General"

class ArticleCreate(ArticleBase):
    normalized_title: Optional[str] = None

class ArticleResponse(ArticleBase):
    id: str
    story_id: Optional[str] = None
    is_duplicate: bool = False
    duplicate_of_id: Optional[str] = None
    publisher_domain: Optional[str] = None
    credibility_status: Optional[str] = "not_assessed"
    fact_check_status: Optional[str] = "Not checked"
    overall_verification_status: Optional[str] = "Not checked"
    ingested_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
