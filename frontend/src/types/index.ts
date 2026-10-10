export interface FactCheckItem {
  claim: string;
  claimant?: string;
  fact_check_publisher: string;
  review_date?: string;
  original_rating: string;
  normalized_status: string;
  fact_check_url: string;
}

export interface VerificationResult {
  article_id: string;
  publisher_domain: string;
  credibility_status: string;
  source_rating?: {
    domain: string;
    rating: string;
    explanation: string;
    provenance: string;
  };
  fact_check_status: string;
  fact_checks: FactCheckItem[];
  discrepancy_status: string;
  cross_source_findings: Record<string, any>;
  limitations: string[];
  last_checked_at: string;
}

export interface StoryVerificationSummary {
  story_id: string;
  total_articles: number;
  verified_fact_checks_count: number;
  disputed_fact_checks_count: number;
  discrepancy_status: string;
  high_credibility_sources_count: number;
  unverified_sources_count: number;
  fact_checks: FactCheckItem[];
  cross_source_findings: Record<string, any>;
  limitations: string[];
  last_checked_at: string;
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
  published_at?: string;
  topic?: string;
  story_id?: string;
  is_duplicate?: boolean;
  duplicate_of_id?: string;
  publisher_domain?: string;
  credibility_status?: string;
  fact_check_status?: string;
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
  earliest_published_at?: string;
  latest_published_at?: string;
  article_count: number;
  is_demo_data?: boolean;
  discrepancy_status?: string;
  fact_check_status?: string;
  articles?: Article[];
}

export interface TimelineEvent {
  article_id: string;
  title: string;
  source_name: string;
  published_at?: string;
  url: string;
  author?: string;
  image_url?: string;
}

export interface StoryTimeline {
  story_id: string;
  story_title: string;
  topic: string;
  total_articles: number;
  earliest_published_at?: string;
  latest_published_at?: string;
  timeline: TimelineEvent[];
}

export interface EvidenceItem {
  article_id: string;
  source_name: string;
  title: string;
  url: string;
  published_at?: string;
}

export interface SourceComparisonItem {
  source_name: string;
  headline: string;
  url: string;
  published_at?: string;
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
