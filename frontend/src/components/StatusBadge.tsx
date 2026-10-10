import React from 'react';
import { Activity, Cpu } from 'lucide-react';

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

export const CredibilityBadge: React.FC<{ status?: string }> = ({ status }) => {
  switch (status) {
    case 'high_credibility':
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
          High Credibility
        </span>
      );
    case 'medium_credibility':
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
          Medium Credibility
        </span>
      );
    case 'low_credibility':
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
          Caution Advised
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-600 border border-slate-200">
          Unverified Publisher
        </span>
      );
  }
};

export const VerificationBadge: React.FC<{ status?: string }> = ({ status }) => {
  switch (status) {
    case 'verified_by_existing_fact_check':
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
          Existing Fact-Check Found
        </span>
      );
    case 'disputed_by_existing_fact_check':
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-100 text-rose-800 border border-rose-300">
          Disputed Claim
        </span>
      );
    case 'conflicting_reports':
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-100 text-amber-800 border border-amber-300">
          Conflicting Reports
        </span>
      );
    case 'unanimous_consensus':
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-100 text-blue-800 border border-blue-300">
          Unanimous Consensus
        </span>
      );
    case 'single_source_only':
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700 border border-slate-300">
          Single Source Reporting
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-50 text-slate-500 border border-slate-200">
          No Matching Fact-Check Found
        </span>
      );
  }
};
