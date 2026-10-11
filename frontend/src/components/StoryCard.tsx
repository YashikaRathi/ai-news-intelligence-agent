import React from 'react';
import { Story } from '../types';
import { formatRelativeTime, getTimestampTooltip } from '../utils/time';
import { VerificationBadge } from './StatusBadge';
import { Clock, ArrowRight, Layers } from 'lucide-react';

interface StoryCardProps {
  story: Story;
  onSelectStory: (storyId: string) => void;
}

export const StoryCard: React.FC<StoryCardProps> = ({ story, onSelectStory }) => {
  const sourcesCount = story.articles
    ? new Set(story.articles.map((a) => a.source_name)).size
    : story.article_count || 1;

  const firstImage = story.articles?.find((a) => a.image_url)?.image_url;

  const pubTimestamp = story.latest_published_at || story.earliest_published_at;
  const formattedRelative = formatRelativeTime(pubTimestamp);
  const tooltipText = getTimestampTooltip(pubTimestamp, 'Updated');

  const verificationStatus =
    story.overall_verification_status ||
    story.fact_check_status ||
    story.discrepancy_status ||
    'Not checked';

  return (
    <article
      onClick={() => onSelectStory(story.id)}
      className="bg-white border border-[#E2E8F0] hover:border-[#60A5FA] rounded-xl p-4 flex flex-col justify-between group cursor-pointer shadow-xs hover:shadow-md transition-all space-y-4"
    >
      <div className="space-y-3">
        {/* Optional Thumbnail Image */}
        {firstImage && (
          <div className="overflow-hidden bg-[#F7FAFF] rounded-lg aspect-[16/9] border border-[#E2E8F0]">
            <img
              src={firstImage}
              alt={story.title}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              onError={(e) => {
                (e.target as HTMLElement).style.display = 'none';
              }}
            />
          </div>
        )}

        {/* Category Badge & Verification Status */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[#EFF6FF] text-[#2563EB] border border-[#60A5FA]/20">
            {story.topic || story.category || 'General'}
          </span>
          <VerificationBadge status={verificationStatus} size="sm" />
        </div>

        {/* Modern Headline */}
        <h3 className="font-extrabold text-base sm:text-lg text-[#0F172A] group-hover:text-[#2563EB] transition-colors leading-snug line-clamp-2">
          {story.title}
        </h3>

        {/* Summary Snippet */}
        <p className="text-xs text-[#64748B] line-clamp-2 leading-relaxed font-normal">
          {story.summary || 'Cluster of multi-source coverage tracking this story event.'}
        </p>
      </div>

      {/* Footer Meta & Action */}
      <div className="pt-3 border-t border-[#E2E8F0] flex items-center justify-between text-xs text-[#64748B]">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 font-semibold text-[11px] text-[#64748B]">
            <Layers className="w-3.5 h-3.5 text-[#2563EB]" />
            <span>{sourcesCount} {sourcesCount === 1 ? 'source' : 'sources'}</span>
          </div>

          <div
            className="flex items-center gap-1 text-[11px] text-[#64748B] font-medium"
            title={tooltipText}
          >
            <Clock className="w-3 h-3 text-[#64748B]" />
            <span>{formattedRelative}</span>
          </div>
        </div>

        <span className="inline-flex items-center gap-1 text-xs font-bold text-[#2563EB] group-hover:translate-x-0.5 transition-transform">
          <span>Read Story</span>
          <ArrowRight className="w-3.5 h-3.5 text-[#2563EB]" />
        </span>
      </div>
    </article>
  );
};
