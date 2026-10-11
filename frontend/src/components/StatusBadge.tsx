import React from 'react';
import {
  Activity,
  Cpu,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  HelpCircle,
  ShieldCheck,
  Scale,
  MinusCircle,
  ShieldAlert,
} from 'lucide-react';

interface StatusBadgeProps {
  apiStatus: 'online' | 'offline' | 'checking';
  isDemo?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ apiStatus, isDemo = true }) => {
  return (
    <div className="flex items-center gap-2">
      {/* Backend Health Status */}
      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-stone-100 border border-stone-200 text-[11px] font-medium">
        <Activity className="w-3 h-3 text-stone-500" />
        <span className="text-stone-500">API:</span>
        {apiStatus === 'online' && (
          <span className="inline-flex items-center gap-1 text-emerald-700 font-semibold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span>
            Online
          </span>
        )}
        {apiStatus === 'offline' && (
          <span className="inline-flex items-center gap-1 text-red-700 font-semibold">
            <span className="w-1.5 h-1.5 rounded-full bg-red-600"></span>
            Offline
          </span>
        )}
        {apiStatus === 'checking' && (
          <span className="inline-flex items-center gap-1 text-amber-700 font-semibold">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-600 animate-ping"></span>
            Connecting...
          </span>
        )}
      </div>

      {/* Demo / Live Mode Indicator */}
      {isDemo && (
        <div className="hidden sm:flex items-center gap-1 px-2.5 py-1 rounded bg-stone-100 border border-stone-200 text-stone-700 text-[11px] font-semibold">
          <Cpu className="w-3 h-3 text-stone-500" />
          <span>LIVE PIPELINE</span>
        </div>
      )}
    </div>
  );
};

export const CredibilityBadge: React.FC<{ status?: string; assessmentStatus?: string }> = ({
  status,
  assessmentStatus,
}) => {
  if (assessmentStatus === 'not_assessed' || status === 'not_assessed' || status === 'unverified_publisher') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700 border border-slate-300">
        <HelpCircle className="w-3 h-3 text-slate-500" />
        <span>Publisher: Not assessed</span>
      </span>
    );
  }

  switch (status) {
    case 'high_credibility':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-300">
          <ShieldCheck className="w-3 h-3 text-emerald-600" />
          <span>High Credibility</span>
        </span>
      );
    case 'medium_credibility':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-50 text-blue-800 border border-blue-300">
          <ShieldCheck className="w-3 h-3 text-blue-600" />
          <span>Medium Credibility</span>
        </span>
      );
    case 'low_credibility':
    case 'caution_advised':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-50 text-amber-800 border border-amber-300">
          <ShieldAlert className="w-3 h-3 text-amber-600" />
          <span>Caution Advised</span>
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700 border border-slate-300">
          <HelpCircle className="w-3 h-3 text-slate-500" />
          <span>Publisher: Not assessed</span>
        </span>
      );
  }
};

export const VerificationBadge: React.FC<{ status?: string; size?: 'sm' | 'md' }> = ({
  status = 'Not checked',
  size = 'sm',
}) => {
  const norm = (status || '').toLowerCase().trim();
  const textClass = size === 'md' ? 'text-xs px-2.5 py-1' : 'text-[10px] px-2 py-0.5';
  const iconClass = size === 'md' ? 'w-3.5 h-3.5' : 'w-3 h-3';

  if (norm.includes('true') && !norm.includes('partially') && !norm.includes('mixed')) {
    return (
      <span className={`inline-flex items-center gap-1 rounded font-bold bg-emerald-50 text-emerald-800 border border-emerald-300 ${textClass}`}>
        <CheckCircle2 className={`${iconClass} text-emerald-600`} />
        <span>Fact-check rated TRUE</span>
      </span>
    );
  }

  if (norm.includes('false')) {
    return (
      <span className={`inline-flex items-center gap-1 rounded font-bold bg-rose-50 text-rose-800 border border-rose-300 ${textClass}`}>
        <XCircle className={`${iconClass} text-rose-600`} />
        <span>Fact-check rated FALSE</span>
      </span>
    );
  }

  if (norm.includes('mixed') || norm.includes('partially')) {
    return (
      <span className={`inline-flex items-center gap-1 rounded font-bold bg-amber-50 text-amber-800 border border-amber-300 ${textClass}`}>
        <Scale className={`${iconClass} text-amber-600`} />
        <span>Mixed or partially true</span>
      </span>
    );
  }

  if (norm.includes('conflicting')) {
    return (
      <span className={`inline-flex items-center gap-1 rounded font-bold bg-orange-50 text-orange-800 border border-orange-300 ${textClass}`}>
        <AlertTriangle className={`${iconClass} text-orange-600`} />
        <span>Conflicting reports</span>
      </span>
    );
  }

  if (norm.includes('unanimous') || norm.includes('consensus')) {
    return (
      <span className={`inline-flex items-center gap-1 rounded font-bold bg-blue-50 text-blue-800 border border-blue-300 ${textClass}`}>
        <CheckCircle2 className={`${iconClass} text-blue-600`} />
        <span>Unanimous consensus</span>
      </span>
    );
  }

  if (norm.includes('insufficient') || norm.includes('single')) {
    return (
      <span className={`inline-flex items-center gap-1 rounded font-bold bg-stone-100 text-stone-700 border border-stone-300 ${textClass}`}>
        <HelpCircle className={`${iconClass} text-stone-500`} />
        <span>Insufficient evidence</span>
      </span>
    );
  }

  if (norm.includes('no matching') || norm === 'unknown') {
    return (
      <span className={`inline-flex items-center gap-1 rounded font-medium bg-slate-50 text-slate-700 border border-slate-300 ${textClass}`}>
        <MinusCircle className={`${iconClass} text-slate-500`} />
        <span>No matching fact-check found</span>
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center gap-1 rounded font-medium bg-slate-50 text-slate-600 border border-slate-200 ${textClass}`}>
      <HelpCircle className={`${iconClass} text-slate-400`} />
      <span>Not checked</span>
    </span>
  );
};
