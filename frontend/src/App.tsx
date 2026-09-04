import { useEffect, useState } from 'react';
import { Header } from './components/Header';
import { DashboardPage } from './pages/DashboardPage';
import { SearchPage } from './pages/SearchPage';
import { StoryIntelligencePage } from './pages/StoryIntelligencePage';
import { StoryGrid } from './components/StoryGrid';
import { LoadingSkeleton } from './components/LoadingSkeleton';
import { EmptyState } from './components/EmptyState';
import { getHealth, getStories } from './services/api';
import { Story } from './types';
import { Sparkles, Layers } from 'lucide-react';

export function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'stories' | 'search' | 'intelligence' | 'topics'>('dashboard');
  const [selectedStoryId, setSelectedStoryId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('AI');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [apiStatus, setApiStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  const [stories, setStories] = useState<Story[]>([]);
  const [loadingStories, setLoadingStories] = useState<boolean>(false);

  // Health Check: Header status depends ONLY on GET /health 200 OK
  const checkHealth = async () => {
    try {
      const data = await getHealth();
      if (data && (data.status === 'ok' || data.status === 'healthy')) {
        setApiStatus('online');
      } else {
        setApiStatus('offline');
      }
    } catch {
      setApiStatus('offline');
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleSelectStory = (storyId: string) => {
    setSelectedStoryId(storyId);
    setActiveTab('intelligence');
  };

  const handleSearchTopic = (query: string) => {
    setSelectedCategory(query);
    setSearchQuery(query || 'AI');
    setActiveTab('search');
  };

  const loadStoriesPage = async () => {
    setLoadingStories(true);
    try {
      const data = await getStories();
      setStories(data);
    } catch {
      setStories([]);
    } finally {
      setLoadingStories(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'stories') {
      loadStoriesPage();
    }
  }, [activeTab]);

  return (
    <div className="min-h-screen bg-white text-[#0F172A] flex flex-col font-sans selection:bg-[#EFF6FF] selection:text-[#2563EB]">
      {/* Modern App Header */}
      <Header
        activeTab={activeTab}
        setActiveTab={(tab) => {
          setSelectedStoryId(null);
          setSelectedCategory('');
          setActiveTab(tab);
        }}
        apiStatus={apiStatus}
        isDemo={true}
        onCategorySelect={handleSearchTopic}
        selectedCategory={selectedCategory}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 bg-white">
        {activeTab === 'dashboard' && (
          <DashboardPage
            onSelectStory={handleSelectStory}
            onSearchTopic={handleSearchTopic}
            selectedCategory={selectedCategory}
          />
        )}

        {(activeTab === 'topics' || activeTab === 'stories') && (
          <div className="space-y-6 max-w-7xl mx-auto">
            <div className="flex items-center justify-between pb-4 border-b border-[#E2E8F0]">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Layers className="w-5 h-5 text-[#2563EB]" />
                  <h1 className="text-2xl font-black text-[#0F172A] tracking-tight">
                    {activeTab === 'topics' ? 'Explore News Topics' : 'All Clustered Stories'}
                  </h1>
                </div>
                <p className="text-xs text-[#64748B] font-medium">
                  Multi-source news stories automatically clustered, deduplicated, and analyzed
                </p>
              </div>
              <button
                onClick={loadStoriesPage}
                className="px-4 py-2 bg-[#2563EB] hover:bg-[#1D4ED8] text-white text-xs font-bold rounded-lg transition-colors shadow-sm"
              >
                Refresh Stories
              </button>
            </div>

            {loadingStories ? (
              <LoadingSkeleton />
            ) : stories.length === 0 ? (
              <EmptyState title="No stories available." onRetry={loadStoriesPage} />
            ) : (
              <StoryGrid stories={stories} onSelectStory={handleSelectStory} />
            )}
          </div>
        )}

        {activeTab === 'search' && (
          <SearchPage
            initialQuery={searchQuery}
            onSelectStory={handleSelectStory}
          />
        )}

        {activeTab === 'intelligence' && selectedStoryId && (
          <StoryIntelligencePage
            storyId={selectedStoryId}
            onBack={() => setActiveTab('dashboard')}
          />
        )}
      </main>

      {/* Modern App Footer */}
      <footer className="border-t border-[#E2E8F0] bg-[#F7FAFF] py-8 text-[#64748B] text-xs font-sans">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-[#2563EB] text-white flex items-center justify-center font-bold text-xs">
              <Sparkles className="w-3 h-3 fill-white text-white" />
            </div>
            <span className="font-extrabold text-[#0F172A] tracking-tight text-sm">
              NEWS<span className="text-[#2563EB]">INTEL</span>
            </span>
            <span className="text-[11px] text-[#64748B] font-medium">
              &bull; Modern AI News Intelligence Platform
            </span>
          </div>

          <div className="flex items-center gap-4 text-xs font-semibold text-[#64748B]">
            <span>Multi-source Grounding</span>
            <span>&bull;</span>
            <span>RAG Synthesis</span>
            <span>&bull;</span>
            <span>Deduplication</span>
            <span>&bull;</span>
            <span>Live Discovery</span>
          </div>
        </div>
      </footer>
    </div>
  );
}



