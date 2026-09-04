from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.ai import (
    StoryIntelligenceResponse,
    ChatRequest,
    ChatResponse,
    SummarizeRequest,
)
from app.services.intelligence import IntelligenceService
from app.services.rag import RAGService
from app.models.story import Story

router = APIRouter(prefix="/ai", tags=["AI Analysis & RAG"])

intelligence_service = IntelligenceService()
rag_service = RAGService()

@router.get("/stories/{story_id}/intelligence", response_model=StoryIntelligenceResponse)
async def get_story_intelligence(story_id: str, db: Session = Depends(get_db)):
    """Retrieve structured AI intelligence for a specific story cluster (What Happened, What Changed, Why It Matters, Evidence, Source Comparison)."""
    try:
        response = await intelligence_service.analyze_story(story_id, db)
        return response
    except ValueError as val_err:
        raise HTTPException(status_code=404, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate story intelligence: {exc}")


@router.post("/chat", response_model=ChatResponse)
async def chat_rag(request: ChatRequest, db: Session = Depends(get_db)):
    """Ground RAG 'Ask the News' Q&A endpoint. Retrieves article evidence before generating answer."""
    question = request.get_question()
    if not question:
        raise HTTPException(status_code=400, detail="Parameter 'question' or 'query' is required.")

    try:
        response = await rag_service.ask_news(
            question=question,
            story_id=request.story_id,
            db=db
        )
        return response
    except Exception as exc:
        return ChatResponse(
            answer="I couldn't find enough evidence in the available coverage to answer that reliably.",
            sources=[],
            is_demo=True
        )


@router.post("/summarize", response_model=StoryIntelligenceResponse)
async def summarize_story(request: SummarizeRequest, db: Session = Depends(get_db)):
    """Summarize story or arbitrary articles into structured intelligence."""
    story_id = request.story_id
    if not story_id:
        # Pick latest story as fallback if none specified
        latest_story = db.query(Story).order_by(Story.last_updated.desc()).first()
        if not latest_story:
            raise HTTPException(status_code=404, detail="No stories found in database to summarize.")
        story_id = latest_story.id

    try:
        response = await intelligence_service.analyze_story(story_id, db)
        return response
    except ValueError as val_err:
        raise HTTPException(status_code=404, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to summarize story: {exc}")
