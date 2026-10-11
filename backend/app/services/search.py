import re
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.article import Article
from app.models.story import Story
from app.services.deduplication import DeduplicationService

STOP_WORDS = {
    "a", "an", "the", "in", "on", "of", "to", "for", "with", "by", "at",
    "from", "as", "is", "was", "are", "were", "and", "or", "it", "its", "has", "have",
    "that", "this", "be", "so", "about", "into", "over", "after", "up", "out", "all"
}

class SearchService:
    """Intelligent Search & Ranking Engine for news articles and story clusters."""

    def __init__(self, relevance_threshold: float = 8.0):
        self.relevance_threshold = relevance_threshold
        self.dedup_service = DeduplicationService()

    @staticmethod
    def parse_query(query: str) -> Dict[str, Any]:
        """Normalize, tokenize, and extract search intent from raw query strings."""
        raw_clean = query.strip()
        if not raw_clean:
            return {
                "clean_query": "",
                "original_query": "",
                "phrases": [],
                "all_terms": [],
                "content_terms": [],
                "acronyms": set()
            }

        # 1. Extract quoted phrases (e.g. '"James Webb" telescope')
        phrases = [p.strip().lower() for p in re.findall(r'"([^"]+)"', raw_clean) if p.strip()]
        no_quotes = re.sub(r'"[^"]+"', ' ', raw_clean)

        # 2. Tokenize while preserving acronyms, versions, and technical terms (e.g. GPT-5, 1.4nm)
        raw_tokens = [t.strip() for t in re.split(r'[\s,;:!?()]+', no_quotes) if t.strip()]
        cleaned_terms = [t.lower() for t in raw_tokens]

        # 3. Detect acronyms and technical terms (e.g. AI, NASA, TSMC, BBC, EV, CEO)
        acronyms = {t.lower() for t in raw_tokens if t.isupper() and 2 <= len(t) <= 5}

        # 4. Filter functional stop words to isolate content-bearing terms
        content_terms = [t for t in cleaned_terms if len(t) > 1 and t not in STOP_WORDS]
        if not content_terms and cleaned_terms:
            # Fall back to all terms if the entire query consists of stop words (e.g. "to be or not to be")
            content_terms = cleaned_terms[:]

        return {
            "clean_query": raw_clean.lower(),
            "original_query": raw_clean,
            "phrases": phrases,
            "all_terms": cleaned_terms,
            "content_terms": content_terms,
            "acronyms": acronyms
        }

    @staticmethod
    def has_whole_word(word: str, text: Optional[str]) -> bool:
        """Check if a word matches with strict whole-word boundaries (avoids 'ai' matching 'rains')."""
        if not text or not word:
            return False
        pattern = r'\b' + re.escape(word.lower()) + r'\b'
        return bool(re.search(pattern, text.lower()))

    @staticmethod
    def has_prefix_word(word: str, text: Optional[str]) -> bool:
        """Check if a word matches as a word prefix (e.g. 'flood' matching 'floods' or 'flooding')."""
        if not text or not word:
            return False
        pattern = r'\b' + re.escape(word.lower())
        return bool(re.search(pattern, text.lower()))

    def score_article(self, article: Article, pq: Dict[str, Any]) -> float:
        """Compute multi-factor relevance score for an article against a parsed query."""
        clean_q = pq["clean_query"]
        content_terms = pq["content_terms"]
        phrases = pq["phrases"]

        title = article.title or ""
        title_lower = title.lower()
        desc = article.description or ""
        desc_lower = desc.lower()
        topic = article.topic or ""
        source = article.source_name or ""
        author = article.author or ""

        score = 0.0
        matched_content_terms = 0

        # 1. Exact phrase and headline matches (Highest Priority)
        if title_lower == clean_q:
            score += 100.0
            matched_content_terms = len(content_terms)
        elif title_lower.startswith(clean_q):
            score += 65.0
            matched_content_terms = max(1, len(content_terms) - 1)
        elif clean_q in title_lower:
            score += 45.0
            matched_content_terms = max(1, len(content_terms) - 1)

        if clean_q in desc_lower and clean_q not in title_lower:
            score += 15.0

        for phrase in phrases:
            if phrase in title_lower:
                score += 35.0
            elif phrase in desc_lower:
                score += 12.0

        # 2. Strict Whole-Word & Prefix Term Matching (Headline > Description > Source/Author)
        for term in content_terms:
            term_matched = False
            if self.has_whole_word(term, title):
                score += 20.0
                term_matched = True
            elif self.has_prefix_word(term, title):
                score += 10.0
                term_matched = True

            if self.has_whole_word(term, desc):
                score += 5.0
                term_matched = True
            elif self.has_prefix_word(term, desc):
                score += 2.5
                term_matched = True

            if self.has_whole_word(term, topic):
                score += 6.0
                term_matched = True

            if self.has_whole_word(term, source) or self.has_whole_word(term, author):
                score += 8.0
                term_matched = True

            if term_matched:
                matched_content_terms += 1

        # Strict Noise Rejection: If no terms matched primary text fields (title, desc, source, author), discard
        has_primary_match = (
            clean_q in title_lower
            or clean_q in desc_lower
            or any(
                self.has_whole_word(t, title)
                or self.has_prefix_word(t, title)
                or self.has_whole_word(t, desc)
                or self.has_prefix_word(t, desc)
                or self.has_whole_word(t, source)
                or self.has_whole_word(t, author)
                for t in content_terms
            )
        )
        if not has_primary_match or (matched_content_terms == 0 and clean_q not in title_lower):
            return 0.0

        # 3. Query Term Coverage & Conjunction Multiplier
        num_terms = len(content_terms)
        if num_terms > 1:
            coverage = matched_content_terms / num_terms
            if coverage == 1.0:
                score += 25.0
            elif coverage >= 0.5:
                score += 10.0
            else:
                score *= 0.5  # Penalize incidental matches on 3+ word queries

        # 4. Semantic TF-IDF Similarity
        text_content = f"{title} {desc}"
        tfidf_sim = self.dedup_service.cosine_similarity_tfidf(clean_q, text_content)
        score += tfidf_sim * 12.0

        # 5. Fine-Grained Recency Tie-Breaker (Max 1.5 points to avoid outranking relevant older news)
        if article.published_at:
            try:
                pub_naive = article.published_at.replace(tzinfo=None) if hasattr(article.published_at, 'replace') else article.published_at
                now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
                age_hours = max(0.0, (now_naive - pub_naive).total_seconds() / 3600.0)
                recency_boost = 1.5 / (1.0 + (age_hours / 24.0))
                score += recency_boost
            except Exception:
                pass

        return score

    def score_story(self, story: Story, pq: Dict[str, Any]) -> float:
        """Compute multi-factor relevance score for a story cluster against a parsed query."""
        clean_q = pq["clean_query"]
        content_terms = pq["content_terms"]
        phrases = pq["phrases"]

        title = story.title or ""
        title_lower = title.lower()
        summary = story.summary or ""
        summary_lower = summary.lower()
        topic = story.topic or ""
        category = story.category or ""

        score = 0.0
        matched_content_terms = 0

        # 1. Exact phrase and headline matches
        if title_lower == clean_q:
            score += 100.0
            matched_content_terms = len(content_terms)
        elif title_lower.startswith(clean_q):
            score += 65.0
            matched_content_terms = max(1, len(content_terms) - 1)
        elif clean_q in title_lower:
            score += 45.0
            matched_content_terms = max(1, len(content_terms) - 1)

        if clean_q in summary_lower and clean_q not in title_lower:
            score += 15.0

        for phrase in phrases:
            if phrase in title_lower:
                score += 35.0
            elif phrase in summary_lower:
                score += 12.0

        # 2. Strict Whole-Word & Prefix Term Matching
        for term in content_terms:
            term_matched = False
            if self.has_whole_word(term, title):
                score += 20.0
                term_matched = True
            elif self.has_prefix_word(term, title):
                score += 10.0
                term_matched = True

            if self.has_whole_word(term, summary):
                score += 5.0
                term_matched = True
            elif self.has_prefix_word(term, summary):
                score += 2.5
                term_matched = True

            if self.has_whole_word(term, topic) or self.has_whole_word(term, category):
                score += 6.0
                term_matched = True

            if term_matched:
                matched_content_terms += 1

        # Strict Noise Rejection: Query must match title or summary
        has_primary_match = (
            clean_q in title_lower
            or clean_q in summary_lower
            or any(
                self.has_whole_word(t, title)
                or self.has_prefix_word(t, title)
                or self.has_whole_word(t, summary)
                or self.has_prefix_word(t, summary)
                for t in content_terms
            )
        )
        if not has_primary_match or (matched_content_terms == 0 and clean_q not in title_lower):
            return 0.0

        # 3. Query Term Coverage
        num_terms = len(content_terms)
        if num_terms > 1:
            coverage = matched_content_terms / num_terms
            if coverage == 1.0:
                score += 25.0
            elif coverage >= 0.5:
                score += 10.0
            else:
                score *= 0.5

        # 4. Semantic TF-IDF Similarity
        text_content = f"{title} {summary}"
        tfidf_sim = self.dedup_service.cosine_similarity_tfidf(clean_q, text_content)
        score += tfidf_sim * 12.0

        # 5. Recency Tie-Breaker (using actual story publication time)
        pub_ref = story.latest_published_at or story.last_updated
        if pub_ref:
            try:
                pub_naive = pub_ref.replace(tzinfo=None) if hasattr(pub_ref, 'replace') else pub_ref
                now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
                age_hours = max(0.0, (now_naive - pub_naive).total_seconds() / 3600.0)
                recency_boost = 1.5 / (1.0 + (age_hours / 24.0))
                score += recency_boost
            except Exception:
                pass

        return score

    @staticmethod
    def get_freshness_cutoff(freshness: Optional[str]) -> Optional[datetime]:
        """Convert freshness filter string ('1h', '6h', '24h', '7d', 'all') into naive UTC cutoff datetime."""
        if not freshness or freshness.lower().strip() in ["all", "any", "none", ""]:
            return None
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        f = freshness.lower().strip()
        if f in ["1h", "hour", "last_hour", "last hour"]:
            return now_utc - timedelta(hours=1)
        elif f in ["6h", "6hours", "last_6h", "last_6_hours", "last 6 hours"]:
            return now_utc - timedelta(hours=6)
        elif f in ["24h", "day", "last_24h", "last_day", "today", "last 24 hours"]:
            return now_utc - timedelta(hours=24)
        elif f in ["7d", "week", "last_7d", "last_week", "last 7 days"]:
            return now_utc - timedelta(days=7)
        return None

    def search_articles_and_stories(
        self,
        db: Session,
        query: str,
        limit: int = 20,
        freshness: Optional[str] = "all",
        sort_by: Optional[str] = "relevance"
    ) -> Tuple[List[Article], List[Story]]:
        """Execute candidate retrieval, precision relevance scoring, deduplication filtering, freshness windowing, and ranking."""
        pq = self.parse_query(query)
        clean_q = pq["clean_query"]
        if not clean_q:
            return [], []

        content_terms = pq["content_terms"]
        cutoff = self.get_freshness_cutoff(freshness)

        # 1. Candidate Retrieval for Articles
        # Exclude exact duplicate syndicated copies so they do not crowd out distinct results
        art_base_query = db.query(Article).filter(Article.is_duplicate.is_(False))
        if cutoff:
            art_base_query = art_base_query.filter(Article.published_at.isnot(None), Article.published_at >= cutoff)

        candidate_filters = [
            Article.title.ilike(f"%{clean_q}%"),
            Article.description.ilike(f"%{clean_q}%"),
            Article.source_name.ilike(f"%{clean_q}%"),
            Article.topic.ilike(f"%{clean_q}%"),
            Article.author.ilike(f"%{clean_q}%")
        ]
        for term in content_terms:
            if len(term) >= 2:
                candidate_filters.append(Article.title.ilike(f"%{term}%"))
                candidate_filters.append(Article.description.ilike(f"%{term}%"))
                candidate_filters.append(Article.source_name.ilike(f"%{term}%"))
                candidate_filters.append(Article.author.ilike(f"%{term}%"))

        article_candidates = art_base_query.filter(or_(*candidate_filters)).limit(100).all()

        # Score & Rank Articles
        scored_articles: List[Tuple[float, Article]] = []
        for art in article_candidates:
            score = self.score_article(art, pq)
            if score >= self.relevance_threshold:
                scored_articles.append((score, art))

        if sort_by == "latest":
            scored_articles.sort(
                key=lambda x: (
                    x[1].published_at.replace(tzinfo=None) if hasattr(x[1].published_at, 'replace') else (x[1].published_at or datetime.min)
                ),
                reverse=True
            )
        else:
            scored_articles.sort(key=lambda x: x[0], reverse=True)

        ranked_articles = [art for _, art in scored_articles[:limit]]

        # 2. Candidate Retrieval for Stories
        story_query = db.query(Story)
        if cutoff:
            story_query = story_query.filter(Story.latest_published_at.isnot(None), Story.latest_published_at >= cutoff)

        story_filters = [
            Story.title.ilike(f"%{clean_q}%"),
            Story.summary.ilike(f"%{clean_q}%"),
            Story.topic.ilike(f"%{clean_q}%"),
            Story.category.ilike(f"%{clean_q}%")
        ]
        for term in content_terms:
            if len(term) >= 2:
                story_filters.append(Story.title.ilike(f"%{term}%"))
                story_filters.append(Story.summary.ilike(f"%{term}%"))
                story_filters.append(Story.topic.ilike(f"%{term}%"))

        story_candidates = story_query.filter(or_(*story_filters)).limit(100).all()

        # Score & Rank Stories
        scored_stories: List[Tuple[float, Story]] = []
        for st in story_candidates:
            score = self.score_story(st, pq)
            if score >= self.relevance_threshold:
                scored_stories.append((score, st))

        if sort_by == "latest":
            scored_stories.sort(
                key=lambda x: (
                    x[1].latest_published_at.replace(tzinfo=None) if hasattr(x[1].latest_published_at, 'replace') else (x[1].latest_published_at or datetime.min)
                ),
                reverse=True
            )
        else:
            scored_stories.sort(key=lambda x: x[0], reverse=True)

        ranked_stories = [st for _, st in scored_stories[:limit]]

        return ranked_articles, ranked_stories

get_freshness_cutoff = SearchService.get_freshness_cutoff
