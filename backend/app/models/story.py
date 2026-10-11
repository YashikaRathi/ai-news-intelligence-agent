import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base

class Story(Base):
    __tablename__ = "stories"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    summary = Column(Text, nullable=True)
    what_changed = Column(Text, nullable=True)
    why_it_matters = Column(Text, nullable=True)
    topic = Column(String, default="General", index=True)
    category = Column(String, default="General", index=True)

    # Verification metadata
    discrepancy_status = Column(String, default="insufficient_evidence", index=True)
    fact_check_status = Column(String, default="not_checked", index=True)

    # Timestamps & Cluster info
    first_seen = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    last_updated = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    earliest_published_at = Column(DateTime, nullable=True)
    latest_published_at = Column(DateTime, nullable=True)
    article_count = Column(Integer, default=0)
    is_demo_data = Column(Boolean, default=False)

    # Relationships
    articles = relationship("Article", back_populates="story", cascade="all, delete-orphan")
