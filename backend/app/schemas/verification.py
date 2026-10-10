from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

class TrustScore(BaseModel):
    score: int  # 0 to 100
    label: str  # "High Trust", "Moderate Trust", "Needs Verification"
    corroboration_score: int  # 0 to 100
    publisher_credibility_score: int  # 0 to 100
    confidence_level: str  # "High", "Medium", "Low"

    model_config = ConfigDict(from_attributes=True)


class ClaimCheck(BaseModel):
    claim_text: str
    status: str  # "Corroborated", "Single Source", "Unverified"
    corroborating_sources: List[str] = []
    details: str

    model_config = ConfigDict(from_attributes=True)


class PublisherCredibility(BaseModel):
    source_name: str
    credibility_tier: str  # "Tier 1 (Established Wire/Major)", "Tier 2 (Regional/Specialized)", "Tier 3 (Unverified)"
    rating: str  # "High", "Medium", "Standard"
    domain_authority_score: int  # 0 to 100

    model_config = ConfigDict(from_attributes=True)


class VerificationResponse(BaseModel):
    story_id: str
    headline: str
    trust_score: TrustScore
    publisher_credibility: List[PublisherCredibility] = []
    claim_checks: List[ClaimCheck] = []
    summary: str
    total_sources: int = 1
    total_articles: int = 1
    is_demo: bool = False

    model_config = ConfigDict(from_attributes=True)
