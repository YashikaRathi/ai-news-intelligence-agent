import datetime
import uuid
from sqlalchemy import Column, String, Text, DateTime, Integer, UniqueConstraint, Index
from app.db.base import Base

class ReaderReview(Base):
    """Stores reader feedback ratings and written reviews for articles or stories."""
    __tablename__ = "reader_reviews"

    id = Column(String, primary_key=True, default=lambda: f"rev_{uuid.uuid4().hex[:12]}")
    target_type = Column(String, nullable=False, index=True)  # 'article' or 'story'
    target_id = Column(String, nullable=False, index=True)
    reader_id = Column(String, nullable=False, index=True)
    reader_name = Column(String, default="Reader", nullable=False)
    rating = Column(Integer, nullable=False)  # 1 to 5
    review_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("target_type", "target_id", "reader_id", name="uq_target_reader"),
        Index("idx_review_target", "target_type", "target_id"),
    )
