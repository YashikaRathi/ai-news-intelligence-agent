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
    def parse_timestamp(date_val: Any) -> datetime:
        """Parse datetime object or ISO date string into UTC datetime."""
        if isinstance(date_val, datetime):
            return date_val.astimezone(timezone.utc) if date_val.tzinfo else date_val
        if isinstance(date_val, str) and date_val:
            try:
                # Handle standard ISO format strings
                dt = datetime.fromisoformat(date_val.replace("Z", "+00:00"))
                return dt.astimezone(timezone.utc) if dt.tzinfo else dt
            except Exception:
                pass
        return datetime.now(timezone.utc)

    def normalize_article(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize raw RSS article data dictionary into structured canonical format."""
        raw_url = raw_data.get("url", "").strip()
        canonical_url = self.normalize_url(raw_url)
        title = self.clean_html(raw_data.get("title", ""))
        normalized_title = self.normalize_title(title)
        article_id = self.generate_article_id(canonical_url if canonical_url else title)

        description = self.clean_html(raw_data.get("description", ""))
        published_at = self.parse_timestamp(raw_data.get("published_at"))

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
            "topic": raw_data.get("topic", "General"),
            "checksum": article_id,
        }
