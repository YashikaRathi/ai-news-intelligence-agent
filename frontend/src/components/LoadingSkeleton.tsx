import React from 'react';

export const LoadingSkeleton: React.FC = () => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 animate-pulse">
      {[1, 2, 3, 4, 5, 6].map((idx) => (
        <div key={idx} className="bg-stone-50 border border-stone-200 p-5 h-64 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="h-4 w-20 bg-stone-200"></div>
              <div className="h-3 w-12 bg-stone-200"></div>
            </div>
            <div className="h-5 w-5/6 bg-stone-200 mb-2"></div>
            <div className="h-5 w-3/4 bg-stone-200 mb-4"></div>
            <div className="h-3 w-full bg-stone-100 mb-1.5"></div>
            <div className="h-3 w-4/5 bg-stone-100"></div>
          </div>
          <div className="pt-3 border-t border-stone-200 flex justify-between items-center">
            <div className="h-3 w-28 bg-stone-200"></div>
            <div className="h-6 w-20 bg-stone-200"></div>
          </div>
        </div>
      ))}
    </div>
  );
};

