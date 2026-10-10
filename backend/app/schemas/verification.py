from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

class SourceRating(BaseModel):
    domain: str
    rating: str = Field(description="e.g. high_credibility, medium_credibility, low_credibility, unverified_publisher")
    explanation: str
    provenance: str = Field(default="Internal Registry")

class FactCheckItem(BaseModel):
    claim: str
    claimant: Optional[str] = None
    fact_check_publisher: str
    review_date: Optional[str] = None
    original_rating: str
    normalized_status: str = Field(description="verified_by_existing_fact_check, disputed_by_existing_fact_check, or unknown")
    fact_check_url: str

class VerificationResult(BaseModel):
    article_id: str
    publisher_domain: str
    credibility_status: str = Field(default="unverified_publisher")
    source_rating: Optional[SourceRating] = None
    fact_check_status: str = Field(default="not_checked")
    fact_checks: List[FactCheckItem] = []
    discrepancy_status: str = Field(default="insufficient_evidence")
    cross_source_findings: Dict[str, Any] = Field(default_factory=dict)
    limitations: List[str] = Field(default_factory=list)
    last_checked_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)

class StoryVerificationSummary(BaseModel):
    story_id: str
    total_articles: int
    verified_fact_checks_count: int = 0
    disputed_fact_checks_count: int = 0
    discrepancy_status: str = Field(default="insufficient_evidence")
    high_credibility_sources_count: int = 0
    unverified_sources_count: int = 0
    fact_checks: List[FactCheckItem] = []
    cross_source_findings: Dict[str, Any] = Field(default_factory=dict)
    limitations: List[str] = Field(default_factory=list)
    last_checked_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)
