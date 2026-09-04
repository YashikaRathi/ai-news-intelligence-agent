import React from 'react';
import { SourceComparisonItem } from '../types';
import { ExternalLink, Bookmark, AlertCircle, CheckCircle2, Globe } from 'lucide-react';

interface SourceComparisonProps {
  items: SourceComparisonItem[];
}

export const SourceComparison: React.FC<SourceComparisonProps> = ({ items }) => {
  if (!items || items.length === 0) {
    return (
      <div className="p-6 bg-[#F7FAFF] border border-[#E2E8F0] rounded-xl text-center text-xs text-[#64748B] font-medium">
        No multi-source comparison available for this story.
      </div>
    );
  }

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
        <div className="flex items-center gap-2">
          <Globe className="w-5 h-5 text-[#2563EB]" />
          <h3 className="text-xl font-extrabold text-[#0F172A] tracking-tight">
            Source Coverage
          </h3>
        </div>
        <span className="text-xs font-semibold text-[#2563EB] bg-[#EFF6FF] px-2.5 py-1 rounded-full border border-[#60A5FA]/30">
          {items.length} {items.length === 1 ? 'outlet' : 'outlets'} analyzed
        </span>
      </div>

      <div className="space-y-4">
        {items.map((item, idx) => (
          <div
            key={idx}
            className="bg-white border border-[#E2E8F0] hover:border-[#60A5FA] rounded-xl p-5 space-y-3 shadow-sm transition-all"
          >
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#E2E8F0] pb-2.5">
              <span className="px-2.5 py-0.5 rounded-md text-xs font-bold bg-[#EFF6FF] text-[#2563EB] border border-[#60A5FA]/30 uppercase tracking-wider">
                {item.source_name}
              </span>
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#F7FAFF] hover:bg-[#EFF6FF] border border-[#E2E8F0] text-xs font-bold text-[#2563EB] transition-colors"
              >
                <span>Read Original Article</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>

            <h4 className="text-base font-bold text-[#0F172A] leading-snug">
              "{item.headline}"
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs pt-1">
              <div className="bg-[#F7FAFF] p-3 rounded-lg border border-[#E2E8F0]">
                <span className="flex items-center gap-1 text-[#0F172A] font-bold mb-1 text-[11px] uppercase tracking-wider">
                  <Bookmark className="w-3.5 h-3.5 text-[#2563EB]" /> Emphasis:
                </span>
                <p className="text-[#64748B] leading-relaxed text-[11px] font-medium">{item.emphasis}</p>
              </div>

              <div className="bg-[#F7FAFF] p-3 rounded-lg border border-[#E2E8F0]">
                <span className="flex items-center gap-1 text-[#0F172A] font-bold mb-1 text-[11px] uppercase tracking-wider">
                  <AlertCircle className="w-3.5 h-3.5 text-purple-600" /> Unique Angle:
                </span>
                <p className="text-[#64748B] leading-relaxed text-[11px] font-medium">{item.differences}</p>
              </div>

              <div className="bg-[#F7FAFF] p-3 rounded-lg border border-[#E2E8F0]">
                <span className="flex items-center gap-1 text-[#0F172A] font-bold mb-1 text-[11px] uppercase tracking-wider">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Fact Agreement:
                </span>
                <p className="text-[#64748B] leading-relaxed text-[11px] font-medium">{item.agreement}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};



