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

    # Timestamps & Cluster info
    first_seen = Column(DateTime, default=datetime.datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)
    earliest_published_at = Column(DateTime, default=datetime.datetime.utcnow)
    latest_published_at = Column(DateTime, default=datetime.datetime.utcnow)
    article_count = Column(Integer, default=0)
    is_demo_data = Column(Boolean, default=False)

    # Relationships
    articles = relationship("Article", back_populates="story", cascade="all, delete-orphan")
