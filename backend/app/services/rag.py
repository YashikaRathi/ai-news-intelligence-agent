from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.article import Article
from app.schemas.ai import ChatResponse, ChatSourceItem

class RAGService:
    """Service responsible for RAG (Retrieval-Augmented Generation) Q&A grounded in news articles."""

    async def ask_news(
        self,
        question: str,
        story_id: Optional[str],
        db: Session
    ) -> ChatResponse:
        """RETRIEVE FIRST -> GENERATE SECOND."""
        from app.providers.llm import get_llm_provider

        if not question or not question.strip():
            return ChatResponse(
                answer="Please provide a non-empty question to query the news database.",
                sources=[],
                is_demo=False
            )

        # 1. RETRIEVE context articles from SQLite
        query_builder = db.query(Article)

        if story_id:
            context_articles = query_builder.filter(Article.story_id == story_id).all()
        else:
            # Full-text / keyword query retrieval from SQLite
            keywords = [f"%{w.strip()}%" for w in question.split() if len(w.strip()) > 3]
            if keywords:
                filters = [
                    or_(
                        Article.title.ilike(kw),
                        Article.description.ilike(kw),
                        Article.topic.ilike(kw)
                    )
                    for kw in keywords[:3]
                ]
                context_articles = query_builder.filter(or_(*filters)).limit(5).all()
            else:
                context_articles = query_builder.order_by(Article.published_at.desc()).limit(5).all()

        if not context_articles:
            return ChatResponse(
                answer="I couldn't find enough evidence in the available coverage to answer that reliably.",
                sources=[],
                is_demo=False
            )

        article_dicts = [
            {
                "id": a.id,
                "title": a.title,
                "description": a.description,
                "url": a.url,
                "source_name": a.source_name,
                "published_at": a.published_at.isoformat() if a.published_at else None
            }
            for a in context_articles
        ]

        # 2. GENERATE grounded answer with active LLM Provider
        llm = get_llm_provider()
        ai_response = await llm.answer_rag_question(
            question=question,
            context_articles=article_dicts
        )

        sources = [
            ChatSourceItem(
                article_id=s.get("article_id", ""),
                source=s.get("source", "Unknown"),
                title=s.get("title", ""),
                url=s.get("url", "")
            )
            for s in ai_response.get("sources", [])
        ]

        return ChatResponse(
            answer=ai_response.get("answer", "I couldn't find enough evidence in the available coverage to answer that reliably."),
            sources=sources,
            is_demo=ai_response.get("is_demo", True)
        )
