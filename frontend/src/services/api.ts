import axios from 'axios';
import {
  HealthResponse,
  Article,
  Story,
  StoryTimeline,
  StoryIntelligence,
  SearchResult,
  ChatResponse,
  VerificationResult,
  StoryVerificationSummary,
  ReviewSummary,
  ReviewItem,
  ReviewCreatePayload,
  NotificationListResponse,
  NotificationItem,
  NotificationPreference,
  FreshnessOption,
} from '../types';

const getBaseURL = () => {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  return 'http://127.0.0.1:8000';
};

export const getOrCreateReaderId = (): string => {
  try {
    let rid = localStorage.getItem('reader_id');
    if (!rid) {
      rid = `reader_${Math.random().toString(36).substring(2, 10)}`;
      localStorage.setItem('reader_id', rid);
    }
    return rid;
  } catch {
    return 'reader_guest';
  }
};

const API = axios.create({
  baseURL: getBaseURL(),
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 12000,
});

export const getHealth = async (): Promise<HealthResponse> => {
  try {
    const response = await API.get<HealthResponse>('/health');
    return response.data;
  } catch (primaryErr) {
    try {
      const fallbackUrl = API.defaults.baseURL?.includes('127.0.0.1')
        ? 'http://localhost:8000/health'
        : 'http://127.0.0.1:8000/health';
      const response = await axios.get<HealthResponse>(fallbackUrl, { timeout: 5000 });
      return response.data;
    } catch {
      throw primaryErr;
    }
  }
};

export const getNews = async (
  topic?: string,
  limit = 20,
  sort = 'latest',
  freshness: FreshnessOption = 'all'
): Promise<Article[]> => {
  const params: Record<string, any> = { limit, sort };
  if (topic) params.topic = topic;
  if (freshness && freshness !== 'all') params.freshness = freshness;
  const response = await API.get<Article[]>('/api/news', { params });
  return response.data;
};

export const getStories = async (
  topic?: string,
  limit = 20,
  freshness: FreshnessOption = 'all',
  sortBy: 'latest' | 'updated' = 'latest'
): Promise<Story[]> => {
  const params: Record<string, any> = { limit, sort_by: sortBy };
  if (topic) params.topic = topic;
  if (freshness && freshness !== 'all') params.freshness = freshness;
  const response = await API.get<Story[]>('/api/stories', { params });
  return response.data;
};

export const getStory = async (storyId: string): Promise<Story> => {
  const response = await API.get<Story>(`/api/stories/${storyId}`);
  return response.data;
};

export const getTimeline = async (storyId: string): Promise<StoryTimeline> => {
  const response = await API.get<StoryTimeline>(`/api/stories/${storyId}/timeline`);
  return response.data;
};

export const getStoryIntelligence = async (storyId: string): Promise<StoryIntelligence> => {
  const response = await API.get<StoryIntelligence>(`/api/ai/stories/${storyId}/intelligence`);
  return response.data;
};

export const searchNews = async (
  query: string,
  limit = 20,
  freshness: FreshnessOption = 'all',
  sortBy: 'relevance' | 'latest' = 'relevance'
): Promise<SearchResult> => {
  const params: Record<string, any> = { q: query, limit, sort_by: sortBy };
  if (freshness && freshness !== 'all') params.freshness = freshness;
  const response = await API.get<SearchResult>('/api/search', { params });
  return response.data;
};

export const askNews = async (storyId: string | null, question: string): Promise<ChatResponse> => {
  const response = await API.post<ChatResponse>('/api/ai/chat', {
    story_id: storyId,
    question,
  });
  return response.data;
};

export const getArticleVerification = async (articleId: string): Promise<VerificationResult> => {
  const response = await API.get<VerificationResult>(`/api/verification/article/${articleId}`);
  return response.data;
};

export const getStoryVerification = async (storyId: string): Promise<StoryVerificationSummary> => {
  const response = await API.get<StoryVerificationSummary>(`/api/verification/story/${storyId}`);
  return response.data;
};

export const refreshVerification = async (storyId?: string): Promise<any> => {
  const response = await API.post('/api/verification/refresh', null, {
    params: { story_id: storyId },
  });
  return response.data;
};

// --- Reader Reviews & Ratings APIs ---

export const getReviewsSummary = async (targetType: 'article' | 'story', targetId: string): Promise<ReviewSummary> => {
  const readerId = getOrCreateReaderId();
  const response = await API.get<ReviewSummary>(`/api/reviews/${targetType}/${targetId}`, {
    headers: { 'X-Reader-Id': readerId },
  });
  return response.data;
};

export const submitReview = async (
  targetType: 'article' | 'story',
  targetId: string,
  payload: ReviewCreatePayload
): Promise<ReviewItem> => {
  const readerId = getOrCreateReaderId();
  const response = await API.post<ReviewItem>(`/api/reviews/${targetType}/${targetId}`, payload, {
    headers: { 'X-Reader-Id': readerId },
  });
  return response.data;
};

export const updateReview = async (
  reviewId: string,
  payload: Partial<ReviewCreatePayload>
): Promise<ReviewItem> => {
  const readerId = getOrCreateReaderId();
  const response = await API.put<ReviewItem>(`/api/reviews/${reviewId}`, payload, {
    headers: { 'X-Reader-Id': readerId },
  });
  return response.data;
};

export const deleteReview = async (reviewId: string): Promise<any> => {
  const readerId = getOrCreateReaderId();
  const response = await API.delete(`/api/reviews/${reviewId}`, {
    headers: { 'X-Reader-Id': readerId },
  });
  return response.data;
};

// --- In-App Notifications APIs ---

export const getNotifications = async (): Promise<NotificationListResponse> => {
  const readerId = getOrCreateReaderId();
  const response = await API.get<NotificationListResponse>('/api/notifications', {
    headers: { 'X-Reader-Id': readerId },
  });
  return response.data;
};

export const markNotificationRead = async (notificationId: string): Promise<NotificationItem> => {
  const response = await API.patch<NotificationItem>(`/api/notifications/${notificationId}/read`);
  return response.data;
};

export const markAllNotificationsRead = async (): Promise<any> => {
  const readerId = getOrCreateReaderId();
  const response = await API.post('/api/notifications/read-all', null, {
    headers: { 'X-Reader-Id': readerId },
  });
  return response.data;
};

export const getNotificationPreferences = async (): Promise<NotificationPreference> => {
  const readerId = getOrCreateReaderId();
  const response = await API.get<NotificationPreference>('/api/notifications/preferences', {
    headers: { 'X-Reader-Id': readerId },
  });
  return response.data;
};

export const updateNotificationPreferences = async (
  payload: Partial<NotificationPreference>
): Promise<NotificationPreference> => {
  const readerId = getOrCreateReaderId();
  const response = await API.put<NotificationPreference>('/api/notifications/preferences', payload, {
    headers: { 'X-Reader-Id': readerId },
  });
  return response.data;
};
