from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.story import Story
from app.models.article import Article
from app.schemas.ai import StoryIntelligenceResponse

class IntelligenceService:
    """Service responsible for generating structured AI news intelligence."""

    async def analyze_story(self, story_id: str, db: Session) -> StoryIntelligenceResponse:
        from app.providers.llm import get_llm_provider
        """Fetch story and related articles from SQLite database and synthesize structured intelligence."""
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise ValueError(f"Story with ID '{story_id}' not found.")

        articles = (
            db.query(Article)
            .filter(Article.story_id == story_id)
            .order_by(Article.published_at.asc())
            .all()
        )

        article_dicts = [
            {
                "id": a.id,
                "title": a.title,
                "description": a.description,
                "url": a.url,
                "source_name": a.source_name,
                "author": a.author,
                "image_url": a.image_url,
                "published_at": a.published_at.isoformat() if a.published_at else None,
                "topic": a.topic
            }
            for a in articles
        ]

        if not article_dicts:
            article_dicts = [
                {
                    "id": f"art_{story.id}",
                    "title": story.title,
                    "description": story.summary or story.title,
                    "url": "https://news.google.com",
                    "source_name": "Google News",
                    "published_at": story.earliest_published_at.isoformat() if story.earliest_published_at else None,
                    "topic": story.topic
                }
            ]

        # Invoke LLM provider (or DemoLLMProvider)
        llm = get_llm_provider()
        ai_raw = await llm.analyze_story_intelligence(
            headline=story.title,
            topic=story.topic or "General",
            articles=article_dicts
        )

        # Run verification check for story cluster
        from app.services.credibility import CredibilityVerificationService
        cred_service = CredibilityVerificationService()
        verification_summary_obj = await cred_service.verify_story_cluster(story.id, article_dicts)

        response = StoryIntelligenceResponse(
            story_id=story.id,
            headline=ai_raw.get("headline", story.title),
            topic=ai_raw.get("topic", story.topic or "General"),
            what_happened=ai_raw.get("what_happened", "Summary unavailable."),
            what_changed=ai_raw.get("what_changed", "Insufficient historical coverage to determine a meaningful change."),
            why_it_matters=ai_raw.get("why_it_matters", "Significance under evaluation."),
            key_points=ai_raw.get("key_points", []),
            entities=ai_raw.get("entities", []),
            sources=ai_raw.get("sources", []),
            evidence=ai_raw.get("evidence", []),
            source_comparison=ai_raw.get("source_comparison", []),
            discrepancy_status=verification_summary_obj.discrepancy_status,
            fact_checks=verification_summary_obj.fact_checks,
            verification_summary=verification_summary_obj.model_dump(),
            confidence=ai_raw.get("confidence", "High"),
            is_demo=ai_raw.get("is_demo", True)
        )

        # Update story summary fields in database
        story.summary = response.what_happened
        story.what_changed = response.what_changed
        story.why_it_matters = response.why_it_matters
        story.discrepancy_status = verification_summary_obj.discrepancy_status
        story.fact_check_status = verification_summary_obj.overall_status
        db.commit()

        return response
