export interface FactCheckItem {
  claim: string;
  claimant?: string;
  fact_check_publisher: string;
  review_date?: string;
  original_rating: string;
  normalized_status: string; // 'Fact-check rated TRUE', 'Fact-check rated FALSE', 'Mixed or partially true'
  fact_check_url: string;
}

export type FreshnessOption = '1h' | '6h' | '24h' | '7d' | 'all';

export interface SourceRating {
  domain: string;
  assessment_status: string; // 'rated' or 'not_assessed'
  rating: string; // 'high_credibility', 'medium_credibility', 'caution_advised', 'not_assessed'
  explanation: string;
  provenance: string;
  limitations?: string;
}

export interface CitationItem {
  article_id?: string;
  title?: string;
  source_name: string;
  url: string;
  published_at?: string;
  is_duplicate?: boolean;
}

export interface CrossSourceFindings {
  agreements: string[];
  differences: string[];
  single_source_claims: string[];
  independent_sources: string[];
  syndicated_sources: string[];
  summary: string;
  citations: CitationItem[];
}

export interface VerificationResult {
  article_id: string;
  publisher_domain: string;
  overall_status: string; // 'Fact-check rated TRUE', 'Fact-check rated FALSE', 'Mixed or partially true', 'Conflicting reports', 'Insufficient evidence', 'No matching fact-check found', 'Not checked'
  status_reason: string;
  publisher_credibility_status: string;
  source_rating?: SourceRating;
  fact_check_status: string;
  fact_checks: FactCheckItem[];
  discrepancy_status: string;
  cross_source_findings: CrossSourceFindings | Record<string, any>;
  limitations: string[];
  last_checked_at?: string;
  credibility_status?: string; // backward compat
}

export interface StoryVerificationSummary {
  story_id: string;
  total_articles: number;
  overall_status: string;
  status_reason: string;
  verified_fact_checks_count: number;
  disputed_fact_checks_count: number;
  discrepancy_status: string;
  high_credibility_sources_count: number;
  not_assessed_sources_count: number;
  unverified_sources_count?: number; // backward compat
  fact_checks: FactCheckItem[];
  cross_source_findings: CrossSourceFindings | Record<string, any>;
  limitations: string[];
  last_checked_at?: string;
}

export interface Article {
  id: string;
  title: string;
  description?: string;
  content?: string;
  url: string;
  canonical_url?: string;
  source_name: string;
  author?: string;
  image_url?: string;
  published_at?: string | null;
  source_updated_at?: string | null;
  ingested_at?: string | null;
  verified_at?: string | null;
  topic?: string;
  story_id?: string;
  is_duplicate?: boolean;
  duplicate_of_id?: string;
  publisher_domain?: string;
  credibility_status?: string;
  fact_check_status?: string;
  overall_verification_status?: string;
  created_at?: string;
}

export interface Story {
  id: string;
  title: string;
  summary?: string;
  what_changed?: string;
  why_it_matters?: string;
  topic?: string;
  category?: string;
  first_seen?: string;
  last_updated?: string;
  earliest_published_at?: string | null;
  latest_published_at?: string | null;
  article_count: number;
  is_demo_data?: boolean;
  discrepancy_status?: string;
  fact_check_status?: string;
  overall_verification_status?: string;
  status_reason?: string;
  articles?: Article[];
}

export interface TimelineEvent {
  article_id: string;
  title: string;
  source_name: string;
  published_at?: string | null;
  url: string;
  author?: string;
  image_url?: string;
}

export interface StoryTimeline {
  story_id: string;
  story_title: string;
  topic: string;
  total_articles: number;
  earliest_published_at?: string | null;
  latest_published_at?: string | null;
  timeline: TimelineEvent[];
}

export interface EvidenceItem {
  article_id: string;
  source_name: string;
  title: string;
  url: string;
  published_at?: string | null;
}

export interface SourceComparisonItem {
  source_name: string;
  headline: string;
  url: string;
  published_at?: string | null;
  emphasis: string;
  differences: string;
  agreement: string;
}

export interface StoryIntelligence {
  story_id: string;
  headline: string;
  topic: string;
  what_happened: string;
  what_changed: string;
  why_it_matters: string;
  key_points: string[];
  entities: string[];
  sources: string[];
  evidence: EvidenceItem[];
  source_comparison: SourceComparisonItem[];
  discrepancy_status?: string;
  fact_checks?: FactCheckItem[];
  verification_summary?: StoryVerificationSummary;
  confidence: string;
  is_demo: boolean;
}

export interface ChatSourceItem {
  article_id: string;
  source: string;
  title: string;
  url: string;
}

export interface ChatResponse {
  answer: string;
  sources: ChatSourceItem[];
  is_demo: boolean;
}

export interface SearchResult {
  query: string;
  article_count: number;
  story_count: number;
  articles: Article[];
  stories: Story[];
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  database: string;
}

// Reader Ratings & Reviews Types
export interface ReviewItem {
  id: string;
  target_type: string;
  target_id: string;
  reader_id: string;
  reader_name: string;
  rating: number;
  review_text?: string;
  created_at: string;
  updated_at: string;
}

export interface ReviewSummary {
  target_type: string;
  target_id: string;
  average_rating: number;
  total_ratings: number;
  rating_distribution: Record<string, number>;
  user_review?: ReviewItem | null;
  reviews: ReviewItem[];
  disclaimer: string;
}

export interface ReviewCreatePayload {
  rating: number;
  review_text?: string;
  reader_name?: string;
}

// Notification Types
export interface NotificationItem {
  id: string;
  recipient_id: string;
  event_type: 'topic_alert' | 'story_update' | 'verification_change' | 'contradiction_alert' | string;
  title: string;
  message: string;
  story_id?: string;
  article_id?: string;
  topic?: string;
  is_read: boolean;
  created_at: string;
}

export interface NotificationListResponse {
  unread_count: number;
  total_count: number;
  notifications: NotificationItem[];
}

export interface NotificationPreference {
  reader_id: string;
  followed_topics: string[];
  followed_stories: string[];
  categories_enabled: string[];
  notifications_enabled: boolean;
  updated_at?: string;
}
