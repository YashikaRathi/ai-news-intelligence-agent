from app.api.news import router as news_router
from app.api.stories import router as stories_router
from app.api.search import router as search_router
from app.api.ai import router as ai_router
from app.api.verification import router as verification_router
from app.api.reviews import router as reviews_router
from app.api.notifications import router as notifications_router

__all__ = [
    "news_router",
    "stories_router",
    "search_router",
    "ai_router",
    "verification_router",
    "reviews_router",
    "notifications_router"
]

