import React, { useEffect, useState } from 'react';
import { StoryIntelligence, StoryTimeline, Story } from '../types';
import { getStory, getStoryIntelligence, getTimeline } from '../services/api';
import { IntelligenceCard } from '../components/IntelligenceCard';
import { Timeline } from '../components/Timeline';
import { SourceComparison } from '../components/SourceComparison';
import { ChatBox } from '../components/ChatBox';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { EmptyState } from '../components/EmptyState';
import { VerificationPanel } from '../components/VerificationPanel';
import { ReaderReviews } from '../components/ReaderReviews';
import { formatRelativeTime, getTimestampTooltip } from '../utils/time';
import { ArrowLeft, Clock, Layers, ShieldCheck, Sparkles } from 'lucide-react';

interface StoryIntelligencePageProps {
  storyId: string;
  onBack: () => void;
}

export const StoryIntelligencePage: React.FC<StoryIntelligencePageProps> = ({ storyId, onBack }) => {
  const [story, setStory] = useState<Story | null>(null);
  const [intelligence, setIntelligence] = useState<StoryIntelligence | null>(null);
  const [timeline, setTimeline] = useState<StoryTimeline | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadStoryData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [storyData, intelData, timelineData] = await Promise.all([
        getStory(storyId),
        getStoryIntelligence(storyId),
        getTimeline(storyId),
      ]);
      setStory(storyData);
      setIntelligence(intelData);
      setTimeline(timelineData);
    } catch (err: any) {
      setError(err.message || 'Unable to load story intelligence details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStoryData();
  }, [storyId]);

  if (loading) {
    return (
      <div className="space-y-6 max-w-7xl mx-auto">
        <button onClick={onBack} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#F7FAFF] border border-[#E2E8F0] text-xs font-semibold text-[#2563EB] hover:bg-[#EFF6FF] transition-all">
          <ArrowLeft className="w-4 h-4" /> Back to Stories
        </button>
        <LoadingSkeleton />
      </div>
    );
  }

  if (error || !intelligence) {
    return (
      <div className="space-y-6 max-w-7xl mx-auto">
        <button onClick={onBack} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#F7FAFF] border border-[#E2E8F0] text-xs font-semibold text-[#2563EB] hover:bg-[#EFF6FF] transition-all">
          <ArrowLeft className="w-4 h-4" /> Back to Stories
        </button>
        <EmptyState title="Unable to load this story." description={error || 'Story intelligence unavailable.'} onRetry={loadStoryData} />
      </div>
    );
  }

  const evidenceCount = intelligence.evidence ? intelligence.evidence.length : 1;
  const sourcesCount = intelligence.sources ? intelligence.sources.length : 1;
  const heroImage = story?.articles?.find((a) => a.image_url)?.image_url;
  const pubTimestamp = story?.latest_published_at || story?.earliest_published_at;

  return (
    <div className="space-y-8 pb-16 max-w-7xl mx-auto">
      {/* Top Back Navigation Bar */}
      <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-4">
        <button
          onClick={onBack}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-[#F7FAFF] hover:bg-[#EFF6FF] border border-[#E2E8F0] text-xs font-bold text-[#2563EB] transition-all shadow-xs"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Stories</span>
        </button>

        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-[#EFF6FF] border border-[#60A5FA]/30 text-xs font-semibold text-[#2563EB]">
            <ShieldCheck className="w-4 h-4" /> Verified Evidence ({evidenceCount})
          </span>
        </div>
      </div>

      {/* Main Title & Metadata Header */}
      <article className="space-y-4">
        <div className="flex items-center gap-2">
          <span className="px-3 py-0.5 rounded-full text-xs font-extrabold uppercase tracking-wider bg-[#2563EB] text-white">
            {intelligence.topic || 'Special Report'}
          </span>
          <span className="text-[#64748B] text-xs font-semibold">&bull;</span>
          <span className="text-xs text-[#64748B] font-semibold uppercase tracking-wider">
            Story Intelligence Analysis
          </span>
        </div>

        <h1 className="text-3xl sm:text-5xl font-black text-[#0F172A] leading-tight tracking-tight">
          {intelligence.headline}
        </h1>

        <div className="flex flex-wrap items-center gap-4 text-xs font-semibold text-[#64748B] pt-2 border-t border-[#E2E8F0]">
          <span
            className="flex items-center gap-1 cursor-help"
            title={getTimestampTooltip(pubTimestamp, 'Updated')}
          >
            <Clock className="w-3.5 h-3.5 text-[#2563EB]" />
            <span>Updated {formatRelativeTime(pubTimestamp)}</span>
          </span>
          <span>&bull;</span>
          <span className="flex items-center gap-1">
            <Layers className="w-3.5 h-3.5 text-[#2563EB]" />
            {timeline ? timeline.total_articles : story?.article_count} Articles across {sourcesCount} Media Outlets
          </span>
        </div>
      </article>

      {/* Featured Hero Article Image */}
      {heroImage && (
        <div className="overflow-hidden rounded-2xl border border-[#E2E8F0] bg-[#F7FAFF] max-h-[460px] shadow-xs">
          <img
            src={heroImage}
            alt={intelligence.headline}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLElement).style.display = 'none';
            }}
          />
        </div>
      )}

      {/* THREE VISUALLY DISTINCT INTELLIGENCE BREAKDOWN CARDS */}
      <section className="space-y-4 pt-2">
        <div className="flex items-center gap-2 border-b border-[#E2E8F0] pb-3">
          <Sparkles className="w-5 h-5 text-[#2563EB]" />
          <h2 className="text-xl font-extrabold text-[#0F172A] tracking-tight">
            Story Intelligence Breakdown
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <IntelligenceCard
            type="happened"
            content={intelligence.what_happened}
            evidenceCount={evidenceCount}
          />

          <IntelligenceCard
            type="changed"
            content={intelligence.what_changed}
            evidenceCount={evidenceCount}
          />

          <IntelligenceCard
            type="matters"
            content={intelligence.why_it_matters}
            evidenceCount={evidenceCount}
          />
        </div>
      </section>

      {/* Main Content Layout: Left = Verification, Source Coverage, Reviews, Right = Ask the News */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 pt-4">
        {/* Left Column (8 cols): Credibility Panel, Source Comparison, Timeline, Reader Reviews */}
        <div className="lg:col-span-8 space-y-10">
          {/* 1. Clear Credibility & Fact-Check Verification Panel */}
          <VerificationPanel
            summary={intelligence.verification_summary}
            title="Credibility & Verification Analysis"
          />

          {/* 2. Source Comparison */}
          {intelligence.source_comparison && (
            <SourceComparison items={intelligence.source_comparison} />
          )}

          {/* 3. Coverage Timeline */}
          {timeline && <Timeline events={timeline.timeline} />}

          {/* 4. Reader Reviews & Ratings */}
          <ReaderReviews
            targetType="story"
            targetId={storyId}
            targetTitle={intelligence.headline}
          />
        </div>

        {/* Right Column (4 cols): Ask the News Research Assistant */}
        <div className="lg:col-span-4">
          <div className="sticky top-20">
            <ChatBox storyId={storyId} />
          </div>
        </div>
      </div>
    </div>
  );
};
