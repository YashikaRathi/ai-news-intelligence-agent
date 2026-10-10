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
} from '../types';

const getBaseURL = () => {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  // Default to http://127.0.0.1:8000 to prevent IPv6 localhost resolution mismatch on Windows
  return 'http://127.0.0.1:8000';
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
    // Attempt fallback to http://localhost:8000/health if primary 127.0.0.1 call failed
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

export const getNews = async (topic?: string, limit = 20, sort = 'latest'): Promise<Article[]> => {
  const params: Record<string, any> = { limit, sort };
  if (topic) params.topic = topic;
  const response = await API.get<Article[]>('/api/news', { params });
  return response.data;
};


export const getStories = async (topic?: string, limit = 20): Promise<Story[]> => {
  const params: Record<string, any> = { limit };
  if (topic) params.topic = topic;
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

export const searchNews = async (query: string, limit = 20): Promise<SearchResult> => {
  const response = await API.get<SearchResult>('/api/search', {
    params: { q: query, limit },
  });
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
