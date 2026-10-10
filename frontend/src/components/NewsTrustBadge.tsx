import React from 'react';
import { ShieldCheck, ShieldAlert, Shield } from 'lucide-react';
import { TrustScore } from '../types';

interface NewsTrustBadgeProps {
  trustScore?: TrustScore;
  score?: number;
  label?: string;
  className?: string;
}

export const NewsTrustBadge: React.FC<NewsTrustBadgeProps> = ({
  trustScore,
  score: rawScore,
  label: rawLabel,
  className = '',
}) => {
  const score = trustScore ? trustScore.score : rawScore ?? 85;
  const label = trustScore ? trustScore.label : rawLabel ?? 'Verified Multi-Source';

  let colorClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  let Icon = ShieldCheck;

  if (score >= 80) {
    colorClasses = 'bg-[#EFF6FF] text-[#2563EB] border-[#60A5FA]/30';
    Icon = ShieldCheck;
  } else if (score >= 65) {
    colorClasses = 'bg-amber-50 text-amber-700 border-amber-200';
    Icon = Shield;
  } else {
    colorClasses = 'bg-slate-100 text-slate-700 border-slate-200';
    Icon = ShieldAlert;
  }

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-bold transition-all shadow-sm ${colorClasses} ${className}`}
      title={`NewsTrust Authenticity Score: ${score}/100`}
    >
      <Icon className="w-4 h-4" />
      <span>{label}</span>
      <span className="ml-1 px-1.5 py-0.5 rounded bg-white/80 text-[10px] font-black border border-current">
        {score}/100
      </span>
    </div>
  );
};
