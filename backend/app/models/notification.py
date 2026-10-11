import datetime
import uuid
from sqlalchemy import Column, String, Text, DateTime, Boolean, Index
from app.db.base import Base

class Notification(Base):
    """Stores in-app notifications persistently in SQLite."""
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=lambda: f"notif_{uuid.uuid4().hex[:12]}")
    recipient_id = Column(String, nullable=False, index=True)  # User/reader ID or "all"
    event_type = Column(String, nullable=False, index=True)  # topic_alert, story_update, verification_change, contradiction_alert
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    story_id = Column(String, nullable=True, index=True)
    article_id = Column(String, nullable=True, index=True)
    topic = Column(String, nullable=True, index=True)
    is_read = Column(Boolean, default=False, index=True)
    event_key = Column(String, unique=True, nullable=True, index=True)  # Deduplication key
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False, index=True)

    __table_args__ = (
        Index("idx_notif_recipient_created", "recipient_id", "created_at"),
    )


class NotificationPreference(Base):
    """User preferences for following topics, stories, and notification categories."""
    __tablename__ = "notification_preferences"

    reader_id = Column(String, primary_key=True)
    followed_topics = Column(Text, default="[]")  # JSON encoded list of topics
    followed_stories = Column(Text, default="[]")  # JSON encoded list of story IDs
    categories_enabled = Column(Text, default='["topic_alert","story_update","verification_change","contradiction_alert"]')
    notifications_enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))
