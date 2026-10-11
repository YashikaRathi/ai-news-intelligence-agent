# AI News Intelligence Agent

An academic Honors Project MVP that transforms multi-source news articles into structured story clusters, real-time intelligence summaries, source comparisons, timeline trajectories, credibility verifications, and grounded RAG Q&A ("Ask the News").

---

## Architecture Overview

```
News Sources (Google News RSS / GNews API / NewsAPI.org)
   │
   ▼
Article Ingestion (`RSSNewsProvider` / `GNewsProvider` / `NewsAPIProvider`)
   │
   ▼
Cleaning & UTC Normalization (`IngestionService`)
   │
   ▼
Duplicate Detection & Syndication Tracking (`DeduplicationService`)
   │
   ▼
Story Event Clustering (`ClusteringService`)
   │
   ▼
Credibility & Fact-Check Verification (`CredibilityVerificationService`)
   │
   ▼
SQLite DB Persistence (`articles`, `stories`, `reviews`, `notifications`)
   │
   ▼
Search & Relevance Engine (`SearchService` with Freshness Windows & Explicit Sorting)
   │
   ▼
AI Analysis (`IntelligenceService` & `BaseLLMProvider`)
(What Happened + What Changed + Why It Matters + Source Comparison + Verification Findings)
   │
   ▼
RAG Search ("Ask the News") (`RAGService` & `POST /api/ai/chat`)
```

---

## Key Features & Capabilities

### 1. News Freshness Engine & Real-Time Feeds
Surfaces genuinely breaking news published minutes or hours ago, eliminating the stale-article problem caused by update/re-ingestion timestamps:
* **Original Publication Timestamp Priority**: Feeds and ranking use original publication dates (`published_at` for articles, `latest_published_at` for story clusters), rather than DB ingestion or editorial typo update times (`last_updated`, `ingested_at`).
* **Multi-Window Freshness Filtering**: Both the dashboard and search interfaces support instant freshness filtering:
  * **Last hour (`1h`)**
  * **Last 6 hours (`6h`)**
  * **Last 24 hours (`24h`)**
  * **Last 7 days (`7d`)**
  * **All available news (`all`)**
* **Publication-First Sorting**: Live feeds sort newest first by publication time. Search allows toggling between **Relevance** (query match + recency balance) and **Newest First** (strict publication time).
* **Clear Zero-Result Empty States**: If no articles exist in the chosen freshness window (e.g., *Last hour*), the UI explicitly informs the reader rather than silently falling back to stale news.
* **Real-Time Breaking RSS**: Integrated Google News Breaking News RSS (`news.google.com/rss`) into default feeds for unembargoed, zero-cost, real-time news updates with RFC 822 timestamps.

### 2. Search Engine Relevance & Multi-Criteria Ranking
An intelligent search and ranking engine ([SearchService](file:///backend/app/services/search.py)) tailored for news discovery:
* **Query Intent & Tokenization**: Extracts quoted phrases (e.g., `"James Webb"`), isolates content-bearing terms with stop-word filtering, and preserves short acronyms (AI, EV, TSMC, NASA, BBC) and version identifiers (GPT-5, 1.4nm).
* **Multi-Field Scoring**: Ranks candidate articles and story clusters using weighted matching across title, description, content, author, source, and topic.
* **Exact Title & Acronym Immunity**: Guarantees that exact title matches rank #1, while preventing false-positive substring hits on words containing acronyms (e.g., "claim" matching "AI").
* **Syndication Penalty**: Suppresses identical reprints so diverse sources surface first.

### 3. Credibility & Fact-Check Verification Layer
Integrated verification layer ([CredibilityVerificationService](file:///backend/app/services/credibility.py)) to help readers evaluate news trustworthiness:
* **Publisher Domain Credibility Registry**: Evaluates domain reputation against a curated registry with explicit status flags (`rated` vs `not_assessed`) and credibility tiers (`high_credibility`, `medium_credibility`, `caution_advised`). Unknown domains remain unverified rather than falsely flagged.
* **External Fact-Check Integration (Google Fact Check Tools API / ClaimReview)**: Queries third-party fact-checkers and displays normalized, human-readable ratings:
  * `Fact-check rated TRUE`
  * `Fact-check rated FALSE`
  * `Mixed or partially true`
  * `Conflicting reports`
  * `Insufficient evidence`
  * `No matching fact-check found`
  * `Not checked`
* **Cross-Source Claim Discrepancy Engine**: Analyzes consensus across clustered outlets to classify reporting status (`unanimous_consensus`, `conflicting_reports`, `single_source_only`, `insufficient_evidence`).
* **Methodological Disclosures**: Discloses that publisher reputation does not equal claim proof, and lack of a fact-check does not imply falsehood.

### 4. Reader Reviews & Community Feedback
Allows community perspectives while preserving journalistic integrity:
* **1 to 5 Star Rating**: Readers evaluate coverage clarity and depth.
* **Anti-Inflation Upsert Mechanics**: Enforces database-level uniqueness per anonymous reader (`UniqueConstraint("target_type", "target_id", "reader_id")`). Readers can update their review, but cannot artificially inflate scores.
* **Statistical Aggregation**: Computes average ratings, total reviews, and 1–5 star distributions.
* **Clarity vs Truthfulness Distinction**: Displays an explicit disclaimer that reader reviews reflect subjective presentation clarity, not factual truthfulness.

### 5. In-App Notifications
Non-intrusive alert system keeping readers updated on developing events:
* **Notification Types**:
  * `verification_change`: Alerts when fact-check or credibility status is updated.
  * `contradiction_alert`: Alerts when conflicting cross-source claims emerge.
  * `topic_alert`: Alerts when fresh articles are ingested for followed topics.
  * `story_update`: Alerts when new coverage is clustered into an existing story.
* **SHA-256 Deduplication**: Hashing (`recipient + event_type + story_id + date`) prevents repetitive notifications.
* **Reader Preferences**: Configurable category preferences and mute toggles via `GET/PUT /api/notifications/preferences`.

### 6. Timestamp Audit & Timezone Accuracy
* **Strict UTC Normalization**: Ingestion parses ISO 8601, explicit offsets (`+05:30`, `-04:00`), and RFC 822 dates into naive UTC datetimes internally.
* **Field Separation**: Distinct tracking for `published_at`, `source_updated_at`, `ingested_at`, and `verified_at`.
* **Local Timezone Display**: Frontend presents relative times (*"15 minutes ago"*, *"3 hours ago"*, *"Yesterday"*) with hover tooltips displaying exact India Standard Time (IST, UTC+05:30) and raw UTC ISO strings.

---

## News Ingestion Providers & Capabilities

| Provider | Freshness & Delay | API Key Required | Rate Limits | Architecture Status |
| :--- | :--- | :--- | :--- | :--- |
| **Google News RSS** | **Real-time (minutes old)** | **No** (Free & public) | No strict limit under standard polling | **Default Real-Time RSS Provider** |
| **GNews API (`gnews.io`)** | **Real-time (minutes old)** | **Yes** (`GNEWS_API_KEY`) | 100 requests/day (Free tier) | **Supported** with automatic RSS fallback |
| **NewsAPI.org** | **24-Hour Delay on Free Tier** (Real-time requires $449/mo plan) | **Yes** (`NEWS_API_KEY`) | 100 requests/day | **Supported** with automatic RSS fallback |
| **Demo Data Provider** | Deterministic snapshots | **No** | None | Active when `DEMO_MODE=true` |

---

## AI Intelligence & RAG Architecture

The AI layer transforms clustered news articles into structured, evidence-grounded intelligence.

### 1. Evidence Retrieval First
* **Retrieve First, Generate Second**: Before invoking the LLM, the backend queries SQLite for articles belonging to the target `story_id` or matching keyword query.
* **Evidence Attribution**: Every generated factual synthesis references original source articles (`article_id`, `source_name`, `title`, `url`).

### 2. Structured Story Intelligence
* **What Happened**: Factual synthesis of the central event strictly grounded in retrieved evidence.
* **What Changed**: Compares earlier coverage vs latest coverage timestamps to isolate the newest development. Returns *"Insufficient historical coverage to determine a meaningful change."* if history is sparse.
* **Why It Matters**: Objective explanation of relevance to users, markets, policy, or technology.
* **Source Comparison**: Contrasts reporting across media outlets (`emphasis`, `differences`, `agreement`).

### 3. Modular LLM Provider & DEMO_MODE Fallback
* Configured via environment variables (`LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`).
* When `DEMO_MODE=true` or when no valid LLM API key is set, the system uses `DemoLLMProvider` for deterministic, offline evidence-grounded responses tagged with `is_demo: true`.

---

## Tech Stack
* **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, Lucide React, Axios
* **Backend**: Python 3.10+, FastAPI, Pydantic V2, SQLAlchemy, HTTPX, Beautiful Soup 4, Feedparser
* **Database**: SQLite
* **AI / LLM**: Modular Provider Abstraction (`BaseLLMProvider`, `OpenAILLMProvider`, `DemoLLMProvider`)
* **News Providers**: `RSSNewsProvider` (with Google News RSS), `GNewsProvider`, `NewsAPIProvider`

---

## Getting Started

### Prerequisites
* Python 3.10 or higher
* Node.js 18+ and `npm`

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

* Backend API: `http://localhost:8000`
* API Health check: `http://localhost:8000/health`
* Interactive OpenAPI Documentation: `http://localhost:8000/docs`

### 2. Frontend Setup

```bash
# Open a new terminal and navigate to frontend directory
cd frontend

# Install packages
npm install

# Start Vite development server
npm run dev
```

* Frontend application: `http://localhost:5173`

---

## Environment Variables

Copy `.env.example` to `.env` in the project root:

```bash
cp .env.example .env
```

| Variable | Description | Example / Default |
| :--- | :--- | :--- |
| `NEWS_PROVIDER` | Active news ingestion provider (`rss`, `gnews`, `newsapi`) | `rss` |
| `GNEWS_API_KEY` | Optional API key for real-time GNews API | *(Optional)* |
| `NEWS_API_KEY` | Optional API key for NewsAPI.org | *(Optional)* |
| `GOOGLE_FACT_CHECK_API_KEY` | Optional API key for Google Fact Check Tools API | *(Optional)* |
| `DEMO_MODE` | Enable offline deterministic datasets | `false` |
| `DATABASE_URL` | SQLite database URI | `sqlite:///./news_intelligence.db` |
| `CORS_ORIGINS` | Permitted origins for API requests | `http://localhost:5173,http://127.0.0.1:5173` |
| `LLM_PROVIDER` | Active LLM provider (`demo`, `openai`, `gemini`) | `demo` |
| `LLM_API_KEY` | API key for LLM Provider (never commit secrets) | *(Optional)* |
| `LLM_MODEL` | Target LLM model identifier | `gpt-4o-mini` |

> [!NOTE]
> All API keys remain configured strictly in backend environment variables. No secrets are embedded in the frontend bundle or committed to source control.

---

## Automated Testing

### Backend Test Suite
Run the full pytest suite (69 automated tests covering freshness filters, publication timestamps, search relevance, deduplication, verification, reviews, and notifications):

```bash
cd backend
.\venv\Scripts\pytest -v
```

### Frontend Typecheck & Build Validation
Validate TypeScript definitions and compile the production bundle:

```bash
cd frontend
npm run build
```
