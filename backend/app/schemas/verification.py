from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

class SourceRating(BaseModel):
    domain: str
    assessment_status: str = Field(
        default="rated",
        description="'rated' if publisher is in registry, 'not_assessed' if not yet evaluated"
    )
    rating: str = Field(
        default="not_assessed",
        description="high_credibility, medium_credibility, caution_advised, or not_assessed"
    )
    explanation: str
    provenance: str = Field(default="Internal Registry")
    limitations: Optional[str] = None


class FactCheckItem(BaseModel):
    claim: str
    claimant: Optional[str] = None
    fact_check_publisher: str
    review_date: Optional[str] = None
    original_rating: str
    normalized_status: str = Field(
        description="'Fact-check rated TRUE', 'Fact-check rated FALSE', 'Mixed or partially true', or 'unknown'"
    )
    fact_check_url: str


class CrossSourceFindings(BaseModel):
    agreements: List[str] = []
    differences: List[str] = []
    single_source_claims: List[str] = []
    independent_sources: List[str] = []
    syndicated_sources: List[str] = []
    summary: str = ""
    citations: List[Dict[str, Any]] = []


class VerificationResult(BaseModel):
    article_id: str
    publisher_domain: str
    overall_status: str = Field(
        default="Not checked",
        description="Readable status: Fact-check rated TRUE, Fact-check rated FALSE, Mixed or partially true, Conflicting reports, Insufficient evidence, No matching fact-check found, Not checked"
    )
    status_reason: str = Field(
        default="",
        description="Clear explanation of why this overall status was assigned"
    )
    publisher_credibility_status: str = Field(
        default="not_assessed",
        description="rated or not_assessed"
    )
    source_rating: Optional[SourceRating] = None
    fact_check_status: str = Field(default="Not checked")
    fact_checks: List[FactCheckItem] = []
    discrepancy_status: str = Field(default="Insufficient evidence")
    cross_source_findings: Dict[str, Any] = Field(default_factory=dict)
    limitations: List[str] = Field(default_factory=list)
    last_checked_at: Optional[datetime] = None

    # Backward compatibility fields for existing tests and components
    credibility_status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class StoryVerificationSummary(BaseModel):
    story_id: str
    total_articles: int
    overall_status: str = Field(default="Not checked")
    status_reason: str = Field(default="")
    verified_fact_checks_count: int = 0
    disputed_fact_checks_count: int = 0
    discrepancy_status: str = Field(default="Insufficient evidence")
    high_credibility_sources_count: int = 0
    not_assessed_sources_count: int = 0
    unverified_sources_count: int = 0  # Backward compat
    fact_checks: List[FactCheckItem] = []
    cross_source_findings: Dict[str, Any] = Field(default_factory=dict)
    limitations: List[str] = Field(default_factory=list)
    last_checked_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
