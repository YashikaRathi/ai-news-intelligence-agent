from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class FactCheckReviewItem(BaseModel):
    publisher_name: str
    publisher_site: Optional[str] = None
    review_url: str
    review_title: Optional[str] = None
    review_date: Optional[str] = None
    textual_rating: str  # Original verdict text or rating (e.g. "False", "Mostly True")

    model_config = ConfigDict(from_attributes=True)


class FactCheckClaimResult(BaseModel):
    matched_claim_text: str
    claimant: Optional[str] = None
    claim_date: Optional[str] = None
    reviews: List[FactCheckReviewItem] = []
    relevance_score: float = 1.0
    context_match: bool = True

    model_config = ConfigDict(from_attributes=True)


class FactCheckSearchResponse(BaseModel):
    query: str
    total_results: int = 0
    results: List[FactCheckClaimResult] = []
    status: str  # "success", "no_results_found", "missing_api_key", "auth_failure", "rate_limited", "timeout_error", "error"
    summary: str
    is_demo: bool = False

    model_config = ConfigDict(from_attributes=True)
