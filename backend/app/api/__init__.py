from app.api.news import router as news_router
from app.api.stories import router as stories_router
from app.api.search import router as search_router
from app.api.ai import router as ai_router

__all__ = ["news_router", "stories_router", "search_router", "ai_router"]
