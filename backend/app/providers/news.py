import os
import logging
import httpx
import feedparser
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import email.utils
from app.providers.demo_data import get_demo_articles

logger = logging.getLogger(__name__)

class BaseNewsProvider(ABC):
    """Abstract base class for news ingestion providers."""

    @abstractmethod
    async def fetch_articles(
        self, topic: Optional[str] = None, limit: int = 50, sort: Optional[str] = "latest"
    ) -> List[Dict[str, Any]]:
        """Fetch raw articles from news sources."""
        pass


class RSSNewsProvider(BaseNewsProvider):
    """Multi-source RSS Feed Provider with topic query support and resilient fallbacks."""

    def __init__(self, feeds: Optional[List[Dict[str, str]]] = None):
        self.default_feeds = feeds or [
            {"name": "Google News", "url": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"},
            {"name": "BBC World", "url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
            {"name": "The Guardian", "url": "https://www.theguardian.com/world/rss"},
            {"name": "TechCrunch", "url": "http://feeds.feedburner.com/TechCrunch/"},
            {"name": "NPR News", "url": "https://feeds.npr.org/1001/rss.xml"},
        ]

    def _parse_entry_date(self, entry: Dict[str, Any], date_field: str) -> Optional[str]:
        """Safely parse RSS entry date field into ISO UTC string. Returns None if missing or invalid."""
        parsed_field = f"{date_field}_parsed"
        struct_time = entry.get(parsed_field) if isinstance(entry, dict) else getattr(entry, parsed_field, None)
        if struct_time:
            try:
                dt = datetime(*struct_time[:6], tzinfo=timezone.utc)
                return dt.isoformat()
            except Exception:
                pass

        raw_str = entry.get(date_field) if isinstance(entry, dict) else getattr(entry, date_field, None)
        if raw_str and isinstance(raw_str, str) and raw_str.strip():
                try:
                    parsed_tuple = email.utils.parsedate_tz(raw_str)
                    if parsed_tuple:
                        dt = datetime.fromtimestamp(email.utils.mktime_tz(parsed_tuple), tz=timezone.utc)
                        return dt.isoformat()
                except Exception:
                    pass
                try:
                    clean_str = raw_str.strip().replace("Z", "+00:00")
                    dt = datetime.fromisoformat(clean_str)
                    if not dt.tzinfo:
                        # Documented naive RSS date policy: treat as UTC
                        dt = dt.replace(tzinfo=timezone.utc)
                    else:
                        dt = dt.astimezone(timezone.utc)
                    return dt.isoformat()
                except Exception:
                    pass

        return None

    def _parse_published_date(self, entry: Dict[str, Any]) -> Optional[str]:
        """Safely parse published date from RSS entry into ISO UTC string, or None if unavailable."""
        return self._parse_entry_date(entry, "published")

    def _parse_updated_date(self, entry: Dict[str, Any]) -> Optional[str]:
        """Safely parse updated/modified date from RSS entry into ISO UTC string, or None."""
        return self._parse_entry_date(entry, "updated") or self._parse_entry_date(entry, "modified")

    def _extract_image_url(self, entry: Dict[str, Any]) -> Optional[str]:
        """Extract media/enclosure thumbnail image from RSS entry."""
        if hasattr(entry, "media_content") and entry.media_content:
            for media in entry.media_content:
                if isinstance(media, dict) and media.get("url"):
                    return media["url"]
        if hasattr(entry, "enclosures") and entry.enclosures:
            for enc in entry.enclosures:
                if isinstance(enc, dict) and enc.get("type", "").startswith("image/") and enc.get("href"):
                    return enc["href"]
        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            for thumb in entry.media_thumbnail:
                if isinstance(thumb, dict) and thumb.get("url"):
                    return thumb["url"]
        return None

    async def fetch_articles(
        self, topic: Optional[str] = None, limit: int = 50, sort: Optional[str] = "latest"
    ) -> List[Dict[str, Any]]:
        # Check for DEMO_MODE flag
        demo_mode = os.getenv("DEMO_MODE", "false").lower() in ["true", "1", "yes"]
        if demo_mode:
            logger.info("DEMO_MODE active. Returning deterministic demo article dataset.")
            return get_demo_articles(topic or "artificial intelligence")

        target_feeds = []
        is_topic_search = bool(topic and topic.strip() and topic.strip().lower() not in ["general", "all", "news"])
        if is_topic_search:
            encoded_topic = topic.strip().replace(" ", "%20")
            google_rss = {
                "name": "Google News",
                "url": f"https://news.google.com/rss/search?q={encoded_topic}&hl=en-US&gl=US&ceid=US:en"
            }
            target_feeds.append(google_rss)
        else:
            target_feeds = list(self.default_feeds)

        articles: List[Dict[str, Any]] = []

        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            for feed_info in target_feeds:
                if len(articles) >= limit:
                    break
                feed_name = feed_info["name"]
                feed_url = feed_info["url"]

                try:
                    response = await client.get(feed_url, headers={"User-Agent": "Mozilla/5.0 (AI News Intelligence Agent MVP)"})
                    if response.status_code != 200:
                        logger.warning(f"Failed to fetch feed {feed_name}: HTTP {response.status_code}")
                        continue

                    parsed = feedparser.parse(response.content)
                    if parsed.bozo and not parsed.entries:
                        logger.warning(f"Malformed XML from feed {feed_name}")
                        continue

                    for entry in parsed.entries:
                        if len(articles) >= limit:
                            break

                        title = getattr(entry, "title", "").strip()
                        link = getattr(entry, "link", "").strip()

                        if not title or not link:
                            continue

                        summary = getattr(entry, "summary", getattr(entry, "description", ""))
                        published_at = self._parse_published_date(entry)
                        source_updated_at = self._parse_updated_date(entry)
                        image_url = self._extract_image_url(entry)
                        entry_author = (
                            getattr(entry, "author", None)
                            or (getattr(entry, "author_detail", {}).get("name") if hasattr(entry, "author_detail") else None)
                            or "Staff Reporter"
                        )

                        articles.append({
                            "title": title,
                            "description": summary,
                            "url": link,
                            "source_name": feed_name,
                            "author": entry_author,
                            "published_at": published_at,
                            "source_updated_at": source_updated_at,
                            "image_url": image_url,
                            "topic": topic or "General"
                        })

                except Exception as exc:
                    logger.warning(f"Error fetching feed '{feed_name}' from {feed_url}: {exc}")
                    continue

        # Fallback to demo articles if network request failed to return any live feeds
        if not articles:
            logger.info("No live RSS articles fetched (network issue or offline). Falling back to demo data.")
            return get_demo_articles(topic or "artificial intelligence")

        return articles[:limit]


class NewsAPIProvider(BaseNewsProvider):
    """Primary NewsAPI.org Provider supporting search, latest recency, popular articles, and top headlines."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key if api_key is not None else os.getenv("NEWS_API_KEY")
        self.base_url = "https://newsapi.org/v2"
        self.rss_fallback_provider = RSSNewsProvider()


    async def fetch_articles(
        self, topic: Optional[str] = None, limit: int = 50, sort: Optional[str] = "latest"
    ) -> List[Dict[str, Any]]:
        # Check DEMO_MODE override
        demo_mode = os.getenv("DEMO_MODE", "false").lower() in ["true", "1", "yes"]
        if demo_mode:
            logger.info("DEMO_MODE active. Returning deterministic demo article dataset.")
            return get_demo_articles(topic or "artificial intelligence")

        if not self.api_key or not self.api_key.strip():
            logger.warning("NEWS_API_KEY missing or empty. Gracefully falling back to RSSNewsProvider.")
            return await self.rss_fallback_provider.fetch_articles(topic=topic, limit=limit, sort=sort)

        headers = {"X-Api-Key": self.api_key.strip()}
        page_size = min(max(limit, 1), 100)
        query_topic = (topic or "").strip()

        # Determine endpoint and query params based on sort mode
        sort_mode = (sort or "latest").lower()
        if sort_mode == "top":
            endpoint = f"{self.base_url}/top-headlines"
            params = {"pageSize": page_size}
            if query_topic:
                params["q"] = query_topic
            else:
                params["country"] = "us"
        elif sort_mode == "popular":
            endpoint = f"{self.base_url}/everything"
            params = {
                "q": query_topic or "technology",
                "sortBy": "popularity",
                "language": "en",
                "pageSize": page_size,
            }
        else:
            # Default / latest recency
            endpoint = f"{self.base_url}/everything"
            params = {
                "q": query_topic or "technology",
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": page_size,
            }

        articles: List[Dict[str, Any]] = []
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(endpoint, params=params, headers=headers)
                if resp.status_code != 200:
                    try:
                        err_json = resp.json()
                        err_msg = err_json.get("message", resp.text)
                    except Exception:
                        err_msg = resp.text
                    logger.warning(f"NewsAPI HTTP {resp.status_code} error: {err_msg}. Falling back to RSS provider.")
                    return await self.rss_fallback_provider.fetch_articles(topic=topic, limit=limit, sort=sort)

                data = resp.json()
                if data.get("status") != "ok":
                    err_msg = data.get("message", "Unknown NewsAPI error")
                    logger.warning(f"NewsAPI returned status '{data.get('status')}': {err_msg}. Falling back to RSS.")
                    return await self.rss_fallback_provider.fetch_articles(topic=topic, limit=limit, sort=sort)

                raw_articles = data.get("articles", [])
                for item in raw_articles:
                    title = (item.get("title") or "").strip()
                    url = (item.get("url") or "").strip()

                    # Filter removed or invalid articles
                    if not title or not url or title == "[Removed]" or url == "https://removed.com":
                        continue

                    source_info = item.get("source") or {}
                    source_name = source_info.get("name") if isinstance(source_info, dict) else "NewsAPI"
                    published_raw = item.get("publishedAt")
                    pub_iso = published_raw.strip() if isinstance(published_raw, str) and published_raw.strip() else None

                    articles.append({
                        "title": title,
                        "description": (item.get("description") or "").strip(),
                        "content": (item.get("content") or item.get("description") or "").strip(),
                        "url": url,
                        "source_name": source_name or "NewsAPI",
                        "author": item.get("author"),
                        "published_at": pub_iso,
                        "source_updated_at": None,
                        "image_url": item.get("urlToImage"),
                        "topic": topic or "General"
                    })

        except Exception as exc:
            logger.warning(f"Exception during NewsAPI fetch ({exc}). Falling back to RSS provider.")
            return await self.rss_fallback_provider.fetch_articles(topic=topic, limit=limit, sort=sort)

        if not articles:
            logger.info("NewsAPI returned 0 articles. Falling back to RSS provider.")
            return await self.rss_fallback_provider.fetch_articles(topic=topic, limit=limit, sort=sort)

        return articles[:limit]


class GNewsProvider(BaseNewsProvider):
    """GNews.io API Provider supporting real-time top headlines and keyword queries."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key if api_key is not None else os.getenv("GNEWS_API_KEY")
        self.base_url = "https://gnews.io/api/v4"
        self.rss_fallback_provider = RSSNewsProvider()

    async def fetch_articles(
        self, topic: Optional[str] = None, limit: int = 50, sort: Optional[str] = "latest"
    ) -> List[Dict[str, Any]]:
        demo_mode = os.getenv("DEMO_MODE", "false").lower() in ["true", "1", "yes"]
        if demo_mode:
            logger.info("DEMO_MODE active. Returning deterministic demo article dataset.")
            return get_demo_articles(topic or "artificial intelligence")

        if not self.api_key or not self.api_key.strip():
            logger.warning("GNEWS_API_KEY missing or empty. Gracefully falling back to RSSNewsProvider.")
            return await self.rss_fallback_provider.fetch_articles(topic=topic, limit=limit, sort=sort)

        query_topic = (topic or "").strip()
        endpoint = f"{self.base_url}/search" if query_topic else f"{self.base_url}/top-headlines"
        params = {
            "apikey": self.api_key.strip(),
            "max": min(max(limit, 1), 50),
            "lang": "en",
        }
        if query_topic:
            params["q"] = query_topic
        else:
            params["category"] = "general"

        articles: List[Dict[str, Any]] = []
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(endpoint, params=params)
                if resp.status_code != 200:
                    logger.warning(f"GNews API HTTP {resp.status_code}. Falling back to RSS.")
                    return await self.rss_fallback_provider.fetch_articles(topic=topic, limit=limit, sort=sort)

                data = resp.json()
                for item in data.get("articles", []):
                    title = (item.get("title") or "").strip()
                    url = (item.get("url") or "").strip()
                    if not title or not url:
                        continue
                    articles.append({
                        "title": title,
                        "description": (item.get("description") or "").strip(),
                        "content": (item.get("content") or item.get("description") or "").strip(),
                        "url": url,
                        "source_name": (item.get("source") or {}).get("name", "GNews"),
                        "author": None,
                        "published_at": item.get("publishedAt"),
                        "source_updated_at": None,
                        "image_url": item.get("image"),
                        "topic": topic or "General"
                    })
        except Exception as exc:
            logger.warning(f"Exception during GNews fetch ({exc}). Falling back to RSS.")
            return await self.rss_fallback_provider.fetch_articles(topic=topic, limit=limit, sort=sort)

        if not articles:
            return await self.rss_fallback_provider.fetch_articles(topic=topic, limit=limit, sort=sort)

        return articles[:limit]


def get_news_provider(provider_name: Optional[str] = None) -> BaseNewsProvider:
    """Factory function for instantiating the appropriate news provider."""
    demo_mode = os.getenv("DEMO_MODE", "false").lower() in ["true", "1", "yes"]
    if demo_mode:
        return RSSNewsProvider()  # RSSNewsProvider handles DEMO_MODE internally

    name = (provider_name or os.getenv("NEWS_PROVIDER", "rss")).lower()
    api_key = os.getenv("NEWS_API_KEY")

    if name == "gnews":
        gnews_key = os.getenv("GNEWS_API_KEY")
        return GNewsProvider(api_key=gnews_key.strip() if gnews_key else None)

    if name == "newsapi" and api_key and api_key.strip():
        return NewsAPIProvider(api_key=api_key.strip())

    return RSSNewsProvider()

