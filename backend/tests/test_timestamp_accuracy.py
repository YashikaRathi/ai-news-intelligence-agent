import pytest
from datetime import datetime, timezone, timedelta
from app.services.ingestion import IngestionService
from app.providers.news import RSSNewsProvider
from app.services.clustering import ClusteringService

def test_valid_utc_publication_timestamp():
    """Test parsing a valid UTC ISO timestamp with 'Z' suffix."""
    iso_val = "2026-10-11T14:30:00Z"
    parsed = IngestionService.parse_timestamp(iso_val)
    assert parsed is not None
    assert parsed.tzinfo == timezone.utc
    assert parsed.year == 2026
    assert parsed.month == 10
    assert parsed.day == 11
    assert parsed.hour == 14
    assert parsed.minute == 30

def test_iso_timestamp_with_explicit_offset():
    """Test parsing ISO timestamp with explicit timezone offset (+05:30 IST)."""
    # 20:00:00 +05:30 is 14:30:00 UTC
    iso_val = "2026-10-11T20:00:00+05:30"
    parsed = IngestionService.parse_timestamp(iso_val)
    assert parsed is not None
    assert parsed.tzinfo == timezone.utc
    assert parsed.hour == 14
    assert parsed.minute == 30

def test_iso_timestamp_with_negative_offset():
    """Test parsing ISO timestamp with negative offset (-04:00 EDT)."""
    # 10:00:00 -04:00 is 14:00:00 UTC
    iso_val = "2026-10-11T10:00:00-04:00"
    parsed = IngestionService.parse_timestamp(iso_val)
    assert parsed is not None
    assert parsed.tzinfo == timezone.utc
    assert parsed.hour == 14
    assert parsed.minute == 0

def test_rss_rfc822_timestamp_with_timezone():
    """Test parsing RFC 822 / 2822 RSS date formats (email format)."""
    rfc_date = "Sun, 11 Oct 2026 14:30:00 +0000"
    parsed = IngestionService.parse_timestamp(rfc_date)
    assert parsed is not None
    assert parsed.tzinfo == timezone.utc
    assert parsed.hour == 14
    assert parsed.minute == 30

def test_missing_publication_date_remains_none():
    """High-priority requirement: Missing publication date must remain None and NEVER be replaced with current time."""
    assert IngestionService.parse_timestamp(None) is None
    assert IngestionService.parse_timestamp("") is None
    assert IngestionService.parse_timestamp("   ") is None

    provider = RSSNewsProvider()
    entry_without_date = {"title": "Test Title", "link": "https://example.com/art"}
    pub_date = provider._parse_published_date(entry_without_date)
    assert pub_date is None

def test_malformed_date_returns_none():
    """Malformed dates should return None gracefully without raising exceptions."""
    assert IngestionService.parse_timestamp("not-a-valid-date-string-1234") is None
    assert IngestionService.parse_timestamp("2026-99-99T99:99:99") is None

def test_midnight_utc_crosses_calendar_day_in_ist():
    """A timestamp around midnight UTC (e.g. 20:00 UTC) falls on the next calendar day in IST (UTC+05:30)."""
    # 2026-10-11 20:00:00 UTC -> in IST is 2026-10-12 01:30:00
    utc_str = "2026-10-11T20:00:00Z"
    parsed = IngestionService.parse_timestamp(utc_str)
    assert parsed is not None
    assert parsed.day == 11
    assert parsed.hour == 20

    # Convert to IST (UTC+5:30)
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    ist_dt = parsed.astimezone(ist_tz)
    assert ist_dt.day == 12  # Next calendar day!
    assert ist_dt.hour == 1
    assert ist_dt.minute == 30

def test_older_article_timestamp():
    """Older article timestamps (e.g. 2024) must be preserved accurately."""
    old_iso = "2024-01-15T08:00:00Z"
    parsed = IngestionService.parse_timestamp(old_iso)
    assert parsed is not None
    assert parsed.year == 2024
    assert parsed.month == 1
    assert parsed.day == 15

def test_future_timestamp_preserves_original():
    """Articles with slightly future timestamps (clock skew) must not be corrupted."""
    future_time = "2026-10-12T12:00:00Z"
    parsed = IngestionService.parse_timestamp(future_time)
    assert parsed is not None
    assert parsed.day == 12

def test_source_updated_at_distinct_from_published_at():
    """Verify published_at and source_updated_at are tracked separately."""
    provider = RSSNewsProvider()
    entry = {
        "published": "Sun, 11 Oct 2026 10:00:00 +0000",
        "updated": "Sun, 11 Oct 2026 12:30:00 +0000"
    }
    pub = provider._parse_published_date(entry)
    upd = provider._parse_updated_date(entry)

    assert pub is not None
    assert upd is not None
    assert pub != upd
    assert "10:00:00" in pub
    assert "12:30:00" in upd

def test_clustering_to_naive_datetime_preserves_utc():
    """Test clustering service _to_naive_datetime converts timezone offset to UTC before stripping tzinfo."""
    # 20:00:00 +05:30 = 14:30:00 UTC
    dt_with_offset = "2026-10-11T20:00:00+05:30"
    naive = ClusteringService._to_naive_datetime(dt_with_offset)
    assert naive is not None
    assert naive.tzinfo is None
    assert naive.hour == 14
    assert naive.minute == 30

def test_clustering_to_naive_datetime_handles_none():
    """Test clustering service _to_naive_datetime returns None for None."""
    assert ClusteringService._to_naive_datetime(None) is None
