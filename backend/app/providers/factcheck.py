import os
import logging
import httpx
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class BaseFactCheckProvider(ABC):
    """Abstract Base Class for External Fact-Check Search Providers."""

    def __init__(self):
        self.api_key: Optional[str] = os.getenv("GOOGLE_FACTCHECK_API_KEY")

    @abstractmethod
    async def search_claims(
        self,
        query: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """Search external fact-check database for claims matching query."""
        pass


class DemoFactCheckProvider(BaseFactCheckProvider):
    """Deterministic local Fact-Check provider for DEMO_MODE or offline execution."""

    async def search_claims(
        self,
        query: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        q_clean = (query or "").strip().lower()
        if not q_clean:
            return {
                "query": query,
                "total_results": 0,
                "results": [],
                "status": "no_results_found",
                "summary": "Empty search query provided.",
                "is_demo": True
            }

        # Deterministic demo mock results
        results = [
            {
                "matched_claim_text": f"Fact Check regarding '{query}'",
                "claimant": "Public Social Media Statement",
                "claim_date": "2026-08-15",
                "relevance_score": 0.95,
                "context_match": True,
                "reviews": [
                    {
                        "publisher_name": "FactCheck.org",
                        "publisher_site": "factcheck.org",
                        "review_url": "https://www.factcheck.org/2026/08/demo-claim-review",
                        "review_title": f"Fact Check Analysis: {query}",
                        "review_date": "2026-08-16",
                        "textual_rating": "False"
                    }
                ]
            }
        ]

        return {
            "query": query,
            "total_results": len(results),
            "results": results[:limit],
            "status": "success",
            "summary": f"Found {len(results)} simulated demo fact-check result(s).",
            "is_demo": True
        }


class GoogleFactCheckProvider(BaseFactCheckProvider):
    """Concrete Google Fact Check Tools API provider implementation."""

    BASE_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

    async def search_claims(
        self,
        query: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_google_factcheck_api_key_here":
            logger.warning("No valid GOOGLE_FACTCHECK_API_KEY found. Returning missing API key response.")
            return {
                "query": query,
                "total_results": 0,
                "results": [],
                "status": "missing_api_key",
                "summary": "No GOOGLE_FACTCHECK_API_KEY configured.",
                "is_demo": False
            }

        q_clean = (query or "").strip()
        if not q_clean:
            return {
                "query": query,
                "total_results": 0,
                "results": [],
                "status": "no_results_found",
                "summary": "Empty query string.",
                "is_demo": False
            }

        params = {
            "query": q_clean,
            "key": self.api_key,
            "pageSize": limit,
            "languageCode": "en"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(self.BASE_URL, params=params)

                if resp.status_code == 400 or resp.status_code == 401 or resp.status_code == 403:
                    logger.error(f"Google Fact Check API Auth failure HTTP {resp.status_code}")
                    return {
                        "query": query,
                        "total_results": 0,
                        "results": [],
                        "status": "auth_failure",
                        "summary": f"Google Fact Check API authentication failed (HTTP {resp.status_code}).",
                        "is_demo": False
                    }
                elif resp.status_code == 429:
                    logger.error("Google Fact Check API rate limit exceeded")
                    return {
                        "query": query,
                        "total_results": 0,
                        "results": [],
                        "status": "rate_limited",
                        "summary": "Google Fact Check API rate limit exceeded.",
                        "is_demo": False
                    }
                elif resp.status_code != 200:
                    logger.error(f"Google Fact Check API Error HTTP {resp.status_code}")
                    return {
                        "query": query,
                        "total_results": 0,
                        "results": [],
                        "status": "error",
                        "summary": f"Google Fact Check API error (HTTP {resp.status_code}).",
                        "is_demo": False
                    }

                try:
                    data = resp.json()
                except Exception as parse_err:
                    logger.error(f"Failed to parse JSON response: {parse_err}")
                    return {
                        "query": query,
                        "total_results": 0,
                        "results": [],
                        "status": "error",
                        "summary": "Malformed JSON response from Google Fact Check API.",
                        "is_demo": False
                    }

                raw_claims = data.get("claims", [])
                if not raw_claims:
                    return {
                        "query": query,
                        "total_results": 0,
                        "results": [],
                        "status": "no_results_found",
                        "summary": f"No external fact-checks found for '{query}'.",
                        "is_demo": False
                    }

                query_words = set(q_clean.lower().split())
                parsed_results = []

                for c in raw_claims:
                    matched_text = c.get("text", "")
                    matched_words = set(matched_text.lower().split())

                    # Context match evaluation: check word overlap with query
                    overlap = len(query_words.intersection(matched_words))
                    relevance_score = round(overlap / max(len(query_words), 1), 2)
                    context_match = relevance_score >= 0.3 or len(query_words) <= 2

                    reviews = []
                    for rev in c.get("claimReview", []):
                        pub = rev.get("publisher", {})
                        reviews.append({
                            "publisher_name": pub.get("name", "Unknown Fact-Checker"),
                            "publisher_site": pub.get("site"),
                            "review_url": rev.get("url", ""),
                            "review_title": rev.get("title"),
                            "review_date": rev.get("reviewDate"),
                            "textual_rating": rev.get("textualRating", "Unrated")
                        })

                    parsed_results.append({
                        "matched_claim_text": matched_text,
                        "claimant": c.get("claimant"),
                        "claim_date": c.get("claimDate"),
                        "reviews": reviews,
                        "relevance_score": relevance_score,
                        "context_match": context_match
                    })

                return {
                    "query": query,
                    "total_results": len(parsed_results),
                    "results": parsed_results[:limit],
                    "status": "success",
                    "summary": f"Found {len(parsed_results)} external fact-check result(s).",
                    "is_demo": False
                }

        except httpx.TimeoutException:
            logger.error("Google Fact Check API request timed out")
            return {
                "query": query,
                "total_results": 0,
                "results": [],
                "status": "timeout_error",
                "summary": "Google Fact Check API request timed out.",
                "is_demo": False
            }
        except Exception as exc:
            logger.error(f"Google Fact Check API execution error: {exc}")
            return {
                "query": query,
                "total_results": 0,
                "results": [],
                "status": "error",
                "summary": f"Google Fact Check API execution failed: {exc}",
                "is_demo": False
            }


def get_factcheck_provider() -> BaseFactCheckProvider:
    """Factory function returning active fact check provider."""
    demo_mode = os.getenv("DEMO_MODE", "false").lower() in ["true", "1", "yes"]
    api_key = os.getenv("GOOGLE_FACTCHECK_API_KEY")

    if demo_mode or not api_key or api_key == "your_google_factcheck_api_key_here":
        return DemoFactCheckProvider()

    return GoogleFactCheckProvider()
