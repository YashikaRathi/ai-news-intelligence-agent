import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.db.session import engine
from app.db.base import Base
import app.models  # Ensures models are registered with Base

from app.schemas.health import HealthResponse
from app.api import news_router, stories_router, search_router, ai_router

load_dotenv()

# Create SQLite tables on app startup for MVP
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI News Intelligence Agent API",
    description="Academic Honors Project MVP backend service for news discovery, clustering, AI summarization, and RAG search.",
    version="0.1.0"
)

# CORS Configuration - Dynamically include all localhost and 127.0.0.1 development ports
origins_str = os.getenv("CORS_ORIGINS", "")
parsed_origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]

default_dev_origins = [
    "http://localhost:5173", "http://127.0.0.1:5173",
    "http://localhost:5174", "http://127.0.0.1:5174",
    "http://localhost:5175", "http://127.0.0.1:5175",
    "http://localhost:3000", "http://127.0.0.1:3000"
]

all_allowed_origins = list(set(parsed_origins + default_dev_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=all_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root & Health Check Endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    return HealthResponse(
        status="ok",
        service="ai-news-intelligence-agent",
        version="0.1.0",
        database="sqlite"
    )

# Register API Routers
app.include_router(news_router, prefix="/api")
app.include_router(stories_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(ai_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, reload=True)
