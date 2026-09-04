# AI News Intelligence Agent

An academic Honors Project MVP that transforms multi-source news articles into structured story clusters, intelligence summaries, source comparisons, timeline trajectories, and grounded RAG Q&A ("Ask the News").

## Architecture Overview

```
News Sources (NewsAPI.org Primary / RSS Feed Fallback)
   │
   ▼
Article Ingestion (`NewsAPIProvider` / `RSSNewsProvider`)
   │
   ▼
Cleaning & Normalization (`IngestionService`)
   │
   ▼
Duplicate Detection (`DeduplicationService`)
   │
   ▼
Story Event Clustering (`ClusteringService`)
   │
   ▼
SQLite DB Persistence (`articles` & `stories` tables)
   │
   ▼
AI Analysis (`IntelligenceService` & `BaseLLMProvider`)
(What Happened + What Changed + Why It Matters + Source Comparison + Evidence Citations)
   │
   ▼
RAG Search ("Ask the News") (`RAGService` & `POST /api/ai/chat`)
```

---

## News Ingestion & Provider Selection Architecture

The news ingestion system uses a modular provider abstraction supporting live API discovery and resilient fallback logic:

1. **NewsAPI Primary Provider (`NewsAPIProvider`)**:
   - Fetches live articles via `/v2/everything` (topic search, latest recency `publishedAt`, or `popularity`) and `/v2/top-headlines`.
   - Extracts metadata including original URLs, source names, authors, published dates, and high-resolution article images (`urlToImage`).
   - Filters out removed articles.

2. **Automatic RSS Fallback Provider (`RSSNewsProvider`)**:
   - Multi-feed fallback mechanism (BBC, Guardian, TechCrunch, NPR, Google News RSS) activated automatically if NewsAPI is offline, rate-limited (HTTP 429), or if `NEWS_API_KEY` is missing/invalid.

3. **Three Execution Modes**:
   - **Mode 1 (`DEMO_MODE=true`)**: Returns deterministic demo datasets for offline testing.
   - **Mode 2 (`DEMO_MODE=false` + `NEWS_PROVIDER=newsapi` + valid `NEWS_API_KEY`)**: NewsAPI primary with automatic RSS fallback.
   - **Mode 3 (`DEMO_MODE=false` + missing/invalid key or `NEWS_PROVIDER=rss`)**: RSS fallback mode.

---

## AI Intelligence & RAG Architecture

The AI layer transforms clustered news articles into structured, evidence-grounded intelligence.

### 1. Evidence Retrieval First
- **Retreat First, Generate Second**: Before calling the LLM, the backend queries SQLite for articles belonging to the target `story_id` or matching keyword query.
- **Evidence Attribution**: Every generated factual synthesis references original source articles (`article_id`, `source_name`, `title`, `url`).

### 2. Structured Story Intelligence
- **What Happened**: Factual synthesis of the central event strictly grounded in retrieved evidence.
- **What Changed**: Compares earlier coverage vs latest coverage timestamps to isolate the newest development. Returns *"Insufficient historical coverage to determine a meaningful change."* if history is sparse.
- **Why It Matters**: Cautious explanation of relevance to users, markets, policy, or technology.
- **Source Comparison**: Contrasts reporting across media outlets (`emphasis`, `differences`, `agreement`).

### 3. Modular LLM Provider & DEMO_MODE Fallback
- Configured via environment variables (`LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`).
- When `DEMO_MODE=true` or when no valid LLM API key is set, the system uses `DemoLLMProvider` for deterministic, offline evidence-grounded responses tagged with `is_demo: true`.

---

## Tech Stack
- **Frontend**: React, Vite, TypeScript, Tailwind CSS, Lucide React
- **Backend**: Python 3.10+, FastAPI, Pydantic V2, SQLAlchemy, HTTPX
- **Database**: SQLite (MVP)
- **AI / LLM**: Modular Provider Abstraction (`BaseLLMProvider`, `OpenAILLMProvider`, `DemoLLMProvider`)
- **News Ingestion**: Modular News Provider (`NewsAPIProvider`, `RSSNewsProvider`, `get_news_provider`)

---

## Getting Started

### Prerequisites
- Python 3.10 or higher
- Node.js 18+ and `npm`

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux/macOS:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend dev server
uvicorn app.main:app --reload --port 8000
```
Backend running at: `http://localhost:8000`
API Health check: `http://localhost:8000/health`
Interactive API Docs: `http://localhost:8000/docs`

### 2. Frontend Setup

```bash
# Open a new terminal and navigate to frontend directory
cd frontend

# Install packages
npm install

# Start Vite development server
npm run dev
```
Frontend running at: `http://localhost:5173`

---

## Environment Variables

Copy `.env.example` to `.env` in the project root:

```bash
cp .env.example .env
```

Key environment settings:
- `NEWS_PROVIDER`: `newsapi` / `rss` (Default: `newsapi`)
- `NEWS_API_KEY`: API key from NewsAPI.org (Kept strictly on backend; never exposed to frontend)
- `DEMO_MODE`: `true` / `false`
- `DATABASE_URL`: SQLite database file path (e.g. `sqlite:///./news_intelligence.db`)
- `CORS_ORIGINS`: Allowed origins for API requests
- `LLM_PROVIDER`: `openai` / `anthropic` / `custom`
- `LLM_API_KEY`: API key for LLM Provider (never commit real secrets)
- `LLM_MODEL`: Target model identifier

---

## Testing

```bash
cd backend
.\venv\Scripts\pytest
```

Frontend production build check:
```bash
cd frontend
npm run build
```

