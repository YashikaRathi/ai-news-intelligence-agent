import React, { useEffect, useState } from 'react';
import { Story, Article, FreshnessOption } from '../types';
import { getStories, getNews } from '../services/api';
import { StoryCard } from '../components/StoryCard';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { EmptyState } from '../components/EmptyState';
import { VerificationBadge } from '../components/StatusBadge';
import { formatRelativeTime, getTimestampTooltip } from '../utils/time';
import { ArrowRight, Search, Sparkles, Layers, Clock } from 'lucide-react';


interface DashboardPageProps {
  onSelectStory: (storyId: string) => void;
  onSearchTopic: (query: string) => void;
  selectedCategory?: string;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onSelectStory, onSearchTopic, selectedCategory = '' }) => {
  const [stories, setStories] = useState<Story[]>([]);
  const [liveArticles, setLiveArticles] = useState<Article[]>([]);
  const [activeSort, setActiveSort] = useState<'latest' | 'popular' | 'top'>('latest');
  const [freshness, setFreshness] = useState<FreshnessOption>('all');
  const [searchInputValue, setSearchInputValue] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const topics = [
    { label: 'Artificial Intelligence', topic: 'artificial intelligence' },
    { label: 'Technology', topic: 'technology' },
    { label: 'India', topic: 'India' },
    { label: 'World', topic: 'world' },
    { label: 'Business', topic: 'business' },
    { label: 'Science', topic: 'science' },
    { label: 'Climate', topic: 'climate' },
  ];

  const freshnessOptions: { label: string; value: FreshnessOption }[] = [
    { label: 'All available news', value: 'all' },
    { label: 'Last hour', value: '1h' },
    { label: 'Last 6 hours', value: '6h' },
    { label: 'Last 24 hours', value: '24h' },
    { label: 'Last 7 days', value: '7d' },
  ];

  const loadData = async (
    topic?: string,
    sortMode: 'latest' | 'popular' | 'top' = activeSort,
    freshnessFilter: FreshnessOption = freshness
  ) => {
    setLoading(true);
    setError(null);

    const activeTopic = topic !== undefined ? topic : selectedCategory;

    try {
      const storiesData = await getStories(activeTopic, 25, freshnessFilter, 'latest');
      setStories(storiesData);
    } catch (dbErr: any) {
      console.warn('SQLite story fetch warning:', dbErr);
    } finally {
      setLoading(false);
    }

    try {
      const articlesData = await getNews(activeTopic || 'artificial intelligence', 25, sortMode, freshnessFilter);
      if (articlesData && articlesData.length > 0) {
        setLiveArticles(articlesData);
        const updatedStories = await getStories(activeTopic, 25, freshnessFilter, 'latest');
        setStories(updatedStories);
      } else {
        setLiveArticles([]);
      }
    } catch (ingestErr: any) {
      console.warn('News ingestion fetch warning:', ingestErr);
    }
  };

  useEffect(() => {
    loadData(selectedCategory, activeSort, freshness);
  }, [selectedCategory]);

  const handleSortChange = (newSort: 'latest' | 'popular' | 'top') => {
    setActiveSort(newSort);
    loadData(selectedCategory, newSort, freshness);
  };

  const handleFreshnessChange = (newFreshness: FreshnessOption) => {
    setFreshness(newFreshness);
    loadData(selectedCategory, activeSort, newFreshness);
  };

  const handleSearchFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInputValue.trim()) {
      onSearchTopic(searchInputValue.trim());
    }
  };

  const heroStory = stories.length > 0 ? stories[0] : null;
  const secondaryStories = stories.slice(1, 4);
  const remainingStories = stories.slice(4);
  const heroImage = heroStory?.articles?.find((a) => a.image_url)?.image_url;

  return (
    <div className="space-y-10 pb-16 max-w-7xl mx-auto">
      {/* 1. HOMEPAGE GREETING & LARGE SEARCH BAR */}
      <section className="bg-gradient-to-b from-[#F7FAFF] to-white border border-[#E2E8F0] rounded-2xl p-6 sm:p-10 shadow-sm text-center space-y-6">
        <div className="max-w-2xl mx-auto space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#EFF6FF] text-[#2563EB] text-xs font-semibold border border-[#60A5FA]/30">
            <Sparkles className="w-3.5 h-3.5 fill-[#2563EB]" />
            <span>AI-Powered News Intelligence</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-black text-[#0F172A] tracking-tight">
            Good morning 👋
          </h1>
          <p className="text-sm sm:text-base text-[#64748B] font-medium">
            Understand what's happening in the world with multi-source intelligence.
          </p>
        </div>

        {/* Large Prominent Search Bar */}
        <form onSubmit={handleSearchFormSubmit} className="max-w-2xl mx-auto relative flex items-center">
          <Search className="w-5 h-5 text-[#2563EB] absolute left-4 pointer-events-none" />
          <input
            type="text"
            value={searchInputValue}
            onChange={(e) => setSearchInputValue(e.target.value)}
            placeholder="Search any topic, person, company or event..."
            className="w-full pl-12 pr-28 py-3.5 bg-white border border-[#E2E8F0] rounded-xl text-sm text-[#0F172A] placeholder-[#64748B] shadow-sm focus:outline-none focus:border-[#2563EB] focus:ring-2 focus:ring-[#60A5FA]/20 transition-all font-medium"
          />
          <button
            type="submit"
            className="absolute right-2 px-4 py-2 bg-[#2563EB] hover:bg-[#1D4ED8] text-white text-xs font-bold rounded-lg transition-colors flex items-center gap-1 shadow-sm"
          >
            <span>Search</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </form>

        {/* 2. EXPLORE TOPICS CHIPS */}
        <div className="pt-2">
          <span className="text-[11px] font-bold text-[#64748B] uppercase tracking-wider block mb-3">
            Explore Topics
          </span>
          <div className="flex flex-wrap items-center justify-center gap-2">
            {topics.map((t, idx) => {
              const isActive = selectedCategory.toLowerCase() === t.topic.toLowerCase();
              return (
                <button
                  key={idx}
                  onClick={() => onSearchTopic(t.topic)}
                  className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all border ${
                    isActive
                      ? 'bg-[#2563EB] text-white border-[#2563EB] shadow-sm'
                      : 'bg-white text-[#0F172A] border-[#E2E8F0] hover:border-[#60A5FA] hover:text-[#2563EB] hover:bg-[#EFF6FF]'
                  }`}
                >
                  {t.label}
                </button>
              );
            })}
          </div>
        </div>
      </section>

      {/* 3. FRESHNESS & FEED CONTROLS BAR */}
      <div className="space-y-3 border-b border-[#E2E8F0] pb-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-[#2563EB]" />
            <h2 className="text-xl font-extrabold text-[#0F172A] tracking-tight">
              Today's Intelligence
            </h2>
            <span className="text-[11px] font-semibold text-[#64748B] bg-[#F1F5F9] px-2.5 py-0.5 rounded-full">
              Publication time: Newest first
            </span>
          </div>

          {/* Sort Switcher */}
          <div className="flex items-center bg-[#F7FAFF] p-1 rounded-xl border border-[#E2E8F0] text-xs font-semibold text-[#0F172A]">
            <button
              onClick={() => handleSortChange('latest')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                activeSort === 'latest' ? 'bg-white text-[#2563EB] shadow-sm font-bold' : 'text-[#64748B] hover:text-[#0F172A]'
              }`}
            >
              Latest
            </button>
            <button
              onClick={() => handleSortChange('popular')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                activeSort === 'popular' ? 'bg-white text-[#2563EB] shadow-sm font-bold' : 'text-[#64748B] hover:text-[#0F172A]'
              }`}
            >
              Popular
            </button>
            <button
              onClick={() => handleSortChange('top')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                activeSort === 'top' ? 'bg-white text-[#2563EB] shadow-sm font-bold' : 'text-[#64748B] hover:text-[#0F172A]'
              }`}
            >
              Top Headlines
            </button>
          </div>
        </div>

        {/* Freshness Filter Chips */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <div className="flex items-center gap-1.5 text-xs font-bold text-[#475569] mr-1">
            <Clock className="w-3.5 h-3.5 text-[#2563EB]" />
            <span>Freshness:</span>
          </div>
          {freshnessOptions.map((opt) => {
            const isSelected = freshness === opt.value;
            return (
              <button
                key={opt.value}
                onClick={() => handleFreshnessChange(opt.value)}
                className={`px-3 py-1 rounded-full text-xs font-semibold transition-all border ${
                  isSelected
                    ? 'bg-[#2563EB] text-white border-[#2563EB] shadow-xs'
                    : 'bg-white text-[#475569] border-[#E2E8F0] hover:border-[#93C5FD] hover:text-[#2563EB]'
                }`}
              >
                {opt.label}
              </button>
            );
          })}
        </div>
      </div>

      {loading ? (
        <LoadingSkeleton />
      ) : error ? (
        <EmptyState title="Unable to load story intelligence" description={error} onRetry={() => loadData()} />
      ) : stories.length === 0 ? (
        <EmptyState
          title={
            freshness !== 'all'
              ? `No stories published in the selected freshness window (${freshnessOptions.find((o) => o.value === freshness)?.label})`
              : 'No stories available.'
          }
          description={
            freshness !== 'all'
              ? "We checked original publication timestamps, and no articles were published within this timeframe. Try selecting 'Last 24 hours' or 'All available news' to view earlier coverage."
              : 'No news stories have been clustered yet. Try another topic or search.'
          }
          onRetry={() => {
            if (freshness !== 'all') {
              handleFreshnessChange('all');
            } else {
              loadData();
            }
          }}
        />
      ) : (
        <>
          {/* 4. HERO FEATURED STORY CARD */}
          {heroStory && (
            <section className="bg-white border border-[#E2E8F0] rounded-2xl overflow-hidden shadow-sm hover:shadow-md transition-shadow group cursor-pointer" onClick={() => onSelectStory(heroStory.id)}>
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-0 items-stretch">
                {/* Image (Left 7 Cols) */}
                <div className="lg:col-span-7 bg-[#F7FAFF] overflow-hidden aspect-[16/10] relative">
                  {heroImage ? (
                    <img
                      src={heroImage}
                      alt={heroStory.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      onError={(e) => {
                        (e.target as HTMLElement).style.display = 'none';
                      }}
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-[#64748B] bg-[#F7FAFF] font-medium text-sm">
                      News Intel Intelligence Coverage
                    </div>
                  )}
                </div>

                {/* Hero Info (Right 5 Cols) */}
                <div className="lg:col-span-5 p-6 sm:p-8 flex flex-col justify-between space-y-6">
                  <div className="space-y-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#EFF6FF] text-[#2563EB] uppercase tracking-wider border border-[#60A5FA]/20">
                          {heroStory.topic || heroStory.category || 'Technology'}
                        </span>
                        <span className="text-xs text-[#64748B] font-semibold">
                          {heroStory.article_count} {heroStory.article_count === 1 ? 'source' : 'sources'}
                        </span>
                      </div>
                      <VerificationBadge
                        status={
                          heroStory.overall_verification_status ||
                          heroStory.fact_check_status ||
                          heroStory.discrepancy_status
                        }
                        size="sm"
                      />
                    </div>

                    <h3 className="text-2xl sm:text-3xl font-extrabold text-[#0F172A] leading-tight group-hover:text-[#2563EB] transition-colors">
                      {heroStory.title}
                    </h3>

                    <p className="text-sm text-[#64748B] leading-relaxed line-clamp-3">
                      {heroStory.summary || 'Clustered intelligence tracking this development across global news outlets.'}
                    </p>
                  </div>

                  <div className="pt-4 border-t border-[#E2E8F0] flex items-center justify-between">
                    <span
                      className="text-xs text-[#64748B] font-semibold cursor-help"
                      title={getTimestampTooltip(heroStory.latest_published_at, 'Updated')}
                    >
                      Updated {formatRelativeTime(heroStory.latest_published_at)}
                    </span>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectStory(heroStory.id);
                      }}
                      className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#2563EB] hover:bg-[#1D4ED8] text-white text-xs font-bold rounded-lg transition-colors shadow-sm"
                    >
                      <span>View Intelligence</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* 5. MULTI-COLUMN SECTION: Secondary Stories & Live Developments Feed */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 pt-4">
            
            {/* Left 7 Cols: Secondary Lead Stories Grid */}
            <div className="lg:col-span-7 space-y-6">
              <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-2">
                <h3 className="text-base font-extrabold text-[#0F172A] tracking-tight">
                  Featured Intelligence Stories
                </h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {secondaryStories.map((story) => (
                  <StoryCard key={story.id} story={story} onSelectStory={onSelectStory} />
                ))}
              </div>
            </div>

            {/* Right 5 Cols: Latest Developments Live Feed */}
            <div className="lg:col-span-5 space-y-6">
              <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-2">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-[#16A34A] animate-pulse"></span>
                  <h3 className="text-base font-extrabold text-[#0F172A] tracking-tight">
                    Latest Developments
                  </h3>
                </div>
                <span className="text-xs text-[#64748B] font-medium">Real-time Feed</span>
              </div>

              {liveArticles.length === 0 ? (
                <div className="bg-[#F7FAFF] border border-[#E2E8F0] rounded-2xl p-6 text-center space-y-2">
                  <Clock className="w-8 h-8 text-[#94A3B8] mx-auto mb-1" />
                  <p className="text-xs font-bold text-[#0F172A]">No articles found in freshness window</p>
                  <p className="text-[11px] text-[#64748B] leading-relaxed">
                    No articles were published within {freshnessOptions.find((o) => o.value === freshness)?.label.toLowerCase()}.
                  </p>
                  {freshness !== 'all' && (
                    <button
                      onClick={() => handleFreshnessChange('all')}
                      className="text-xs font-semibold text-[#2563EB] hover:underline pt-1 inline-block"
                    >
                      Show all available news
                    </button>
                  )}
                </div>
              ) : (
                <div className="bg-[#F7FAFF] border border-[#E2E8F0] rounded-2xl p-4 divide-y divide-[#E2E8F0]">
                  {liveArticles.slice(0, 6).map((art, idx) => {
                    const pubTime = formatRelativeTime(art.published_at);
                    const tooltip = getTimestampTooltip(art.published_at, 'Published');

                    return (
                      <div key={idx} className="py-3.5 first:pt-1 last:pb-1 flex items-start justify-between gap-3 group">
                        <div className="flex-1 space-y-1">
                          <div className="flex items-center gap-2 text-xs font-semibold text-[#64748B]">
                            <span className="text-[#2563EB] font-bold">{art.source_name}</span>
                            <span>&bull;</span>
                            <span title={tooltip} className="cursor-help">{pubTime}</span>
                          </div>
                          <a
                            href={art.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm font-bold text-[#0F172A] group-hover:text-[#2563EB] transition-colors leading-snug block line-clamp-2"
                          >
                            {art.title}
                          </a>
                        </div>

                        {art.image_url && (
                          <img
                            src={art.image_url}
                            alt={art.title}
                            className="w-16 h-14 object-cover rounded-lg border border-[#E2E8F0] shrink-0"
                            onError={(e) => {
                              (e.target as HTMLElement).style.display = 'none';
                            }}
                          />
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* 6. ALL STORIES GRID CATALOG */}
          {remainingStories.length > 0 && (
            <section className="pt-6 space-y-6">
              <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
                <div>
                  <h3 className="text-xl font-extrabold text-[#0F172A] tracking-tight">
                    All Clustered Intelligence
                  </h3>
                  <p className="text-xs text-[#64748B] font-medium mt-0.5">
                    Browse all verified multi-source news clusters
                  </p>
                </div>
                <span className="text-xs font-semibold text-[#2563EB] bg-[#EFF6FF] px-3 py-1 rounded-full border border-[#60A5FA]/30">
                  {remainingStories.length} stories
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {remainingStories.map((s) => (
                  <StoryCard key={s.id} story={s} onSelectStory={onSelectStory} />
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
};




