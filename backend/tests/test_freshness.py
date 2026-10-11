import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from app.main import app
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models.article import Article
from app.models.story import Story
from app.services.search import SearchService, get_freshness_cutoff
from app.services.ingestion import IngestionService
from app.providers.news import RSSNewsProvider, GNewsProvider, get_news_provider

client = TestClient(app)

def make_article(**kwargs) -> Article:
    """Helper to instantiate Article with normalized_title and canonical_url populated."""
    title = kwargs.get("title", "Sample Article")
    if "normalized_title" not in kwargs:
        kwargs["normalized_title"] = title.lower()
    url = kwargs.get("url", f"https://news.example.com/{kwargs.get('id', 'art')}")
    kwargs["url"] = url
    if "canonical_url" not in kwargs:
        kwargs["canonical_url"] = url
    if "source_name" not in kwargs:
        kwargs["source_name"] = "SampleSource"
    return Article(**kwargs)

@pytest.fixture(autouse=True)
def setup_freshness_db():
    """Setup a clean SQLite database before each test and mock external network ingestion."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    mock_provider = MagicMock()
    mock_provider.fetch_articles = AsyncMock(return_value=[])
    with patch("app.api.search.get_news_provider", return_value=mock_provider), \
         patch("app.api.news.get_news_provider", return_value=mock_provider):
        yield

    # Ensure tables exist for subsequent test suites
    Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# 1. Freshness Cutoff Calculation Tests
# ---------------------------------------------------------------------------

def test_freshness_cutoff_intervals():
    """Test that get_freshness_cutoff returns expected UTC timestamps."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # 1 hour
    cutoff_1h = get_freshness_cutoff("1h")
    assert cutoff_1h is not None
    assert abs((now - timedelta(hours=1) - cutoff_1h).total_seconds()) < 5

    # 6 hours
    cutoff_6h = get_freshness_cutoff("6h")
    assert cutoff_6h is not None
    assert abs((now - timedelta(hours=6) - cutoff_6h).total_seconds()) < 5

    # 24 hours
    cutoff_24h = get_freshness_cutoff("24h")
    assert cutoff_24h is not None
    assert abs((now - timedelta(hours=24) - cutoff_24h).total_seconds()) < 5

    # 7 days
    cutoff_7d = get_freshness_cutoff("7d")
    assert cutoff_7d is not None
    assert abs((now - timedelta(days=7) - cutoff_7d).total_seconds()) < 5

    # All or None
    assert get_freshness_cutoff("all") is None
    assert get_freshness_cutoff(None) is None
    assert get_freshness_cutoff("invalid") is None


# ---------------------------------------------------------------------------
# 2. Old Articles Excluded vs Newly Published Articles Included
# ---------------------------------------------------------------------------

def test_freshness_filter_excludes_old_articles_and_includes_recent():
    """Articles published days ago are excluded when 1h or 24h filter is applied."""
    db = SessionLocal()
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Brand new article (15 minutes ago)
    recent_art = make_article(
        id="art_recent_15m",
        title="Breaking: Tech Giants Announce Realtime Agent Architecture",
        url="https://news.example.com/breaking-agent",
        source_name="TechDaily",
        published_at=now - timedelta(minutes=15),
        topic="technology",
    )

    # 3 hours ago article
    med_art = make_article(
        id="art_med_3h",
        title="Midday Review: Autonomous Systems in Manufacturing",
        url="https://news.example.com/midday-review",
        source_name="IndustrialNews",
        published_at=now - timedelta(hours=3),
        topic="technology",
    )

    # 4 days ago old article
    old_art = make_article(
        id="art_old_4d",
        title="Historic Retrospective on Early Language Modeling",
        url="https://news.example.com/old-paper",
        source_name="ArchiveNews",
        published_at=now - timedelta(days=4),
        topic="technology",
    )

    db.add_all([recent_art, med_art, old_art])
    db.commit()
    db.close()

    # Query 1h freshness -> only recent_art
    res_1h = client.get("/api/news?freshness=1h")
    assert res_1h.status_code == 200
    items_1h = res_1h.json()
    assert len(items_1h) == 1
    assert items_1h[0]["id"] == "art_recent_15m"

    # Query 6h freshness -> recent_art and med_art
    res_6h = client.get("/api/news?freshness=6h")
    assert res_6h.status_code == 200
    items_6h = res_6h.json()
    assert len(items_6h) == 2
    ids_6h = [item["id"] for item in items_6h]
    assert "art_recent_15m" in ids_6h
    assert "art_med_3h" in ids_6h
    assert "art_old_4d" not in ids_6h

    # Query all freshness -> all 3
    res_all = client.get("/api/news?freshness=all")
    assert res_all.status_code == 200
    assert len(res_all.json()) == 3


# ---------------------------------------------------------------------------
# 3. Recently Updated but Old Article Must NOT be Treated as Fresh
# ---------------------------------------------------------------------------

def test_recently_updated_old_article_not_treated_as_fresh():
    """An old article that was updated 5 minutes ago must NOT pass 1h freshness filter."""
    db = SessionLocal()
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Published 5 days ago, but updated 5 minutes ago (editorial typo fix)
    edited_art = make_article(
        id="art_edited_old",
        title="Older Report With Recent Minor Typo Fix",
        url="https://news.example.com/edited-old-article",
        source_name="PressWire",
        published_at=now - timedelta(days=5),
        source_updated_at=now - timedelta(minutes=5),
        ingested_at=now - timedelta(minutes=2),
        topic="general",
    )

    # Genuinely fresh article published 20 minutes ago
    fresh_art = make_article(
        id="art_truly_fresh",
        title="Live Developments Happening Right Now",
        url="https://news.example.com/fresh-live",
        source_name="PressWire",
        published_at=now - timedelta(minutes=20),
        topic="general",
    )

    db.add_all([edited_art, fresh_art])
    db.commit()
    db.close()

    # When querying 1h freshness
    res = client.get("/api/news?freshness=1h")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]["id"] == "art_truly_fresh"
    # Old edited article must be excluded!
    assert all(i["id"] != "art_edited_old" for i in items)


# ---------------------------------------------------------------------------
# 4. Timezone Offset Normalization and Freshness
# ---------------------------------------------------------------------------

def test_timezone_offsets_normalization():
    """Timezones with various offsets (IST +05:30, EDT -04:00) normalize to UTC correctly."""
    now_utc = datetime.now(timezone.utc)
    t_minus_30m = now_utc - timedelta(minutes=30)

    # Format in IST (+05:30)
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    t_ist = t_minus_30m.astimezone(ist_tz).strftime("%Y-%m-%dT%H:%M:%S+05:30")
    parsed_ist = IngestionService.parse_timestamp(t_ist)
    assert parsed_ist is not None
    assert parsed_ist.tzinfo == timezone.utc

    # Format in EDT (-04:00)
    edt_tz = timezone(timedelta(hours=-4))
    t_edt = t_minus_30m.astimezone(edt_tz).strftime("%Y-%m-%dT%H:%M:%S-04:00")
    parsed_edt = IngestionService.parse_timestamp(t_edt)
    assert parsed_edt is not None
    assert parsed_edt.tzinfo == timezone.utc

    # Both converted to naive UTC should match approximately
    diff_sec = abs((parsed_ist.replace(tzinfo=None) - parsed_edt.replace(tzinfo=None)).total_seconds())
    assert diff_sec < 2


# ---------------------------------------------------------------------------
# 5. Missing Publication Timestamp Handling
# ---------------------------------------------------------------------------

def test_missing_timestamp_not_treated_as_fresh():
    """Missing or null publication dates must not be pretended as fresh news."""
    db = SessionLocal()
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    art_no_date = make_article(
        id="art_missing_date",
        title="Article With Completely Missing Publish Date",
        url="https://news.example.com/no-date",
        source_name="UnknownSource",
        published_at=None,
        topic="general",
    )

    art_fresh = make_article(
        id="art_has_date",
        title="Article With Verified Publish Date",
        url="https://news.example.com/valid-date",
        source_name="KnownSource",
        published_at=now - timedelta(minutes=10),
        topic="general",
    )

    db.add_all([art_no_date, art_fresh])
    db.commit()
    db.close()

    # 1h freshness filter
    res = client.get("/api/news?freshness=1h")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]["id"] == "art_has_date"

    # All news returns both without error
    res_all = client.get("/api/news?freshness=all")
    assert res_all.status_code == 200
    assert len(res_all.json()) == 2


# ---------------------------------------------------------------------------
# 6. Cross-Provider Deduplication Preserving Source and Publication Time
# ---------------------------------------------------------------------------

def test_deduplication_preserves_original_source_and_published_at():
    """Deduplication marks duplicate articles while preserving original source URL and timestamp."""
    db = SessionLocal()
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    original_pub = now - timedelta(hours=2)

    original_art = make_article(
        id="art_orig_reuters",
        title="Global Semiconductor Coalition Announces Next-Gen Standards",
        url="https://reuters.com/business/chips/coalition-standards",
        source_name="Reuters",
        published_at=original_pub,
        is_duplicate=False,
    )
    db.add(original_art)
    db.commit()

    # Syndicated reprint from Yahoo News
    syndicated_art = make_article(
        id="art_syndicated_yahoo",
        title="Global Semiconductor Coalition Announces Next-Gen Standards",
        url="https://yahoo.com/news/chips/coalition-standards",
        source_name="Yahoo Finance",
        published_at=original_pub + timedelta(minutes=15),
        is_duplicate=True,
        duplicate_of_id="art_orig_reuters",
    )
    db.add(syndicated_art)
    db.commit()
    db.close()

    # Query GET /api/news should hide is_duplicate=True by default
    res = client.get("/api/news?freshness=6h")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]["id"] == "art_orig_reuters"
    assert items[0]["url"] == "https://reuters.com/business/chips/coalition-standards"


# ---------------------------------------------------------------------------
# 7. Empty Results When Freshness Window Has No Articles
# ---------------------------------------------------------------------------

def test_empty_results_when_freshness_window_empty():
    """If no articles exist within the selected window, return empty list rather than silently falling back to old news."""
    db = SessionLocal()
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Only old articles from 2 days ago exist
    old_art = make_article(
        id="art_two_days_old",
        title="Two Day Old Scientific Announcement",
        url="https://news.example.com/two-days",
        source_name="ScienceReport",
        published_at=now - timedelta(days=2),
    )
    db.add(old_art)
    db.commit()
    db.close()

    # 1h filter must return empty list []
    res_1h = client.get("/api/news?freshness=1h")
    assert res_1h.status_code == 200
    assert res_1h.json() == []

    # 6h filter must return empty list []
    res_6h = client.get("/api/news?freshness=6h")
    assert res_6h.status_code == 200
    assert res_6h.json() == []

    # Search with 1h filter must also return 0 articles and 0 stories
    res_search = client.get("/api/search?q=Scientific&freshness=1h")
    assert res_search.status_code == 200
    data = res_search.json()
    assert data["article_count"] == 0
    assert len(data["articles"]) == 0


# ---------------------------------------------------------------------------
# 8. Story Sorting and Freshness
# ---------------------------------------------------------------------------

def test_story_freshness_and_sorting():
    """Stories are sorted newest-first by latest_published_at and filtered by freshness."""
    db = SessionLocal()
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    s_fresh = Story(
        id="story_fresh",
        title="Fresh Story Breaking 30 Minutes Ago",
        summary="A recent story cluster.",
        topic="Technology",
        first_seen=now - timedelta(minutes=45),
        last_updated=now - timedelta(minutes=30),
        latest_published_at=now - timedelta(minutes=30),
        article_count=2,
    )

    s_old = Story(
        id="story_old",
        title="Older Story Cluster from 3 Days Ago",
        summary="An older story cluster.",
        topic="Technology",
        first_seen=now - timedelta(days=4),
        last_updated=now - timedelta(minutes=5),  # Recently re-clustered/touched!
        latest_published_at=now - timedelta(days=3),  # Original publication 3 days ago
        article_count=5,
    )

    db.add_all([s_fresh, s_old])
    db.commit()
    db.close()

    # Under 1h freshness, only story_fresh should return, despite story_old having last_updated 5m ago!
    res_1h = client.get("/api/stories?freshness=1h")
    assert res_1h.status_code == 200
    stories_1h = res_1h.json()
    assert len(stories_1h) == 1
    assert stories_1h[0]["id"] == "story_fresh"

    # Under all freshness, story_fresh must appear before story_old because latest_published_at is newer
    res_all = client.get("/api/stories?freshness=all&sort_by=latest")
    assert res_all.status_code == 200
    stories_all = res_all.json()
    assert len(stories_all) == 2
    assert stories_all[0]["id"] == "story_fresh"
    assert stories_all[1]["id"] == "story_old"


# ---------------------------------------------------------------------------
# 9. Provider Architecture: Realtime RSS and GNews Evaluation
# ---------------------------------------------------------------------------

def test_google_news_rss_provider_configuration():
    """Verify RSS provider includes Google News breaking feed for true real-time headlines."""
    provider = RSSNewsProvider()
    assert any(f.get("name") == "Google News" for f in provider.default_feeds)
    assert any("news.google.com/rss" in f.get("url", "") for f in provider.default_feeds)

def test_gnews_provider_initialization():
    """Verify GNews provider initializes and handles missing API key gracefully with RSS fallback."""
    gnews = GNewsProvider(api_key=None)
    assert gnews.api_key is None
    # Factory resolution
    prov = get_news_provider("gnews")
    assert isinstance(prov, GNewsProvider)
