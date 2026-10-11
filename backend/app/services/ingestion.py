import re
import hashlib
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from datetime import datetime, timezone
from typing import Dict, Any, Optional

class IngestionService:
    """Service responsible for article discovery, cleaning, and normalization."""

    @staticmethod
    def clean_html(text: Optional[str]) -> str:
        """Strip HTML tags and normalize whitespace."""
        if not text:
            return ""
        # Remove HTML tags
        clean = re.sub(r"<[^>]+>", " ", text)
        # Normalize whitespace (replace multiple spaces/newlines with a single space)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    @staticmethod
    def normalize_title(title: str) -> str:
        """Clean whitespace, lowercase, and strip common punctuation for matching."""
        cleaned = IngestionService.clean_html(title).lower()
        # Remove non-alphanumeric characters except spaces
        cleaned = re.sub(r"[^\w\s]", "", cleaned)
        return re.sub(r"\s+", " ", cleaned).strip()

    @staticmethod
    def normalize_url(url: str) -> str:
        """Remove tracking parameters (utm_*, fbclid, gclid, etc.) to get a canonical URL."""
        if not url:
            return ""
        try:
            parsed = urlparse(url.strip())
            # Tracking query parameters to strip
            tracking_params = {
                "utm_source", "utm_medium", "utm_campaign", "utm_term",
                "utm_content", "fbclid", "gclid", "ref", "source", "mc_cid", "mc_eid"
            }
            query_dict = parse_qs(parsed.query, keep_blank_values=False)
            filtered_query = {k: v for k, v in query_dict.items() if k.lower() not in tracking_params}
            
            new_query = urlencode(filtered_query, doseq=True)
            # Reconstruct canonical URL (strip trailing slashes)
            canonical = urlunparse((
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                parsed.path.rstrip("/"),
                parsed.params,
                new_query,
                ""  # strip fragment
            ))
            return canonical
        except Exception:
            return url.strip()

    @staticmethod
    def generate_article_id(canonical_url: str) -> str:
        """Generate a deterministic SHA256 hex string ID from canonical URL."""
        return hashlib.sha256(canonical_url.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def parse_timestamp(date_val: Any) -> Optional[datetime]:
        """Parse datetime object, ISO date string, or RFC 822 string into timezone-aware UTC datetime.
        
        Explicit Policy for Naive Datetimes:
        When an ingested source timestamp contains no explicit timezone offset:
        - Per standard internet news syndication and API conventions, naive timestamps from providers
          are interpreted as UTC.
        - The timestamp is assigned timezone.utc without altering the wall-clock value.
        
        Returns None if date_val is None, empty, or unparseable. NEVER returns current time.
        """
        if date_val is None:
            return None

        if isinstance(date_val, datetime):
            if date_val.tzinfo is not None:
                return date_val.astimezone(timezone.utc)
            return date_val.replace(tzinfo=timezone.utc)

        if isinstance(date_val, str):
            clean_val = date_val.strip()
            if not clean_val:
                return None

            # 1. Standard ISO format strings (handling Z and explicit offsets)
            try:
                iso_str = clean_val.replace("Z", "+00:00")
                dt = datetime.fromisoformat(iso_str)
                if dt.tzinfo is not None:
                    return dt.astimezone(timezone.utc)
                return dt.replace(tzinfo=timezone.utc)
            except Exception:
                pass

            # 2. RFC 2822 / email timestamp format
            try:
                import email.utils
                parsed_tuple = email.utils.parsedate_tz(clean_val)
                if parsed_tuple:
                    ts = email.utils.mktime_tz(parsed_tuple)
                    return datetime.fromtimestamp(ts, tz=timezone.utc)
            except Exception:
                pass

        return None

    def normalize_article(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize raw RSS article data dictionary into structured canonical format."""
        raw_url = raw_data.get("url", "").strip()
        canonical_url = self.normalize_url(raw_url)
        title = self.clean_html(raw_data.get("title", ""))
        normalized_title = self.normalize_title(title)
        article_id = self.generate_article_id(canonical_url if canonical_url else title)

        description = self.clean_html(raw_data.get("description", ""))
        published_at = self.parse_timestamp(raw_data.get("published_at"))
        source_updated_at = self.parse_timestamp(raw_data.get("source_updated_at"))

        return {
            "id": article_id,
            "title": title,
            "normalized_title": normalized_title,
            "description": description,
            "content": raw_data.get("content", description),
            "url": raw_url,
            "canonical_url": canonical_url,
            "source_name": raw_data.get("source_name", "Unknown Source").strip(),
            "author": self.clean_html(raw_data.get("author")) or None,
            "image_url": raw_data.get("image_url"),
            "published_at": published_at,
            "source_updated_at": source_updated_at,
            "topic": raw_data.get("topic", "General"),
            "checksum": article_id,
        }
