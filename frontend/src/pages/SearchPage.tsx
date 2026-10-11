import React, { useState, useEffect } from 'react';
import { SearchResult, FreshnessOption } from '../types';
import { searchNews } from '../services/api';
import { SearchBar } from '../components/SearchBar';
import { StoryCard } from '../components/StoryCard';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { EmptyState } from '../components/EmptyState';
import { formatRelativeTime, getTimestampTooltip } from '../utils/time';
import { ExternalLink, Clock, ArrowUpDown } from 'lucide-react';


interface SearchPageProps {
  initialQuery?: string;
  onSelectStory: (storyId: string) => void;
}

export const SearchPage: React.FC<SearchPageProps> = ({ initialQuery = 'AI', onSelectStory }) => {
  const [query, setQuery] = useState(initialQuery);
  const [freshness, setFreshness] = useState<FreshnessOption>('all');
  const [sortBy, setSortBy] = useState<'relevance' | 'latest'>('relevance');
  const [result, setResult] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const freshnessOptions: { label: string; value: FreshnessOption }[] = [
    { label: 'All available news', value: 'all' },
    { label: 'Last hour', value: '1h' },
    { label: 'Last 6 hours', value: '6h' },
    { label: 'Last 24 hours', value: '24h' },
    { label: 'Last 7 days', value: '7d' },
  ];

  const executeSearch = async (
    qStr: string,
    fOpt: FreshnessOption = freshness,
    sOpt: 'relevance' | 'latest' = sortBy
  ) => {
    if (!qStr.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await searchNews(qStr.trim(), 20, fOpt, sOpt);
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Search request failed.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    executeSearch(query, freshness, sortBy);
  }, []);

  const handleSearchSubmit = (q: string) => {
    setQuery(q);
    executeSearch(q, freshness, sortBy);
  };

  const handleFreshnessChange = (newFreshness: FreshnessOption) => {
    setFreshness(newFreshness);
    executeSearch(query, newFreshness, sortBy);
  };

  const handleSortChange = (newSort: 'relevance' | 'latest') => {
    setSortBy(newSort);
    executeSearch(query, freshness, newSort);
  };

  return (
    <div className="space-y-8 pb-12 max-w-7xl mx-auto">
      {/* Search Header Banner */}
      <div className="bg-[#F7FAFF] border border-[#E2E8F0] rounded-2xl p-6 sm:p-8 space-y-5 shadow-sm">
        <div>
          <h2 className="text-2xl sm:text-3xl font-black text-[#0F172A] tracking-tight">
            Search News Intelligence
          </h2>
          <p className="text-xs sm:text-sm text-[#64748B] font-medium mt-1">
            Search topics, companies, people, or events across live news feeds with freshness filtering
          </p>
        </div>
        <div className="max-w-2xl">
          <SearchBar onSearch={handleSearchSubmit} initialQuery={query} />
        </div>

        {/* Filters and Sorting Controls Bar */}
        <div className="pt-2 border-t border-[#E2E8F0] flex flex-wrap items-center justify-between gap-4">
          {/* Freshness Filter */}
          <div className="flex flex-wrap items-center gap-2">
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

          {/* Sort Switcher */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-[#475569] flex items-center gap-1">
              <ArrowUpDown className="w-3.5 h-3.5 text-[#2563EB]" />
              <span>Sort:</span>
            </span>
            <div className="flex items-center bg-white p-1 rounded-xl border border-[#E2E8F0] text-xs font-semibold">
              <button
                onClick={() => handleSortChange('relevance')}
                className={`px-3 py-1 rounded-lg transition-all ${
                  sortBy === 'relevance'
                    ? 'bg-[#2563EB] text-white shadow-xs font-bold'
                    : 'text-[#64748B] hover:text-[#0F172A]'
                }`}
              >
                Relevance
              </button>
              <button
                onClick={() => handleSortChange('latest')}
                className={`px-3 py-1 rounded-lg transition-all ${
                  sortBy === 'latest'
                    ? 'bg-[#2563EB] text-white shadow-xs font-bold'
                    : 'text-[#64748B] hover:text-[#0F172A]'
                }`}
              >
                Newest first (Publication)
              </button>
            </div>
          </div>
        </div>
      </div>

      {loading ? (
        <LoadingSkeleton />
      ) : error ? (
        <EmptyState title="Search Failed" description={error} onRetry={() => executeSearch(query)} />
      ) : !result || (result.stories.length === 0 && result.articles.length === 0) ? (
        <EmptyState
          title={
            freshness !== 'all'
              ? `No news found in the '${freshnessOptions.find((o) => o.value === freshness)?.label}' window.`
              : 'No news found.'
          }
          description={
            freshness !== 'all'
              ? `No articles or stories matching "${query}" were published within this freshness timeframe. Try selecting 'All available news' or 'Last 24 hours'.`
              : `No records matched '${query}'. Try searching another query or topic.`
          }
          onRetry={() => {
            if (freshness !== 'all') {
              handleFreshnessChange('all');
            } else {
              executeSearch(query);
            }
          }}
        />
      ) : (
        <div className="space-y-10">
          {/* Search Result Count */}
          <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3 text-xs font-semibold text-[#64748B]">
            <div>
              Results for <span className="text-[#2563EB] font-bold">"{query}"</span>
            </div>
            <span className="bg-[#EFF6FF] text-[#2563EB] px-3 py-1 rounded-full border border-[#60A5FA]/30 font-bold">
              {result.stories.length} stories &bull; {result.articles.length} articles
            </span>
          </div>

          {/* Matching Stories */}
          {result.stories.length > 0 && (
            <section className="space-y-4">
              <h3 className="text-lg font-extrabold text-[#0F172A] tracking-tight">
                Matching Stories ({result.stories.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {result.stories.map((story) => (
                  <StoryCard key={story.id} story={story} onSelectStory={onSelectStory} />
                ))}
              </div>
            </section>
          )}

          {/* Matching Coverage Articles */}
          {result.articles.length > 0 && (
            <section className="space-y-4 pt-2">
              <h3 className="text-lg font-extrabold text-[#0F172A] tracking-tight">
                Individual Articles ({result.articles.length})
              </h3>
              <div className="bg-[#F7FAFF] border border-[#E2E8F0] rounded-2xl p-4 divide-y divide-[#E2E8F0]">
                {result.articles.map((art) => (
                  <article
                    key={art.id}
                    className="py-4 first:pt-1 last:pb-1 flex items-start justify-between gap-4 group"
                  >
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center gap-2 text-xs font-semibold text-[#64748B]">
                        <span className="text-[#2563EB] font-bold">
                          {art.source_name}
                        </span>
                        <span>&bull;</span>
                        <span
                          className="flex items-center gap-1 cursor-help"
                          title={getTimestampTooltip(art.published_at, 'Published')}
                        >
                          <Clock className="w-3 h-3 text-[#2563EB]" />
                          <span>{formatRelativeTime(art.published_at)}</span>
                        </span>
                      </div>
                      <a
                        href={art.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-base font-bold text-[#0F172A] group-hover:text-[#2563EB] transition-colors leading-snug block"
                      >
                        {art.title}
                      </a>
                      <p className="text-xs text-[#64748B] line-clamp-2 leading-relaxed">{art.description}</p>
                    </div>

                    {art.image_url ? (
                      <img
                        src={art.image_url}
                        alt={art.title}
                        className="w-24 h-16 object-cover rounded-xl border border-[#E2E8F0] shrink-0"
                        onError={(e) => {
                          (e.target as HTMLElement).style.display = 'none';
                        }}
                      />
                    ) : (
                      <a
                        href={art.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-2.5 rounded-lg bg-white border border-[#E2E8F0] text-[#2563EB] hover:bg-[#EFF6FF] shrink-0 transition-colors"
                        title="Read source"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    )}
                  </article>
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  );
};


