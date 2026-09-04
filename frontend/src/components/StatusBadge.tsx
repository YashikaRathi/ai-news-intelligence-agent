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

