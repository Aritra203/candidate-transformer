import React from 'react';

interface StatusCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon: React.ComponentType<{ className?: string }>;
  status?: 'success' | 'warning' | 'error' | 'info' | 'neutral';
}

export default function StatusCard({
  title,
  value,
  description,
  icon: Icon,
  status = 'neutral'
}: StatusCardProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'success':
        return 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/20 border-emerald-100 dark:border-emerald-900/30';
      case 'warning':
        return 'text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/20 border-amber-100 dark:border-amber-900/30';
      case 'error':
        return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/20 border-red-100 dark:border-red-900/30';
      case 'info':
        return 'text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/20 border-indigo-100 dark:border-indigo-900/30';
      default:
        return 'text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-900/40 border-slate-100 dark:border-slate-800/40';
    }
  };

  return (
    <div className={`rounded-xl border p-5 bg-white dark:bg-slate-950 transition-all shadow-sm ${getStatusColor()}`}>
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-slate-500 dark:text-slate-400">{title}</span>
        <div className="p-2 rounded-lg bg-white dark:bg-slate-900/60 shadow-sm border border-slate-100 dark:border-slate-800">
          <Icon className="h-4 w-4" />
        </div>
      </div>
      <div className="mt-3">
        <h3 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          {value}
        </h3>
        {description && (
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 truncate">
            {description}
          </p>
        )}
      </div>
    </div>
  );
}
