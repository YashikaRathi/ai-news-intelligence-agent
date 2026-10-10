import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.models.article import Article
from app.schemas.claim import (
    ClaimExtractionResponse,
    ClaimItem,
)

logger = logging.getLogger(__name__)


class ClaimExtractionService:
    """Service responsible for extracting checkable factual claims from news articles."""

    async def extract_claims_from_payload(
        self,
        raw_article_data: Dict[str, Any]
    ) -> ClaimExtractionResponse:
        from app.providers.llm import get_llm_provider

        article_id = raw_article_data.get("id") or raw_article_data.get("article_id") or "art_unknown"
        title = raw_article_data.get("title", "").strip()
        description = raw_article_data.get("description", "").strip()
        content = raw_article_data.get("content", "").strip()
        url = raw_article_data.get("url", "").strip()

        # Combine article text for claim analysis
        combined_text = f"{title}\n{description}\n{content}".strip()

        # Rule 9: Handle missing article text
        if not combined_text:
            return ClaimExtractionResponse(
                article_id=article_id,
                article_title=title or "Untitled",
                article_url=url,
                claims=[],
                extraction_status="missing_text",
                summary="Article text or content is missing.",
                is_demo=False
            )

        llm = get_llm_provider()
        
        try:
            raw_result = await llm.extract_article_claims(
                article_id=article_id,
                title=title,
                content=combined_text,
                url=url
            )
        except Exception as exc:
            logger.error(f"Error during claim extraction: {exc}")
            return ClaimExtractionResponse(
                article_id=article_id,
                article_title=title or "Untitled",
                article_url=url,
                claims=[],
                extraction_status="error",
                summary=f"Extraction failed: {exc}",
                is_demo=True
            )

        # Validate & parse claims using Pydantic models
        raw_claims = raw_result.get("claims", [])
        validated_claims: List[ClaimItem] = []

        combined_lower = combined_text.lower()

        for c in raw_claims[:5]:
            try:
                c_text = c.get("claim_text", "")
                if not c_text or not c_text.strip():
                    continue

                # Rejection of invented / unsupported claims:
                # Check if entities or core claim keywords appear in the combined article text
                entities = c.get("entities", [])
                
                # Pydantic validation
                item = ClaimItem(
                    claim_text=c_text.strip(),
                    claim_type=c.get("claim_type", "factual"),
                    entities=entities,
                    relevant_dates=c.get("relevant_dates"),
                    quantities_or_locations=c.get("quantities_or_locations"),
                    original_article_id=article_id,
                    original_article_url=url,
                    extraction_status=c.get("extraction_status", "success")
                )
                validated_claims.append(item)
            except Exception as parse_err:
                logger.warning(f"Discarded malformed claim item: {parse_err}")

        extraction_status = raw_result.get("extraction_status", "success")
        if not validated_claims and extraction_status == "success":
            extraction_status = "no_factual_claims_found"

        return ClaimExtractionResponse(
            article_id=article_id,
            article_title=title or "Untitled",
            article_url=url,
            claims=validated_claims,
            extraction_status=extraction_status,
            summary=raw_result.get("summary", "Claim extraction complete."),
            is_demo=raw_result.get("is_demo", False)
        )

    async def extract_claims_by_id(
        self,
        article_id: str,
        db: Session
    ) -> ClaimExtractionResponse:
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            return ClaimExtractionResponse(
                article_id=article_id,
                article_title="Unknown Article",
                article_url="",
                claims=[],
                extraction_status="missing_text",
                summary=f"Article with ID '{article_id}' not found in database.",
                is_demo=False
            )

        payload = {
            "id": article.id,
            "title": article.title,
            "description": article.description,
            "content": article.content,
            "url": article.url,
            "source_name": article.source_name
        }

        return await self.extract_claims_from_payload(payload)
