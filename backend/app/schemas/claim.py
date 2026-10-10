from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class ClaimItem(BaseModel):
    claim_text: str
    claim_type: str = "factual"  # "factual", "statistical", "attributed_quote", "event", "policy"
    entities: List[str] = []
    relevant_dates: Optional[str] = None
    quantities_or_locations: Optional[str] = None
    original_article_id: str
    original_article_url: str
    extraction_status: str = "success"

    model_config = ConfigDict(from_attributes=True)


class ClaimExtractionResponse(BaseModel):
    article_id: str
    article_title: str
    article_url: str
    claims: List[ClaimItem] = []
    extraction_status: str  # "success", "no_factual_claims_found", "missing_text", "demo_mode", "error"
    summary: str
    is_demo: bool = False

    model_config = ConfigDict(from_attributes=True)


class ClaimExtractionRequest(BaseModel):
    article_id: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    source_name: Optional[str] = None
