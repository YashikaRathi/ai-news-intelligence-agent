import React, { useState } from 'react';
import { Search } from 'lucide-react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  initialQuery?: string;
}

export const SearchBar: React.FC<SearchBarProps> = ({ onSearch, initialQuery = '' }) => {
  const [query, setQuery] = useState(initialQuery);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  const topicChips = [
    'Artificial Intelligence',
    'OpenAI',
    'SpaceX',
    'Cybersecurity',
    'Semiconductors',
  ];

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative flex items-center">
          <Search className="w-4 h-4 text-stone-400 absolute left-3.5 pointer-events-none" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search any topic, company, person, or event..."
            className="w-full pl-10 pr-24 py-2.5 bg-stone-50 border border-stone-300 text-stone-900 placeholder-stone-400 text-xs sm:text-sm focus:outline-none focus:border-stone-900 transition"
          />
          <button
            type="submit"
            className="absolute right-1.5 px-3.5 py-1.5 bg-stone-900 hover:bg-red-700 text-white font-bold text-xs uppercase tracking-wider transition-colors"
          >
            Search
          </button>
        </div>
      </form>

      {/* Suggested Topic Chips */}
      <div className="flex flex-wrap items-center gap-1.5 mt-2.5">
        <span className="text-[11px] font-bold text-stone-500 uppercase tracking-wider mr-1">
          Topics:
        </span>
        {topicChips.map((chip) => (
          <button
            key={chip}
            onClick={() => {
              setQuery(chip);
              onSearch(chip);
            }}
            className="px-2.5 py-0.5 bg-stone-100 hover:bg-stone-200 border border-stone-200 text-stone-700 hover:text-red-700 text-[11px] font-semibold transition-colors"
          >
            {chip}
          </button>
        ))}
      </div>
    </div>
  );
};

