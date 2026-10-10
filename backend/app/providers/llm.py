import os
import json
import logging
import httpx
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from app.services.prompts import (
    SYSTEM_NEWS_INTELLIGENCE_PROMPT,
    STORY_INTELLIGENCE_USER_PROMPT_TEMPLATE,
    SYSTEM_RAG_CHAT_PROMPT,
    RAG_CHAT_USER_PROMPT_TEMPLATE,
    SYSTEM_CLAIM_EXTRACTION_PROMPT,
    CLAIM_EXTRACTION_USER_PROMPT_TEMPLATE,
)

load_dotenv()
logger = logging.getLogger(__name__)

class BaseLLMProvider(ABC):
    """Abstract Base Class for LLM Provider abstraction."""

    def __init__(self):
        self.api_key: Optional[str] = os.getenv("LLM_API_KEY")
        self.model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.provider_name: str = os.getenv("LLM_PROVIDER", "openai")

    @abstractmethod
    async def analyze_story_intelligence(
        self,
        headline: str,
        topic: str,
        articles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Synthesize structured story intelligence (What Happened, What Changed, Why It Matters)."""
        pass

    @abstractmethod
    async def answer_rag_question(
        self,
        question: str,
        context_articles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate grounded RAG answer based on retrieved article evidence context."""
        pass

    @abstractmethod
    async def extract_article_claims(
        self,
        article_id: str,
        title: str,
        content: str,
        url: str
    ) -> Dict[str, Any]:
        """Extract up to 5 verifiable factual claims from article content."""
        pass


class DemoLLMProvider(BaseLLMProvider):
    """Deterministic local LLM provider for DEMO_MODE or when no valid API key is available."""

    async def analyze_story_intelligence(
        self,
        headline: str,
        topic: str,
        articles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        logger.info("DemoLLMProvider analyzing story intelligence from stored article evidence.")
        
        # Sort articles chronologically
        sorted_arts = sorted(
            articles,
            key=lambda x: str(x.get("published_at") or "")
        )

        sources = list({a.get("source_name", "Unknown Source") for a in articles})
        
        # Deduce "What Happened"
        earliest_desc = sorted_arts[0].get("description", "") if sorted_arts else ""
        what_happened = (
            f"Factual synthesis: {headline}. "
            f"Coverage across {len(articles)} source(s) ({', '.join(sources)}) details "
            f"the core event development: {earliest_desc[:220]}"
        )

        # Deduce "What Changed" (Compare earliest vs latest article)
        if len(sorted_arts) > 1:
            latest_art = sorted_arts[-1]
            what_changed = (
                f"Latest development from {latest_art.get('source_name', 'recent coverage')}: "
                f"'{latest_art.get('title', '')}'. "
                f"Shift observed from initial coverage to updated announcement."
            )
        else:
            what_changed = "Insufficient historical coverage to determine a meaningful change."

        why_it_matters = (
            f"Significance: This development in {topic} impacts industry stakeholders, "
            f"technical implementations, and market dynamics across reporting entities."
        )

        # Build evidence items
        evidence = [
            {
                "article_id": a.get("id", ""),
                "source_name": a.get("source_name", "Unknown"),
                "title": a.get("title", ""),
                "url": a.get("url", ""),
                "published_at": a.get("published_at")
            }
            for a in articles
        ]

        # Build source comparison items
        source_comparison = [
            {
                "source_name": a.get("source_name", "Unknown"),
                "headline": a.get("title", ""),
                "url": a.get("url", ""),
                "published_at": a.get("published_at"),
                "emphasis": f"Focuses on {a.get('title', '')[:80]}...",
                "differences": f"Unique angle reported by {a.get('source_name', 'source')}.",
                "agreement": "Agrees on the central event facts and timing."
            }
            for a in articles[:5]
        ]

        key_points = [a.get("title", "") for a in articles[:4]]
        entities = [s for s in sources] + [topic]

        return {
            "headline": headline,
            "topic": topic,
            "what_happened": what_happened,
            "what_changed": what_changed,
            "why_it_matters": why_it_matters,
            "key_points": key_points,
            "entities": entities,
            "sources": sources,
            "evidence": evidence,
            "source_comparison": source_comparison,
            "confidence": "High (Demo Grounded)",
            "is_demo": True
        }

    async def answer_rag_question(
        self,
        question: str,
        context_articles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not context_articles:
            return {
                "answer": "I couldn't find enough evidence in the available coverage to answer that reliably.",
                "sources": [],
                "is_demo": True
            }

        q_lower = question.lower().strip()

        # Sort articles chronologically
        sorted_arts = sorted(
            context_articles,
            key=lambda x: str(x.get("published_at") or "")
        )

        # Unique sources set
        unique_sources_map: Dict[str, Dict[str, Any]] = {}
        for a in context_articles:
            key = a.get("id") or a.get("url") or a.get("title")
            if key and key not in unique_sources_map:
                unique_sources_map[key] = {
                    "article_id": a.get("id", ""),
                    "source": a.get("source_name", "Unknown Source"),
                    "title": a.get("title", ""),
                    "url": a.get("url", "")
                }
        sources = list(unique_sources_map.values())
        source_names = list({s["source"] for s in sources})
        source_count = len(source_names)
        source_str = f"({', '.join(source_names)})" if source_names else ""

        latest_art = sorted_arts[-1] if sorted_arts else context_articles[0]
        earliest_art = sorted_arts[0] if sorted_arts else context_articles[0]

        # Categorize Question Intent to construct question-specific answers
        if any(w in q_lower for w in ["latest", "recent", "newest", "update", "current"]):
            answer = (
                f"LATEST DEVELOPMENT: According to recent reporting from {latest_art.get('source_name', 'sources')}, "
                f"'{latest_art.get('title', '')}'. "
                f"Summary: {latest_art.get('description', 'Latest updates have been logged.')}"
            )
        elif any(w in q_lower for w in ["why", "important", "significance", "matter", "impact"]):
            answer = (
                f"SIGNIFICANCE & IMPACT: This story is important because it represents major developments reported across "
                f"{source_count} outlet(s) {source_str}. "
                f"The core situation ('{latest_art.get('title', '')}') directly affects emergency relief operations, "
                f"local infrastructure, and regional policy response."
            )
        elif any(w in q_lower for w in ["change", "changed", "earlier", "previous", "shift", "differ"]):
            if len(sorted_arts) > 1:
                answer = (
                    f"TIMELINE SHIFT: Earlier reports from {earliest_art.get('source_name', 'initial coverage')} focused on "
                    f"'{earliest_art.get('title', '')}'. "
                    f"Subsequent developments reported by {latest_art.get('source_name', 'latest coverage')} indicate "
                    f"'{latest_art.get('title', '')}'."
                )
            else:
                answer = (
                    f"COVERAGE ANALYSIS: All available reporting from {latest_art.get('source_name', 'the source')} currently "
                    f"focuses on '{latest_art.get('title', '')}'. Historical comparison is limited to current initial dispatches."
                )
        elif any(w in q_lower for w in ["sources", "who reported", "outlets", "media", "which source"]):
            art_titles = [f"• {a.get('source_name')}: '{a.get('title')}'" for a in context_articles[:4]]
            answer = (
                f"SOURCE COVERAGE SUMMARY: This story is being reported by {source_count} unique news outlet(s) {source_str}.\n"
                + "\n".join(art_titles)
            )
        elif any(w in q_lower for w in ["facts", "main facts", "key facts", "summary", "overview"]):
            facts = [f"1. {a.get('title')} ({a.get('source_name')})" for a in context_articles[:3]]
            answer = (
                f"VERIFIED CORE FACTS:\n" + "\n".join(facts)
            )
        elif any(w in q_lower for w in ["next", "future", "predict", "ahead", "happen next"]):
            answer = (
                "The available news reports do not provide enough verified evidence to predict future outcomes reliably. "
                "Current coverage focuses on active relief and ongoing operational efforts."
            )
        else:
            # Fallback for general custom question
            answer = (
                f"GROUNDED RESPONSE for '{question}': Based on coverage from {latest_art.get('source_name', 'reporting')} "
                f"('{latest_art.get('title', '')}'): {latest_art.get('description', '')}"
            )

        return {
            "answer": answer,
            "sources": sources,
            "is_demo": True
        }

    async def extract_article_claims(
        self,
        article_id: str,
        title: str,
        content: str,
        url: str
    ) -> Dict[str, Any]:
        text = (content or "").strip()
        title_text = (title or "").strip()
        combined_text = f"{title_text} {text}".strip()

        if not combined_text:
            return {
                "article_id": article_id,
                "article_title": title,
                "article_url": url,
                "claims": [],
                "extraction_status": "missing_text",
                "summary": "Article content is missing or empty.",
                "is_demo": True
            }

        text_lower = combined_text.lower()

        # Detect pure opinion / speculative / non-factual text
        opinion_markers = [
            "opinion:", "in my view", "i think", "in my opinion", "editorial:", "should be banned",
            "the future is bright", "must realize", "i feel", "pure speculation", "i believe"
        ]
        is_opinion_only = any(marker in text_lower for marker in opinion_markers) and not any(
            w in text_lower for w in ["announced", "reported", "said", "percent", "stipulated", "confirmed", "increased", "decreased", "launched", "unveiled", "signed"]
        )

        if is_opinion_only:
            return {
                "article_id": article_id,
                "article_title": title,
                "article_url": url,
                "claims": [],
                "extraction_status": "no_factual_claims_found",
                "summary": "No checkable factual claims found in opinion or speculative text.",
                "is_demo": True
            }

        # Deterministic factual claims extraction for demo mode
        claims = []

        # Claim 1: Headline factual claim
        claims.append({
            "claim_text": f"Core event reported: '{title_text}'",
            "claim_type": "factual",
            "entities": [title_text.split()[0]] if title_text else [],
            "relevant_dates": None,
            "quantities_or_locations": None,
            "original_article_id": article_id,
            "original_article_url": url,
            "extraction_status": "success"
        })

        # Claim 2: Body text assertion if present
        if len(text) > 20:
            snippet = text[:150].strip()
            claims.append({
                "claim_text": f"Source reporting details: '{snippet}'",
                "claim_type": "factual",
                "entities": [],
                "relevant_dates": None,
                "quantities_or_locations": None,
                "original_article_id": article_id,
                "original_article_url": url,
                "extraction_status": "success"
            })

        return {
            "article_id": article_id,
            "article_title": title,
            "article_url": url,
            "claims": claims[:5],
            "extraction_status": "demo_mode",
            "summary": f"Extracted {len(claims[:5])} simulated claim(s) in demo mode.",
            "is_demo": True
        }


class OpenAILLMProvider(BaseLLMProvider):
    """Concrete OpenAI API implementation using httpx HTTP client."""

    async def analyze_story_intelligence(
        self,
        headline: str,
        topic: str,
        articles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_llm_api_key_here":
            logger.warning("No valid LLM_API_KEY found. Falling back to DemoLLMProvider.")
            return await DemoLLMProvider().analyze_story_intelligence(headline, topic, articles)

        evidence_str = "\n".join([
            f"- Source: {a.get('source_name')}\n  Title: {a.get('title')}\n  Published: {a.get('published_at')}\n  Snippet: {a.get('description', '')[:250]}"
            for a in articles
        ])

        user_prompt = STORY_INTELLIGENCE_USER_PROMPT_TEMPLATE.format(
            headline=headline,
            topic=topic,
            evidence_text=evidence_str
        )

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": SYSTEM_NEWS_INTELLIGENCE_PROMPT},
                            {"role": "user", "content": user_prompt}
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.2
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    parsed["is_demo"] = False
                    
                    # Attach evidence citations with exact stored URLs
                    parsed["evidence"] = [
                        {
                            "article_id": a.get("id", ""),
                            "source_name": a.get("source_name", "Unknown"),
                            "title": a.get("title", ""),
                            "url": a.get("url", ""),
                            "published_at": a.get("published_at")
                        }
                        for a in articles
                    ]
                    return parsed
                else:
                    logger.error(f"OpenAI API Error HTTP {resp.status_code}: {resp.text}")
        except Exception as exc:
            logger.error(f"Failed to query OpenAI API: {exc}")

        # Fallback to DemoLLMProvider on API failure
        return await DemoLLMProvider().analyze_story_intelligence(headline, topic, articles)

    async def answer_rag_question(
        self,
        question: str,
        context_articles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_llm_api_key_here":
            return await DemoLLMProvider().answer_rag_question(question, context_articles)

        if not context_articles:
            return {
                "answer": "I couldn't find enough evidence in the available coverage to answer that reliably.",
                "sources": [],
                "is_demo": False
            }

        # Deduplicate sources by ID / URL
        unique_sources_map: Dict[str, Dict[str, Any]] = {}
        for a in context_articles:
            key = a.get("id") or a.get("url") or a.get("title")
            if key and key not in unique_sources_map:
                unique_sources_map[key] = {
                    "article_id": a.get("id", ""),
                    "source": a.get("source_name", "Unknown Source"),
                    "title": a.get("title", ""),
                    "url": a.get("url", "")
                }
        sources = list(unique_sources_map.values())

        context_str = "\n".join([
            f"Article ID: {a.get('id')}\nSource: {a.get('source_name')}\nTitle: {a.get('title')}\nURL: {a.get('url')}\nContent: {a.get('description', '')}"
            for a in context_articles
        ])

        user_prompt = RAG_CHAT_USER_PROMPT_TEMPLATE.format(
            question=question,
            context_text=context_str
        )

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": SYSTEM_RAG_CHAT_PROMPT},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.1
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    answer_text = data["choices"][0]["message"]["content"].strip()
                    
                    return {
                        "answer": answer_text,
                        "sources": sources,
                        "is_demo": False
                    }
        except Exception as exc:
            logger.error(f"Failed RAG query to OpenAI API: {exc}")

        return await DemoLLMProvider().answer_rag_question(question, context_articles)

    async def extract_article_claims(
        self,
        article_id: str,
        title: str,
        content: str,
        url: str
    ) -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_llm_api_key_here":
            return await DemoLLMProvider().extract_article_claims(article_id, title, content, url)

        combined = f"{title or ''}\n{content or ''}".strip()
        if not combined:
            return {
                "article_id": article_id,
                "article_title": title,
                "article_url": url,
                "claims": [],
                "extraction_status": "missing_text",
                "summary": "Article content is missing or empty.",
                "is_demo": False
            }

        user_prompt = CLAIM_EXTRACTION_USER_PROMPT_TEMPLATE.format(
            title=title or "",
            content=content or ""
        )

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": SYSTEM_CLAIM_EXTRACTION_PROMPT},
                            {"role": "user", "content": user_prompt}
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.1
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    raw_content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(raw_content)

                    status = parsed.get("extraction_status", "success")
                    summary = parsed.get("summary", "Claims extracted successfully.")
                    raw_claims = parsed.get("claims", [])

                    formatted_claims = []
                    for c in raw_claims[:5]:
                        c_text = c.get("claim_text")
                        if c_text:
                            formatted_claims.append({
                                "claim_text": c_text,
                                "claim_type": c.get("claim_type", "factual"),
                                "entities": c.get("entities", []),
                                "relevant_dates": c.get("relevant_dates"),
                                "quantities_or_locations": c.get("quantities_or_locations"),
                                "original_article_id": article_id,
                                "original_article_url": url,
                                "extraction_status": "success"
                            })

                    return {
                        "article_id": article_id,
                        "article_title": title,
                        "article_url": url,
                        "claims": formatted_claims,
                        "extraction_status": status,
                        "summary": summary,
                        "is_demo": False
                    }
        except Exception as exc:
            logger.error(f"Failed claim extraction query to OpenAI API: {exc}")

        return await DemoLLMProvider().extract_article_claims(article_id, title, content, url)



def get_llm_provider() -> BaseLLMProvider:
    """Factory function returning active LLM provider (or DemoLLMProvider if DEMO_MODE=true or no key)."""
    demo_mode = os.getenv("DEMO_MODE", "false").lower() in ["true", "1", "yes"]
    api_key = os.getenv("LLM_API_KEY")

    if demo_mode or not api_key or api_key == "your_llm_api_key_here":
        return DemoLLMProvider()

    provider_type = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider_type == "openai":
        return OpenAILLMProvider()

    return DemoLLMProvider()
