import os
import logging
import urllib.parse
import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from app.schemas.verification import (
    SourceRating,
    FactCheckItem,
    VerificationResult,
    StoryVerificationSummary,
)

logger = logging.getLogger(__name__)

# Configurable Registry of Known Publisher Domains with documented methodology
DEFAULT_CREDIBILITY_REGISTRY: Dict[str, Dict[str, str]] = {
    "bbc.com": {
        "assessment_status": "rated",
        "rating": "high_credibility",
        "explanation": "Established international public broadcaster operating under a Royal Charter with published editorial guidelines and mandatory public correction notices.",
        "provenance": "Editorial Policy Audit Registry"
    },
    "bbc.co.uk": {
        "assessment_status": "rated",
        "rating": "high_credibility",
        "explanation": "Established international public broadcaster with strict editorial guidelines and transparent correction procedures.",
        "provenance": "Editorial Policy Audit Registry"
    },
    "theguardian.com": {
        "assessment_status": "rated",
        "rating": "high_credibility",
        "explanation": "Major independent news organization with transparent correction policies and Scott Trust governance preventing commercial bias.",
        "provenance": "Editorial Policy Audit Registry"
    },
    "techcrunch.com": {
        "assessment_status": "rated",
        "rating": "high_credibility",
        "explanation": "Established technology journalism publication adhering to commercial disclosure guidelines for tech and venture news.",
        "provenance": "Industry Media Registry"
    },
    "npr.org": {
        "assessment_status": "rated",
        "rating": "high_credibility",
        "explanation": "Non-profit public media organization with independent journalism standards and ombudsperson accountability.",
        "provenance": "Public Media Registry"
    },
    "reuters.com": {
        "assessment_status": "rated",
        "rating": "high_credibility",
        "explanation": "Global news wire service operating under the Thomson Reuters Trust Principles of independence and freedom from bias.",
        "provenance": "Global News Agency Registry"
    },
    "apnews.com": {
        "assessment_status": "rated",
        "rating": "high_credibility",
        "explanation": "Independent global news cooperative producing verified wire reporting and adhering to the AP News Values and Principles.",
        "provenance": "Global News Agency Registry"
    },
    "nytimes.com": {
        "assessment_status": "rated",
        "rating": "high_credibility",
        "explanation": "Major newspaper of record with comprehensive fact-checking standards, detailed corrections policy, and strict sourcing guidelines.",
        "provenance": "Major Media Registry"
    },
    "washingtonpost.com": {
        "assessment_status": "rated",
        "rating": "high_credibility",
        "explanation": "Established investigative journalism publication with transparent editorial standards and dedicated fact-checking staff.",
        "provenance": "Major Media Registry"
    },
    "bloomberg.com": {
        "assessment_status": "rated",
        "rating": "high_credibility",
        "explanation": "Financial news provider with strict market reporting accuracy policies and Bloomberg News Editorial Standards.",
        "provenance": "Financial Media Registry"
    },
    "theverge.com": {
        "assessment_status": "rated",
        "rating": "medium_credibility",
        "explanation": "Technology news outlet covering tech trends, product reviews, and culture with standard digital journalism practices.",
        "provenance": "Tech Media Registry"
    },
    "wired.com": {
        "assessment_status": "rated",
        "rating": "medium_credibility",
        "explanation": "Established tech and culture magazine providing analysis, reporting, and commentary with Conde Nast editorial oversight.",
        "provenance": "Tech Media Registry"
    }
}

class CredibilityVerificationService:
    """Service evaluating publisher credibility, external fact-check matching, and cross-source coverage consistency."""

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
        """Evaluate a publisher domain against the credibility registry.
        
        Important requirement: Unknown publishers are marked 'Not assessed', NOT classified as fake or unreliable.
        Publisher reputation is kept strictly separate from the truthfulness of an individual article.
        """
        norm_domain = domain.lower().strip()
        if norm_domain in self.registry:
            info = self.registry[norm_domain]
            return SourceRating(
                domain=norm_domain,
                assessment_status="rated",
                rating=info.get("rating", "high_credibility"),
                explanation=info.get("explanation", "Recognized media entity in registry."),
                provenance=info.get("provenance", "Editorial Policy Audit Registry"),
                limitations="Publisher reputation reflects historical editorial governance, not proof of individual claim veracity."
            )
        
        # Check domain suffix fallback (e.g., news.google.com -> google.com)
        parts = norm_domain.split(".")
        if len(parts) > 2:
            parent_domain = ".".join(parts[-2:])
            if parent_domain in self.registry:
                info = self.registry[parent_domain]
                return SourceRating(
                    domain=norm_domain,
                    assessment_status="rated",
                    rating=info.get("rating", "high_credibility"),
                    explanation=f"Subdomain of {parent_domain}. {info.get('explanation', '')}",
                    provenance=info.get("provenance", "Editorial Policy Audit Registry"),
                    limitations="Publisher reputation reflects parent organization standards."
                )

        return SourceRating(
            domain=norm_domain,
            assessment_status="not_assessed",
            rating="not_assessed",
            explanation="This publisher domain is not currently indexed in our editorial audit registry. An unassessed status does not indicate unreliability or lack of accuracy.",
            provenance="Default Unassessed Policy",
            limitations="No formal assessment available. Readers should review reported citations and cross-source consensus directly."
        )

    def _normalize_fact_check_verdict(self, rating_text: str) -> str:
        """Safely map external fact-check rating strings to nuanced normalized status.
        
        Statuses:
        - 'Fact-check rated TRUE'
        - 'Fact-check rated FALSE'
        - 'Mixed or partially true'
        - 'unknown'
        """
        text = (rating_text or "").lower().strip()
        
        # Check mixed / partially true first
        mixed_keywords = [
            "mixed", "partially true", "half true", "partly true", "mostly false",
            "mostly true", "needs context", "missing context", "half truth", "unproven",
            "misleading", "in dispute", "exaggerated", "cherry-picked", "unsupported"
        ]
        if any(kw in text for kw in mixed_keywords):
            return "Mixed or partially true"

        # Explicit FALSE
        false_keywords = [
            "false", "fake", "incorrect", "debunked", "untrue", "pants on fire",
            "fabricated", "hoax", "inaccurate", "scam", "wrong", "disproven"
        ]
        if any(kw in text for kw in false_keywords):
            return "Fact-check rated FALSE"

        # Explicit TRUE
        true_keywords = [
            "true", "correct", "accurate", "verified", "supported", "confirmed"
        ]
        if any(kw in text for kw in true_keywords):
            return "Fact-check rated TRUE"

        return "unknown"

    async def search_fact_checks(self, query: str) -> Tuple[str, List[FactCheckItem]]:
        """Search Google Fact Check Tools API for existing third-party fact-checks matching a query.
        
        Returns:
            Tuple[status, List[FactCheckItem]]
            status is one of:
            - 'Fact-check rated TRUE'
            - 'Fact-check rated FALSE'
            - 'Mixed or partially true'
            - 'No matching fact-check found'
            - 'Not checked'
        """
        if not query or not query.strip():
            return "Not checked", []

        if not self.fact_check_api_key:
            logger.info("GOOGLE_FACT_CHECK_API_KEY not configured. Skipping external fact-check search.")
            return "Not checked", []

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
                    return "Not checked", []

                data = resp.json()
                claims = data.get("claims", [])
                if not claims:
                    return "No matching fact-check found", []

                fact_checks: List[FactCheckItem] = []
                has_false = False
                has_mixed = False
                has_true = False

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
                        if norm_status == "Fact-check rated FALSE":
                            has_false = True
                        elif norm_status == "Mixed or partially true":
                            has_mixed = True
                        elif norm_status == "Fact-check rated TRUE":
                            has_true = True

                        fact_checks.append(FactCheckItem(
                            claim=claim_text,
                            claimant=claimant,
                            fact_check_publisher=pub_name,
                            review_date=review_date,
                            original_rating=textual_rating,
                            normalized_status=norm_status,
                            fact_check_url=review_url
                        ))

                if not fact_checks:
                    return "No matching fact-check found", []

                if has_false:
                    overall = "Fact-check rated FALSE"
                elif has_mixed:
                    overall = "Mixed or partially true"
                elif has_true:
                    overall = "Fact-check rated TRUE"
                else:
                    overall = "No matching fact-check found"

                return overall, fact_checks

        except Exception as exc:
            logger.warning(f"Exception during Fact Check API query: {exc}")
            return "Not checked", []

    async def verify_article(self, article: Dict[str, Any]) -> VerificationResult:
        """Verify an individual article's publisher domain credibility and external fact-checks."""
        url = article.get("url") or article.get("canonical_url", "")
        domain = self.extract_domain(url)
        source_rating = self.evaluate_publisher(domain)

        headline = article.get("title", "")
        fact_check_status, fact_checks = await self.search_fact_checks(headline)

        # Determine overall verification status and clear rationale
        if fact_check_status in ["Fact-check rated TRUE", "Fact-check rated FALSE", "Mixed or partially true"]:
            overall_status = fact_check_status
            fc_first = fact_checks[0] if fact_checks else None
            pub = fc_first.fact_check_publisher if fc_first else "an external fact-checker"
            rating = fc_first.original_rating if fc_first else fact_check_status
            status_reason = f"External fact-checker {pub} evaluated this claim and assigned rating: '{rating}'."
        elif fact_check_status == "No matching fact-check found":
            overall_status = "No matching fact-check found"
            status_reason = "No matching third-party fact-check review was located for this specific headline or claim."
        elif fact_check_status == "Not checked":
            overall_status = "Not checked"
            status_reason = "External fact-check lookup was not executed (API service unconfigured or unavailable)."
        else:
            overall_status = "Insufficient evidence"
            status_reason = "Available evidence is inadequate to reach a definitive truthfulness conclusion."

        limitations = [
            "Publisher reputation reflects organizational governance and correction transparency, not independent proof of this specific claim.",
            "Fact-check searches rely on third-party publisher databases and exact keyword matching.",
            "Absence of an external fact-check record does NOT confirm or refute the claims made in this article."
        ]

        if fact_check_status == "Not checked":
            limitations.append("External Google Fact Check API key is unconfigured. Fact-check matching was skipped.")

        now_utc = datetime.now(timezone.utc)
        return VerificationResult(
            article_id=str(article.get("id", "")),
            publisher_domain=domain,
            overall_status=overall_status,
            status_reason=status_reason,
            publisher_credibility_status=source_rating.assessment_status,
            source_rating=source_rating,
            fact_check_status=fact_check_status,
            fact_checks=fact_checks,
            discrepancy_status="Insufficient evidence",
            cross_source_findings={},
            limitations=limitations,
            last_checked_at=now_utc,
            credibility_status=source_rating.rating  # Backward compatibility
        )

    def analyze_cross_source_discrepancies(self, articles: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
        """Analyze claim consistency and discrepancies across multiple articles in a story cluster.
        
        Distinguishes:
        - Independent reporting from syndicated or duplicate articles
        - High multi-source alignment vs conflicting reports
        - Single-source claims (without treating them as automatically false)
        - Clickable citations with timestamps
        """
        if not articles:
            return "Insufficient evidence", {
                "agreements": [],
                "differences": [],
                "single_source_claims": [],
                "independent_sources": [],
                "syndicated_sources": [],
                "summary": "No articles available for cross-source discrepancy analysis.",
                "citations": []
            }

        # Build citations list with clickable titles and sources
        citations = [
            {
                "article_id": a.get("id"),
                "title": a.get("title"),
                "source_name": a.get("source_name", "Unknown Source"),
                "url": a.get("url") or a.get("canonical_url", ""),
                "published_at": a.get("published_at"),
                "is_duplicate": a.get("is_duplicate", False)
            }
            for a in articles
        ]

        if len(articles) == 1:
            art = articles[0]
            src = art.get("source_name", "Single Source")
            return "Insufficient evidence", {
                "agreements": [f"Reported solely by {src}"],
                "differences": [],
                "single_source_claims": [art.get("title", "")],
                "independent_sources": [src],
                "syndicated_sources": [],
                "summary": f"Single-source reporting from {src}. Single-source claims are not automatically false, but require additional independent reporting to establish cross-source consensus.",
                "citations": citations
            }

        # Distinguish independent sources from syndicated duplicates
        independent_sources: List[str] = []
        syndicated_sources: List[str] = []
        seen_titles = set()

        for a in articles:
            src = a.get("source_name", "Unknown Source")
            title_norm = a.get("title", "").strip().lower()
            if a.get("is_duplicate") or title_norm in seen_titles:
                syndicated_sources.append(src)
            else:
                seen_titles.add(title_norm)
                if src not in independent_sources:
                    independent_sources.append(src)

        sources_unique = list(set([a.get("source_name", "Unknown Source") for a in articles]))
        titles = [a.get("title", "") for a in articles]

        # Overlap check across independent titles
        words_sets = [set(t.lower().split()) for t in titles if t]
        if words_sets:
            common_words = set.intersection(*words_sets)
            significant_words = {w for w in common_words if len(w) > 3}
        else:
            significant_words = set()

        # Check for conflicting keyword signals in headlines
        conflict_markers = ["denies", "refutes", "contradicts", "disputes", "doubts", "clash", "divided", "untrue", "false"]
        headline_conflicts = [t for t in titles if any(m in t.lower() for m in conflict_markers)]

        if len(independent_sources) >= 2 and len(significant_words) >= 2 and not headline_conflicts:
            status = "Unanimous consensus"
            summary = f"Strong agreement observed across {len(independent_sources)} independent media outlets ({', '.join(independent_sources[:3])})."
        elif headline_conflicts or (len(independent_sources) >= 2 and len(significant_words) < 1):
            status = "Conflicting reports"
            summary = f"Noticeable divergence or contradictory reporting angles detected across {len(independent_sources)} independent sources."
        else:
            status = "Insufficient evidence"
            summary = f"Limited independent coverage across {len(independent_sources)} source(s); insufficient evidence to confirm cross-source consensus."

        agreements = [
            f"Coverage across {len(sources_unique)} outlet(s) focuses on central event: '{titles[0][:60]}...'"
        ]

        differences = []
        if headline_conflicts:
            differences.append(f"Contradictory framing identified: '{headline_conflicts[0][:80]}...'")

        # Check publication timestamps for developing news updates
        timestamps = [a.get("published_at") for a in articles if a.get("published_at")]
        if len(timestamps) > 1:
            differences.append(f"Coverage spans timeline updates. Timestamp variations reflect developing reporting rather than factual conflict.")

        single_source_claims = []
        if len(independent_sources) == 1:
            single_source_claims.append(titles[0])

        return status, {
            "agreements": agreements,
            "differences": differences,
            "single_source_claims": single_source_claims,
            "independent_sources": independent_sources,
            "syndicated_sources": syndicated_sources,
            "summary": summary,
            "citations": citations
        }

    async def verify_story_cluster(self, story_id: str, articles: List[Dict[str, Any]]) -> StoryVerificationSummary:
        """Verify an entire story cluster, combining domain ratings, fact-checks, and discrepancy analysis."""
        total_arts = len(articles)
        all_fact_checks: List[FactCheckItem] = []
        verified_count = 0
        disputed_count = 0
        high_cred_count = 0
        not_assessed_count = 0

        has_fact_check_false = False
        has_fact_check_true = False
        has_fact_check_mixed = False

        for art in articles:
            res = await self.verify_article(art)
            if res.source_rating and res.source_rating.assessment_status == "rated" and res.source_rating.rating == "high_credibility":
                high_cred_count += 1
            else:
                not_assessed_count += 1

            for fc in res.fact_checks:
                all_fact_checks.append(fc)
                if fc.normalized_status == "Fact-check rated TRUE":
                    verified_count += 1
                    has_fact_check_true = True
                elif fc.normalized_status == "Fact-check rated FALSE":
                    disputed_count += 1
                    has_fact_check_false = True
                elif fc.normalized_status == "Mixed or partially true":
                    has_fact_check_mixed = True

        disc_status, disc_findings = self.analyze_cross_source_discrepancies(articles)

        # Determine overall verification status for the story cluster
        if has_fact_check_false:
            overall_status = "Fact-check rated FALSE"
            status_reason = "An external fact-checker explicitly rated a central claim in this story as false/fabricated."
        elif has_fact_check_mixed:
            overall_status = "Mixed or partially true"
            status_reason = "An external fact-checker reviewed claims in this story with a mixed/partially true rating."
        elif has_fact_check_true:
            overall_status = "Fact-check rated TRUE"
            status_reason = "An external fact-checker explicitly verified and confirmed the primary claim."
        elif disc_status == "Conflicting reports":
            overall_status = "Conflicting reports"
            status_reason = "Independent news sources report conflicting accounts or divergent claims."
        elif total_arts < 2 or disc_status == "Insufficient evidence":
            overall_status = "Insufficient evidence"
            status_reason = "Evidence from available coverage is insufficient to reach a definitive consensus verdict."
        elif not self.fact_check_api_key:
            overall_status = "Not checked"
            status_reason = "External fact-check verification was not performed."
        else:
            overall_status = "No matching fact-check found"
            status_reason = "No matching third-party fact-check review was found in public registries."

        limitations = [
            "Source reputation reflects organizational standards and policies, not individual claim accuracy.",
            "Absence of an external fact-check record does not confirm or refute reporting.",
            "Cross-source consensus reflects agreement among retrieved articles, not independent scientific proof."
        ]

        now_utc = datetime.now(timezone.utc)
        return StoryVerificationSummary(
            story_id=story_id,
            total_articles=total_arts,
            overall_status=overall_status,
            status_reason=status_reason,
            verified_fact_checks_count=verified_count,
            disputed_fact_checks_count=disputed_count,
            discrepancy_status=disc_status,
            high_credibility_sources_count=high_cred_count,
            not_assessed_sources_count=not_assessed_count,
            unverified_sources_count=not_assessed_count,  # Backward compatibility
            fact_checks=all_fact_checks,
            cross_source_findings=disc_findings,
            limitations=limitations,
            last_checked_at=now_utc
        )
