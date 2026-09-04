import React from 'react';
import { SearchX, RefreshCw } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  onRetry?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No intelligence found for this topic yet.',
  description = 'Try searching another topic, checking backend connection, or clearing search filters.',
  onRetry,
}) => {
  return (
    <div className="bg-stone-50 border border-stone-200 p-10 text-center max-w-xl mx-auto my-8 space-y-3">
      <div className="p-3 bg-stone-100 border border-stone-200 w-12 h-12 mx-auto flex items-center justify-center text-red-700">
        <SearchX className="w-6 h-6" />
      </div>
      <h3 className="font-serif-headline font-bold text-lg text-stone-900">{title}</h3>
      <p className="text-xs text-stone-600 max-w-md mx-auto leading-relaxed">{description}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 inline-flex items-center gap-1.5 px-4 py-2 bg-stone-900 hover:bg-red-700 text-white text-xs font-bold uppercase tracking-wider transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Feed</span>
        </button>
      )}
    </div>
  );
};

