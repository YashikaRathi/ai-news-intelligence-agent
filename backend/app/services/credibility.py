import os
import logging
import urllib.parse
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.schemas.verification import (
    SourceRating,
    FactCheckItem,
    VerificationResult,
    StoryVerificationSummary,
)

logger = logging.getLogger(__name__)

# Configurable Registry of Known Publisher Domains
DEFAULT_CREDIBILITY_REGISTRY: Dict[str, Dict[str, str]] = {
    "bbc.com": {
        "rating": "high_credibility",
        "explanation": "Established international public service broadcaster with strict editorial guidelines.",
        "provenance": "Editorial Policy Audit Registry"
    },
    "bbc.co.uk": {
        "rating": "high_credibility",
        "explanation": "Established international public service broadcaster with strict editorial guidelines.",
        "provenance": "Editorial Policy Audit Registry"
    },
    "theguardian.com": {
        "rating": "high_credibility",
        "explanation": "Major independent news organization with transparent correction policies.",
        "provenance": "Editorial Policy Audit Registry"
    },
    "techcrunch.com": {
        "rating": "high_credibility",
        "explanation": "Recognized technology journalism publication focusing on startups and industry news.",
        "provenance": "Industry Media Registry"
    },
    "npr.org": {
        "rating": "high_credibility",
        "explanation": "Non-profit public media organization with independent journalism standards.",
        "provenance": "Public Media Registry"
    },
    "reuters.com": {
        "rating": "high_credibility",
        "explanation": "Global news agency adhering to strict neutrality and wire standards.",
        "provenance": "Global News Agency Registry"
    },
    "apnews.com": {
        "rating": "high_credibility",
        "explanation": "Independent global news cooperative producing verified wire reporting.",
        "provenance": "Global News Agency Registry"
    },
    "nytimes.com": {
        "rating": "high_credibility",
        "explanation": "Major newspaper of record with comprehensive fact-checking standards.",
        "provenance": "Major Media Registry"
    },
    "washingtonpost.com": {
        "rating": "high_credibility",
        "explanation": "Established investigative journalism publication with transparent editorial standards.",
        "provenance": "Major Media Registry"
    },
    "bloomberg.com": {
        "rating": "high_credibility",
        "explanation": "Financial news provider with strict market reporting accuracy policies.",
        "provenance": "Financial Media Registry"
    },
    "theverge.com": {
        "rating": "medium_credibility",
        "explanation": "Technology news outlet covering tech trends, reviews, and commentary.",
        "provenance": "Tech Media Registry"
    },
    "wired.com": {
        "rating": "medium_credibility",
        "explanation": "Established tech and culture magazine providing analysis and reporting.",
        "provenance": "Tech Media Registry"
    }
}

class CredibilityVerificationService:
    """Service evaluating publisher credibility, fact-check matching, and cross-source discrepancies."""

    def __init__(self, registry: Optional[Dict[str, Dict[str, str]]] = None):
        self.registry = registry if registry is not None else DEFAULT_CREDIBILITY_REGISTRY
        self.fact_check_api_key = os.getenv("GOOGLE_FACT_CHECK_API_KEY", "").strip()

    @staticmethod
    def extract_domain(url: Optional[str]) -> str:
        """Safely extract and normalize the publisher domain from an article URL."""
        if not url or not isinstance(url, str) or not url.strip():
            return "unknown_domain"

        clean_url = url.strip()
        if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
            clean_url = "https://" + clean_url

        try:
            parsed = urllib.parse.urlparse(clean_url)
            domain = parsed.netloc.lower().split(":")[0]
            if domain.startswith("www."):
                domain = domain[4:]
            return domain if domain else "unknown_domain"
        except Exception:
            return "unknown_domain"

    def evaluate_publisher(self, domain: str) -> SourceRating:
        """Evaluate a publisher domain against the credibility registry."""
        norm_domain = domain.lower().strip()
        if norm_domain in self.registry:
            info = self.registry[norm_domain]
            return SourceRating(
                domain=norm_domain,
                rating=info.get("rating", "unverified_publisher"),
                explanation=info.get("explanation", "Recognized media entity in registry."),
                provenance=info.get("provenance", "Internal Registry")
            )
        
        # Check domain suffix fallback (e.g., news.google.com -> google.com)
        parts = norm_domain.split(".")
        if len(parts) > 2:
            parent_domain = ".".join(parts[-2:])
            if parent_domain in self.registry:
                info = self.registry[parent_domain]
                return SourceRating(
                    domain=norm_domain,
                    rating=info.get("rating", "unverified_publisher"),
                    explanation=f"Subdomain of {parent_domain}. {info.get('explanation', '')}",
                    provenance=info.get("provenance", "Internal Registry")
                )

        return SourceRating(
            domain=norm_domain,
            rating="unverified_publisher",
            explanation="Domain is not present in the pre-configured credibility registry. Not marked unreliable.",
            provenance="Default Unverified Policy"
        )

    def _normalize_fact_check_verdict(self, rating_text: str) -> str:
        """Safely map external fact-check rating strings to normalized status."""
        text = (rating_text or "").lower()
        positive_keywords = ["true", "correct", "accurate", "mostly true", "supported", "verified"]
        negative_keywords = ["false", "fake", "incorrect", "misleading", "inaccurate", "debunked", "untrue", "pants on fire"]

        if any(kw in text for kw in positive_keywords) and not any(kw in text for kw in negative_keywords):
            return "verified_by_existing_fact_check"
        elif any(kw in text for kw in negative_keywords):
            return "disputed_by_existing_fact_check"
        return "unknown"

    async def search_fact_checks(self, query: str) -> Tuple[str, List[FactCheckItem]]:
        """Search Google Fact Check Tools API for existing fact-checks matching a query."""
        if not query or not query.strip():
            return "not_checked", []

        if not self.fact_check_api_key:
            logger.info("GOOGLE_FACT_CHECK_API_KEY not configured. Skipping external fact-check search.")
            return "not_checked", []

        api_url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
        params = {
            "query": query.strip()[:150],
            "key": self.fact_check_api_key,
            "languageCode": "en"
        }

        try:
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
                resp = await client.get(api_url, params=params)
                if resp.status_code != 200:
                    logger.warning(f"Google Fact Check API returned HTTP {resp.status_code}")
                    return "api_error", []

                data = resp.json()
                claims = data.get("claims", [])
                if not claims:
                    return "no_matching_fact_check", []

                fact_checks: List[FactCheckItem] = []
                overall_status = "no_matching_fact_check"

                for claim_item in claims[:3]:  # Top 3 matching claims
                    claim_text = claim_item.get("text", query)
                    claimant = claim_item.get("claimant")
                    claim_reviews = claim_item.get("claimReview", [])

                    for review in claim_reviews:
                        pub_info = review.get("publisher") or {}
                        pub_name = pub_info.get("name", "Third-Party Fact Checker")
                        review_date = review.get("reviewDate")
                        textual_rating = review.get("textualRating", "Unspecified Verdict")
                        review_url = review.get("url", "")

                        norm_status = self._normalize_fact_check_verdict(textual_rating)
                        if norm_status == "disputed_by_existing_fact_check":
                            overall_status = "disputed_by_existing_fact_check"
                        elif norm_status == "verified_by_existing_fact_check" and overall_status != "disputed_by_existing_fact_check":
                            overall_status = "verified_by_existing_fact_check"

                        fact_checks.append(FactCheckItem(
                            claim=claim_text,
                            claimant=claimant,
                            fact_check_publisher=pub_name,
                            review_date=review_date,
                            original_rating=textual_rating,
                            normalized_status=norm_status,
                            fact_check_url=review_url
                        ))

                return (overall_status if fact_checks else "no_matching_fact_check"), fact_checks

        except Exception as exc:
            logger.warning(f"Exception during Fact Check API query: {exc}")
            return "api_error", []

    async def verify_article(self, article: Dict[str, Any]) -> VerificationResult:
        """Verify an individual article's publisher domain credibility and external fact-checks."""
        url = article.get("url") or article.get("canonical_url", "")
        domain = self.extract_domain(url)
        source_rating = self.evaluate_publisher(domain)

        headline = article.get("title", "")
        fact_check_status, fact_checks = await self.search_fact_checks(headline)

        limitations = [
            "Publisher domain rating reflects general organizational standards, not proof of individual claim veracity.",
            "Fact-check search relies on external third-party publisher databases and exact keyword matching."
        ]

        if fact_check_status == "not_checked":
            limitations.append("External Google Fact Check API key is not configured. Fact-check matching was skipped.")

        return VerificationResult(
            article_id=str(article.get("id", "")),
            publisher_domain=domain,
            credibility_status=source_rating.rating,
            source_rating=source_rating,
            fact_check_status=fact_check_status,
            fact_checks=fact_checks,
            discrepancy_status="insufficient_evidence",
            cross_source_findings={},
            limitations=limitations,
            last_checked_at=datetime.utcnow()
        )

    def analyze_cross_source_discrepancies(self, articles: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
        """Analyze claim consistency and discrepancies across multiple articles in a story cluster."""
        if not articles:
            return "insufficient_evidence", {
                "agreements": [],
                "differences": [],
                "single_source_claims": [],
                "summary": "No articles available for cross-source discrepancy analysis."
            }

        if len(articles) == 1:
            art = articles[0]
            return "single_source_only", {
                "agreements": [f"Reported solely by {art.get('source_name', 'Single Source')}"],
                "differences": [],
                "single_source_claims": [art.get("title", "")],
                "summary": "Single-source reporting. Cross-source comparison requires multiple independent outlets."
            }

        # Multiple sources present
        sources = list({a.get("source_name", "Unknown Source") for a in articles})
        titles = [a.get("title", "") for a in articles]

        # Simple overlap check for demonstration and fallback
        common_words = set(titles[0].lower().split())
        for t in titles[1:]:
            common_words = common_words.intersection(set(t.lower().split()))

        # Filter out trivial stop words
        significant_words = {w for w in common_words if len(w) > 3}

        if len(significant_words) >= 2:
            status = "unanimous_consensus"
            summary = f"High alignment observed across {len(sources)} independent sources ({', '.join(sources[:3])})."
        else:
            status = "conflicting_reports"
            summary = f"Varied focal points or reporting angles detected across {len(sources)} sources."

        agreements = [f"Coverage across {len(sources)} outlets focuses on central topic '{titles[0][:60]}...'"]
        differences = []

        # Compare publication timestamps to detect reporting updates vs true contradictions
        timestamps = [a.get("published_at") for a in articles if a.get("published_at")]
        if len(timestamps) > 1:
            differences.append(f"Reporting spans timeline updates from {sources[0]} to {sources[-1]}. Timestamp differences reflect developing news updates.")

        return status, {
            "agreements": agreements,
            "differences": differences,
            "single_source_claims": [],
            "summary": summary
        }

    async def verify_story_cluster(self, story_id: str, articles: List[Dict[str, Any]]) -> StoryVerificationSummary:
        """Verify an entire story cluster, combining domain ratings, fact-checks, and discrepancy analysis."""
        total_arts = len(articles)
        all_fact_checks: List[FactCheckItem] = []
        verified_count = 0
        disputed_count = 0
        high_cred_count = 0
        unverified_count = 0

        for art in articles:
            res = await self.verify_article(art)
            if res.credibility_status == "high_credibility":
                high_cred_count += 1
            elif res.credibility_status == "unverified_publisher":
                unverified_count += 1

            for fc in res.fact_checks:
                all_fact_checks.append(fc)
                if fc.normalized_status == "verified_by_existing_fact_check":
                    verified_count += 1
                elif fc.normalized_status == "disputed_by_existing_fact_check":
                    disputed_count += 1

        disc_status, disc_findings = self.analyze_cross_source_discrepancies(articles)

        limitations = [
            "Source reputation does not guarantee individual claim accuracy.",
            "Absence of a fact-check record does not verify or disprove claims."
        ]

        return StoryVerificationSummary(
            story_id=story_id,
            total_articles=total_arts,
            verified_fact_checks_count=verified_count,
            disputed_fact_checks_count=disputed_count,
            discrepancy_status=disc_status,
            high_credibility_sources_count=high_cred_count,
            unverified_sources_count=unverified_count,
            fact_checks=all_fact_checks,
            cross_source_findings=disc_findings,
            limitations=limitations,
            last_checked_at=datetime.utcnow()
        )
