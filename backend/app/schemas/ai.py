from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

class EvidenceItem(BaseModel):
    article_id: str
    source_name: str
    title: str
    url: str
    published_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SourceComparisonItem(BaseModel):
    source_name: str
    headline: str
    url: str
    published_at: Optional[datetime] = None
    emphasis: str
    differences: str
    agreement: str

    model_config = ConfigDict(from_attributes=True)


class StoryIntelligenceResponse(BaseModel):
    story_id: str
    headline: str
    topic: str
    what_happened: str
    what_changed: str
    why_it_matters: str
    key_points: List[str] = []
    entities: List[str] = []
    sources: List[str] = []
    evidence: List[EvidenceItem] = []
    source_comparison: List[SourceComparisonItem] = []
    confidence: str = "High"
    is_demo: bool = False

    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    story_id: Optional[str] = None
    query: Optional[str] = None  # query parameter support
    question: Optional[str] = None

    def get_question(self) -> str:
        return self.question or self.query or ""


class ChatSourceItem(BaseModel):
    article_id: str
    source: str
    title: str
    url: str

    model_config = ConfigDict(from_attributes=True)


class ChatResponse(BaseModel):
    answer: str
    sources: List[ChatSourceItem] = []
    is_demo: bool = False

    model_config = ConfigDict(from_attributes=True)


class SummarizeRequest(BaseModel):
    story_id: Optional[str] = None
    articles: Optional[List[Dict[str, Any]]] = None
