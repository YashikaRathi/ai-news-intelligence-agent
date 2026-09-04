import math
from collections import Counter
from typing import Dict, Any, List, Tuple

class DeduplicationService:
    """Service responsible for Exact and Near Duplicate Detection."""

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple word tokenizer removing short stop words."""
        stop_words = {
            "a", "an", "the", "in", "on", "of", "to", "for", "with", "by", "at",
            "from", "as", "is", "was", "are", "were", "and", "or", "it", "its", "has", "have"
        }
        words = text.lower().split()
        return [w for w in words if len(w) > 1 and w not in stop_words]

    @classmethod
    def jaccard_similarity(cls, text_a: str, text_b: str) -> float:
        """Calculate Jaccard similarity between two texts."""
        set_a = set(cls._tokenize(text_a))
        set_b = set(cls._tokenize(text_b))
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        return intersection / union if union > 0 else 0.0

    @classmethod
    def cosine_similarity_tfidf(cls, text_a: str, text_b: str) -> float:
        """Calculate word frequency Cosine similarity between two texts."""
        tokens_a = cls._tokenize(text_a)
        tokens_b = cls._tokenize(text_b)
        
        if not tokens_a or not tokens_b:
            return 0.0

        vec_a = Counter(tokens_a)
        vec_b = Counter(tokens_b)

        intersection = set(vec_a.keys()) & set(vec_b.keys())
        dot_product = sum(vec_a[x] * vec_b[x] for x in intersection)

        norm_a = math.sqrt(sum(count ** 2 for count in vec_a.values()))
        norm_b = math.sqrt(sum(count ** 2 for count in vec_b.values()))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def is_exact_duplicate(self, article_a: Dict[str, Any], article_b: Dict[str, Any]) -> bool:
        """Check if two articles are exact duplicates based on canonical URL or normalized title."""
        url_match = (
            article_a.get("canonical_url") and
            article_b.get("canonical_url") and
            article_a["canonical_url"] == article_b["canonical_url"]
        )
        title_match = (
            article_a.get("normalized_title") and
            article_b.get("normalized_title") and
            article_a["normalized_title"] == article_b["normalized_title"]
        )
        return bool(url_match or title_match)

    def is_near_duplicate(self, article_a: Dict[str, Any], article_b: Dict[str, Any], threshold: float = 0.65) -> bool:
        """Check if two articles are near duplicates based on title and description similarity."""
        title_sim = self.cosine_similarity_tfidf(
            article_a.get("normalized_title", ""),
            article_b.get("normalized_title", "")
        )
        if title_sim >= threshold:
            return True

        # Combine title and description for secondary check
        text_a = f"{article_a.get('title', '')} {article_a.get('description', '')}"
        text_b = f"{article_b.get('title', '')} {article_b.get('description', '')}"

        jaccard_sim = self.jaccard_similarity(text_a, text_b)
        return jaccard_sim >= threshold

    def process_duplicates(
        self,
        new_articles: List[Dict[str, Any]],
        existing_articles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process incoming articles against existing DB records to set is_duplicate & duplicate_of_id flags."""
        processed = []
        all_canonical_urls = {art.get("canonical_url") for art in existing_articles if art.get("canonical_url")}

        for art in new_articles:
            art_copy = dict(art)
            c_url = art_copy.get("canonical_url")

            # Exact URL check against DB
            if c_url in all_canonical_urls:
                art_copy["is_duplicate"] = True
                processed.append(art_copy)
                continue

            # Compare against existing non-duplicate articles
            is_dup = False
            for existing in existing_articles:
                if existing.get("is_duplicate"):
                    continue
                if self.is_exact_duplicate(art_copy, existing) or self.is_near_duplicate(art_copy, existing):
                    art_copy["is_duplicate"] = True
                    art_copy["duplicate_of_id"] = existing.get("id")
                    is_dup = True
                    break

            if not is_dup:
                art_copy["is_duplicate"] = False
                all_canonical_urls.add(c_url)

            processed.append(art_copy)

        return processed
