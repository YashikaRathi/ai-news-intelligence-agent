import React from 'react';
import { Search, Sparkles } from 'lucide-react';

interface HeaderProps {
  activeTab: 'dashboard' | 'stories' | 'search' | 'intelligence' | 'topics';
  setActiveTab: (tab: 'dashboard' | 'stories' | 'search' | 'topics') => void;
  apiStatus: 'online' | 'offline' | 'checking';
  isDemo?: boolean;
  onCategorySelect?: (category: string) => void;
  selectedCategory?: string;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  apiStatus,
  onCategorySelect,
  selectedCategory = '',
}) => {
  const navItems = [
    { label: 'Home', tab: 'dashboard' as const },
    { label: 'Latest', tab: 'dashboard' as const },
    { label: 'Topics', tab: 'topics' as const },
    { label: 'Stories', tab: 'stories' as const },
  ];

  return (
    <header className="bg-white border-b border-[#E2E8F0] sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Left: Brand Logo */}
        <div className="flex items-center gap-8">
          <div
            onClick={() => {
              if (onCategorySelect) onCategorySelect('');
              setActiveTab('dashboard');
            }}
            className="cursor-pointer flex items-center gap-2 group"
          >
            <div className="w-8 h-8 rounded-lg bg-[#2563EB] text-white flex items-center justify-center font-bold text-sm shadow-sm group-hover:bg-[#1D4ED8] transition-colors">
              <Sparkles className="w-4 h-4 fill-white text-white" />
            </div>
            <div>
              <span className="text-lg font-black tracking-tight text-[#0F172A]">
                NEWS<span className="text-[#2563EB]">INTEL</span>
              </span>
              <span className="hidden sm:inline-block text-[10px] font-semibold text-[#64748B] uppercase tracking-wider ml-2 bg-[#EFF6FF] px-1.5 py-0.5 rounded text-[#2563EB] border border-[#60A5FA]/30">
                AI Intelligence
              </span>
            </div>
          </div>

          {/* Center: Navigation Links */}
          <nav className="hidden md:flex items-center space-x-1">
            {navItems.map((item, idx) => {
              const isActive = activeTab === item.tab && !selectedCategory;
              return (
                <button
                  key={idx}
                  onClick={() => {
                    if (onCategorySelect) onCategorySelect('');
                    setActiveTab(item.tab);
                  }}
                  className={`px-3.5 py-1.5 rounded-lg text-sm font-semibold transition-all ${
                    isActive
                      ? 'bg-[#EFF6FF] text-[#2563EB]'
                      : 'text-[#64748B] hover:text-[#0F172A] hover:bg-slate-50'
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Right: Quick Search Button & Live Status */}
        <div className="flex items-center gap-3">
          {/* Subtle Live Badge */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#F7FAFF] border border-[#E2E8F0] text-xs font-semibold text-[#64748B]">
            <span className={`w-2 h-2 rounded-full ${apiStatus === 'online' ? 'bg-[#16A34A] animate-pulse' : 'bg-slate-400'}`}></span>
            <span className="text-[11px] uppercase tracking-wider">{apiStatus === 'online' ? 'Live' : 'Syncing'}</span>
          </div>

          {/* Search Trigger */}
          <button
            onClick={() => setActiveTab('search')}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#F7FAFF] hover:bg-[#EFF6FF] border border-[#E2E8F0] text-[#64748B] hover:text-[#2563EB] text-xs font-semibold transition-all shadow-sm"
          >
            <Search className="w-4 h-4 text-[#2563EB]" />
            <span className="hidden sm:inline">Search</span>
          </button>
        </div>
      </div>
    </header>
  );
};



