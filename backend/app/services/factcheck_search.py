import logging
from typing import Dict, Any, Optional
from app.schemas.factcheck import FactCheckSearchResponse, FactCheckClaimResult, FactCheckReviewItem

logger = logging.getLogger(__name__)


class FactCheckSearchService:
    """Service responsible for searching external third-party fact-checkers."""

    async def search_claim_factchecks(
        self,
        query: str,
        limit: int = 5
    ) -> FactCheckSearchResponse:
        from app.providers.factcheck import get_factcheck_provider

        provider = get_factcheck_provider()
        
        try:
            raw = await provider.search_claims(query=query, limit=limit)
        except Exception as exc:
            logger.error(f"Error executing factcheck search: {exc}")
            return FactCheckSearchResponse(
                query=query,
                total_results=0,
                results=[],
                status="error",
                summary=f"Search failed: {exc}",
                is_demo=True
            )

        results = []
        for r in raw.get("results", []):
            reviews = [
                FactCheckReviewItem(
                    publisher_name=rev.get("publisher_name", "Unknown Fact-Checker"),
                    publisher_site=rev.get("publisher_site"),
                    review_url=rev.get("review_url", ""),
                    review_title=rev.get("review_title"),
                    review_date=rev.get("review_date"),
                    textual_rating=rev.get("textual_rating", "Unrated")
                )
                for rev in r.get("reviews", [])
            ]

            results.append(
                FactCheckClaimResult(
                    matched_claim_text=r.get("matched_claim_text", ""),
                    claimant=r.get("claimant"),
                    claim_date=r.get("claim_date"),
                    reviews=reviews,
                    relevance_score=r.get("relevance_score", 1.0),
                    context_match=r.get("context_match", True)
                )
            )

        return FactCheckSearchResponse(
            query=raw.get("query", query),
            total_results=raw.get("total_results", len(results)),
            results=results,
            status=raw.get("status", "success"),
            summary=raw.get("summary", "Search complete."),
            is_demo=raw.get("is_demo", False)
        )
