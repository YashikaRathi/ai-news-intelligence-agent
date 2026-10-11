import React from 'react';
import { TimelineEvent } from '../types';
import { formatISTDateTime, formatRelativeTime, getTimestampTooltip } from '../utils/time';
import { Clock, ExternalLink, Activity } from 'lucide-react';

interface TimelineProps {
  events: TimelineEvent[];
}

export const Timeline: React.FC<TimelineProps> = ({ events }) => {
  if (!events || events.length === 0) {
    return (
      <div className="p-6 bg-[#F7FAFF] border border-[#E2E8F0] rounded-xl text-center text-xs text-[#64748B] font-medium">
        No coverage timeline available for this story yet.
      </div>
    );
  }

  // Sort events chronologically (latest first for visual prominence)
  const sortedEvents = [...events].sort((a, b) => {
    const timeA = a.published_at ? new Date(a.published_at).getTime() : 0;
    const timeB = b.published_at ? new Date(b.published_at).getTime() : 0;
    return timeB - timeA;
  });

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-[#2563EB]" />
          <h3 className="text-xl font-extrabold text-[#0F172A] tracking-tight">
            Story Chronology & Timeline
          </h3>
        </div>
        <span className="text-xs font-semibold text-[#2563EB] bg-[#EFF6FF] px-2.5 py-1 rounded-full border border-[#60A5FA]/30">
          {events.length} {events.length === 1 ? 'event' : 'events'} recorded
        </span>
      </div>

      <div className="relative pl-6 border-l-2 border-[#2563EB] space-y-6 pt-1">
        {sortedEvents.map((event, idx) => {
          const formattedRelative = formatRelativeTime(event.published_at);
          const tooltip = getTimestampTooltip(event.published_at, 'Published');
          const istExact = event.published_at ? formatISTDateTime(event.published_at) : 'Time unavailable';

          const isLatest = idx === 0;

          return (
            <div key={event.article_id || idx} className="relative group">
              {/* Blue Circular Bullet Node */}
              <div
                className={`absolute -left-[31px] top-3.5 w-4 h-4 rounded-full border-2 bg-white transition-all ${
                  isLatest ? 'border-[#2563EB] bg-[#2563EB] ring-4 ring-[#EFF6FF]' : 'border-[#60A5FA]'
                }`}
              />

              <div className="bg-white border border-[#E2E8F0] hover:border-[#60A5FA] rounded-xl p-4 space-y-2 shadow-sm transition-all">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#E2E8F0] pb-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-[#EFF6FF] text-[#2563EB] border border-[#60A5FA]/20">
                      {event.source_name}
                    </span>
                    {isLatest && (
                      <span className="px-2 py-0.5 text-[9px] font-extrabold rounded-full bg-[#16A34A] text-white uppercase tracking-wider">
                        Latest
                      </span>
                    )}
                  </div>

                  <span
                    className="text-xs text-[#64748B] font-semibold flex items-center gap-1 cursor-help"
                    title={tooltip}
                  >
                    <Clock className="w-3.5 h-3.5 text-[#2563EB]" />
                    <span>{istExact} &bull; {formattedRelative}</span>
                  </span>
                </div>

                <h4 className="text-sm font-bold text-[#0F172A] group-hover:text-[#2563EB] transition-colors leading-snug">
                  {event.title}
                </h4>

                <div className="pt-2 flex items-center justify-end">
                  <a
                    href={event.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-[#2563EB] hover:underline"
                  >
                    <span>Read Source</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};



