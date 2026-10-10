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

export interface TrustScore {
  score: number;
  label: string;
  corroboration_score: number;
  publisher_credibility_score: number;
  confidence_level: string;
}

export interface ClaimCheck {
  claim_text: string;
  status: string;
  corroborating_sources: string[];
  details: string;
}

export interface PublisherCredibility {
  source_name: string;
  credibility_tier: string;
  rating: string;
  domain_authority_score: number;
}

export interface VerificationResponse {
  story_id: string;
  headline: string;
  trust_score: TrustScore;
  publisher_credibility: PublisherCredibility[];
  claim_checks: ClaimCheck[];
  summary: string;
  total_sources: number;
  total_articles: number;
  is_demo: boolean;
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
  verification?: VerificationResponse;
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

