from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class NotificationItem(BaseModel):
    id: str
    recipient_id: str
    event_type: str
    title: str
    message: str
    story_id: Optional[str] = None
    article_id: Optional[str] = None
    topic: Optional[str] = None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class NotificationListResponse(BaseModel):
    unread_count: int
    total_count: int
    notifications: List[NotificationItem]

class NotificationPreferenceUpdate(BaseModel):
    followed_topics: Optional[List[str]] = None
    followed_stories: Optional[List[str]] = None
    categories_enabled: Optional[List[str]] = None
    notifications_enabled: Optional[bool] = None

class NotificationPreferenceResponse(BaseModel):
    reader_id: str
    followed_topics: List[str]
    followed_stories: List[str]
    categories_enabled: List[str]
    notifications_enabled: bool
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
