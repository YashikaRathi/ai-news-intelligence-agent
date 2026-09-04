import React, { useState, useEffect } from 'react';
import { SearchResult } from '../types';
import { searchNews } from '../services/api';
import { SearchBar } from '../components/SearchBar';
import { StoryCard } from '../components/StoryCard';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { EmptyState } from '../components/EmptyState';
import { ExternalLink, Clock } from 'lucide-react';


interface SearchPageProps {
  initialQuery?: string;
  onSelectStory: (storyId: string) => void;
}

export const SearchPage: React.FC<SearchPageProps> = ({ initialQuery = 'AI', onSelectStory }) => {
  const [query, setQuery] = useState(initialQuery);
  const [result, setResult] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const executeSearch = async (qStr: string) => {
    if (!qStr.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await searchNews(qStr.trim());
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Search request failed.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    executeSearch(query);
  }, []);

  const handleSearchSubmit = (q: string) => {
    setQuery(q);
    executeSearch(q);
  };

  return (
    <div className="space-y-8 pb-12 max-w-7xl mx-auto">
      {/* Search Header Banner */}
      <div className="bg-[#F7FAFF] border border-[#E2E8F0] rounded-2xl p-6 sm:p-8 space-y-4 shadow-sm">
        <div>
          <h2 className="text-2xl sm:text-3xl font-black text-[#0F172A] tracking-tight">
            Search News Intelligence
          </h2>
          <p className="text-xs sm:text-sm text-[#64748B] font-medium mt-1">
            Search topics, companies, people, or events across live news feeds
          </p>
        </div>
        <div className="max-w-2xl">
          <SearchBar onSearch={handleSearchSubmit} initialQuery={query} />
        </div>
      </div>

      {loading ? (
        <LoadingSkeleton />
      ) : error ? (
        <EmptyState title="Search Failed" description={error} onRetry={() => executeSearch(query)} />
      ) : !result || (result.stories.length === 0 && result.articles.length === 0) ? (
        <EmptyState title="No news found." description={`No records matched '${query}'. Try searching another query.`} />
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
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-[#2563EB]" />
                          {art.published_at ? new Date(art.published_at).toLocaleDateString() : 'Recent'}
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


