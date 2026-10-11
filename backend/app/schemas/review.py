from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, ConfigDict

class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5, description="1 to 5 star rating of usefulness/clarity/reading experience")
    review_text: Optional[str] = Field(None, max_length=1000, description="Optional written review feedback (max 1000 characters)")
    reader_name: Optional[str] = Field("Anonymous Reader", max_length=50)

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    review_text: Optional[str] = Field(None, max_length=1000)
    reader_name: Optional[str] = Field(None, max_length=50)

class ReviewItem(BaseModel):
    id: str
    target_type: str
    target_id: str
    reader_id: str
    reader_name: str
    rating: int
    review_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ReviewSummary(BaseModel):
    target_type: str
    target_id: str
    average_rating: float
    total_ratings: int
    rating_distribution: Dict[str, int] = Field(
        default_factory=lambda: {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}
    )
    user_review: Optional[ReviewItem] = None
    reviews: List[ReviewItem] = []
    disclaimer: str = "Reader ratings reflect reader experience, clarity, and usefulness. They are NOT a truthfulness verdict and do not affect official verification results."

    model_config = ConfigDict(from_attributes=True)
