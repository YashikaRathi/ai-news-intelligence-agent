import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base

class Article(Base):
    __tablename__ = "articles"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    normalized_title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    url = Column(String, unique=True, nullable=False, index=True)
    canonical_url = Column(String, nullable=False, index=True)
    source_name = Column(String, nullable=False, index=True)
    author = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    published_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    topic = Column(String, nullable=True, index=True)

    # Duplicate detection tracking
    is_duplicate = Column(Boolean, default=False, index=True)
    duplicate_of_id = Column(String, ForeignKey("articles.id"), nullable=True)
    
    # Story cluster relation
    story_id = Column(String, ForeignKey("stories.id"), nullable=True, index=True)
    story = relationship("Story", back_populates="articles")

    # Ingestion metadata
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    checksum = Column(String, nullable=True, index=True)
