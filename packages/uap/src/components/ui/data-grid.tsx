import React from 'react';
import { cn } from '../utils';

interface DataGridProps<T> {
  columns: {
    key: string;
    header: string;
    render?: (item: T) => React.ReactNode;
    width?: string;
    grow?: boolean;
  }[];
  data: T[];
  loading?: boolean;
  emptyMessage?: string;
  gap?: number;
  className?: string;
}

export function DataGrid<T extends { id: string }>({
  columns,
  data,
  loading,
  emptyMessage = 'No data',
  gap = 4,
  className,
}: DataGridProps<T>) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-32 bg-neutral-100 dark:bg-neutral-800 rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="text-center py-12 text-neutral-400">{emptyMessage}</div>
    );
  }

  return (
    <div className={cn('grid gap-4', className)} style={{ gap }}>
      {data.map((item) => (
        <div
          key={item.id}
          className="bg-white dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700 p-4 hover:shadow-md transition-shadow"
        >
          <div className="grid gap-3" style={{ gridTemplateColumns: `repeat(${columns.length}, 1fr)` }}>
            {columns.map((col) => (
              <div key={col.key} className={cn(col.grow && 'col-span-2')}>
                <span className="text-xs font-medium text-neutral-400 dark:text-neutral-500 block mb-1">
                  {col.header}
                </span>
                <div className="text-sm text-neutral-900 dark:text-white">
                  {col.render ? col.render(item) : String((item as any)[col.key] ?? '')}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
