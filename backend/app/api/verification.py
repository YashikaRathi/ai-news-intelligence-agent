from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from app.db.session import get_db
from app.models.article import Article
from app.models.story import Story
from app.schemas.verification import VerificationResult, StoryVerificationSummary
from app.services.credibility import CredibilityVerificationService

router = APIRouter(prefix="/verification", tags=["Credibility & Fact Check Verification"])

credibility_service = CredibilityVerificationService()

@router.get("/article/{article_id}", response_model=VerificationResult)
async def get_article_verification(article_id: str, db: Session = Depends(get_db)):
    """Retrieve publisher domain credibility, fact-check records, and discrepancy status for a specific article."""
    art = db.query(Article).filter(Article.id == article_id).first()
    if not art:
        raise HTTPException(status_code=404, detail=f"Article with ID '{article_id}' not found.")

    art_dict = {
        "id": art.id,
        "title": art.title,
        "url": art.url,
        "canonical_url": art.canonical_url,
        "source_name": art.source_name,
        "published_at": art.published_at
    }

    result = await credibility_service.verify_article(art_dict)
    
    # Update DB fields if changed
    if art.credibility_status != result.credibility_status or art.fact_check_status != result.fact_check_status:
        art.publisher_domain = result.publisher_domain
        art.credibility_status = result.credibility_status
        art.fact_check_status = result.fact_check_status
        db.commit()

    return result


@router.get("/story/{story_id}", response_model=StoryVerificationSummary)
async def get_story_verification(story_id: str, db: Session = Depends(get_db)):
    """Retrieve aggregated verification summary, domain ratings, fact-checks, and cross-source discrepancies for a story cluster."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail=f"Story with ID '{story_id}' not found.")

    articles = db.query(Article).filter(Article.story_id == story_id).all()
    articles_dict = [
        {
            "id": a.id,
            "title": a.title,
            "url": a.url,
            "canonical_url": a.canonical_url,
            "source_name": a.source_name,
            "published_at": a.published_at
        }
        for a in articles
    ]

    summary = await credibility_service.verify_story_cluster(story_id, articles_dict)
    
    # Update story DB model
    if story.discrepancy_status != summary.discrepancy_status:
        story.discrepancy_status = summary.discrepancy_status
        db.commit()

    return summary


@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_verification(
    story_id: Optional[str] = Query(None, description="Optional story ID to refresh verification for"),
    db: Session = Depends(get_db)
):
    """Trigger/refresh verification logic for a specific story or all active stories."""
    if story_id:
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise HTTPException(status_code=404, detail=f"Story with ID '{story_id}' not found.")

        articles = db.query(Article).filter(Article.story_id == story_id).all()
        articles_dict = [
            {
                "id": a.id,
                "title": a.title,
                "url": a.url,
                "canonical_url": a.canonical_url,
                "source_name": a.source_name,
                "published_at": a.published_at
            }
            for a in articles
        ]
        summary = await credibility_service.verify_story_cluster(story_id, articles_dict)
        story.discrepancy_status = summary.discrepancy_status
        db.commit()

        return {
            "status": "success",
            "message": f"Refreshed verification for story '{story_id}'.",
            "story_id": story_id,
            "summary": summary.model_dump()
        }

    # Refresh top 10 stories if story_id not specified
    stories = db.query(Story).order_by(Story.last_updated.desc()).limit(10).all()
    refreshed_count = 0

    for st in stories:
        arts = db.query(Article).filter(Article.story_id == st.id).all()
        arts_dict = [
            {
                "id": a.id,
                "title": a.title,
                "url": a.url,
                "canonical_url": a.canonical_url,
                "source_name": a.source_name,
                "published_at": a.published_at
            }
            for a in arts
        ]
        sum_res = await credibility_service.verify_story_cluster(st.id, arts_dict)
        st.discrepancy_status = sum_res.discrepancy_status
        refreshed_count += 1

    db.commit()

    return {
        "status": "success",
        "message": f"Refreshed verification across {refreshed_count} active story clusters.",
        "refreshed_stories_count": refreshed_count
    }
