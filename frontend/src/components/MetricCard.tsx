import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  iconColor?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
}) => {
  return (
    <div className="bg-white border border-stone-200 p-4 relative overflow-hidden">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[10px] font-extrabold uppercase tracking-wider text-stone-500">{title}</p>
          <h3 className="font-serif-headline text-2xl font-bold text-stone-900 mt-1 tracking-tight">{value}</h3>
          {subtitle && <p className="text-[11px] text-stone-500 mt-0.5">{subtitle}</p>}
        </div>
        <div className="p-2 bg-stone-100 border border-stone-200 text-stone-700">
          <Icon className="w-4 h-4 text-red-700" />
        </div>
      </div>
    </div>
  );
};

