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
    published_at = Column(DateTime, nullable=True, index=True)
    source_updated_at = Column(DateTime, nullable=True)
    ingested_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    verified_at = Column(DateTime, nullable=True)
    topic = Column(String, nullable=True, index=True)

    # Verification metadata
    publisher_domain = Column(String, nullable=True, index=True)
    credibility_status = Column(String, default="not_assessed", index=True)
    fact_check_status = Column(String, default="not_checked", index=True)

    # Duplicate detection tracking
    is_duplicate = Column(Boolean, default=False, index=True)
    duplicate_of_id = Column(String, ForeignKey("articles.id"), nullable=True)
    
    # Story cluster relation
    story_id = Column(String, ForeignKey("stories.id"), nullable=True, index=True)
    story = relationship("Story", back_populates="articles")

    # Ingestion metadata
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    checksum = Column(String, nullable=True, index=True)
