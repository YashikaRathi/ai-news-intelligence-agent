import React from 'react';
import { LucideIcon, FileText, Zap, HelpCircle } from 'lucide-react';

interface IntelligenceCardProps {
  type: 'happened' | 'changed' | 'matters';
  content: string;
  evidenceCount: number;
}

export const IntelligenceCard: React.FC<IntelligenceCardProps> = ({
  type,
  content,
  evidenceCount,
}) => {
  const config = {
    happened: {
      title: 'WHAT HAPPENED',
      subtitle: 'Factual Synthesis',
      icon: FileText,
      badgeBg: 'bg-[#EFF6FF]',
      badgeText: 'text-[#2563EB]',
      borderAccent: 'border-[#2563EB]',
    },
    changed: {
      title: 'WHAT CHANGED',
      subtitle: 'Newest Development vs History',
      icon: Zap,
      badgeBg: 'bg-purple-50',
      badgeText: 'text-purple-600',
      borderAccent: 'border-purple-500',
    },
    matters: {
      title: 'WHY IT MATTERS',
      subtitle: 'Significance & Impact',
      icon: HelpCircle,
      badgeBg: 'bg-amber-50',
      badgeText: 'text-amber-700',
      borderAccent: 'border-amber-500',
    },
  }[type];

  const Icon: LucideIcon = config.icon;

  return (
    <div className={`bg-[#F7FAFF] border border-[#E2E8F0] border-t-4 ${config.borderAccent} rounded-xl p-5 flex flex-col justify-between shadow-sm space-y-3`}>
      <div>
        {/* Card Header */}
        <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3 mb-3">
          <div className="flex items-center gap-2">
            <div className={`p-1.5 rounded-lg ${config.badgeBg} ${config.badgeText}`}>
              <Icon className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-extrabold text-xs text-[#0F172A] tracking-wide uppercase">{config.title}</h3>
              <p className="text-[10px] text-[#64748B] font-medium">{config.subtitle}</p>
            </div>
          </div>

          <span className="text-[10px] font-bold text-[#2563EB] bg-[#EFF6FF] px-2 py-0.5 rounded-full border border-[#60A5FA]/30">
            {evidenceCount} {evidenceCount === 1 ? 'source' : 'sources'}
          </span>
        </div>

        {/* Content Paragraph */}
        <p className="text-xs sm:text-sm text-[#0F172A] leading-relaxed font-normal">{content}</p>
      </div>
    </div>
  );
};



