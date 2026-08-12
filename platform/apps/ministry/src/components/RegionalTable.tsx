import { cn } from '@gula/ui-platform';
import { ArrowUpDown } from 'lucide-react';
import { useState } from 'react';

interface Column<T> {
  key: keyof T | string;
  label: string;
  labelAr: string;
  sortable?: boolean;
  render?: (item: T) => React.ReactNode;
  align?: 'left' | 'center' | 'right';
  width?: string;
}

interface RegionalTableProps<T> {
  data?: T[];
  columns?: Column<T>[];
  onRowClick?: (item: T) => void;
  className?: string;
}

export function RegionalTable<T extends Record<string, any>>({ data = [], columns = [], onRowClick, className }: RegionalTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  const sorted = [...data].sort((a, b) => {
    if (!sortKey) return 0;
    const aVal = a[sortKey];
    const bVal = b[sortKey];
    if (aVal == null) return 1;
    if (bVal == null) return -1;
    const cmp = typeof aVal === 'number' ? aVal - bVal : String(aVal).localeCompare(String(bVal));
    return sortDir === 'asc' ? cmp : -cmp;
  });

  return (
    <div className={cn('overflow-x-auto rounded-xl border border-white/10', className)}>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/5 bg-white/5">
            {columns.map(col => (
              <th
                key={String(col.key)}
                className={cn(
                  'px-4 py-3 text-xs font-bold uppercase tracking-wider text-slate-400',
                  col.align === 'center' && 'text-center',
                  col.align === 'right' && 'text-right',
                  col.align === 'left' && 'text-left',
                  !col.align && 'text-right',
                  col.sortable && 'cursor-pointer hover:text-white transition-colors',
                )}
                style={col.width ? { width: col.width } : undefined}
                onClick={() => col.sortable && handleSort(String(col.key))}
              >
                <span className="inline-flex items-center gap-1">
                  {col.labelAr}
                  {col.sortable && <ArrowUpDown size={12} className="text-slate-500" />}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((item, i) => (
            <tr
              key={item.id || i}
              onClick={() => onRowClick?.(item)}
              className={cn(
                'border-b border-white/5 transition-colors',
                onRowClick && 'cursor-pointer',
                'hover:bg-white/5',
              )}
            >
              {columns.map(col => (
                <td
                  key={String(col.key)}
                  className={cn(
                    'px-4 py-3 text-sm text-slate-300',
                    col.align === 'center' && 'text-center',
                    col.align === 'right' && 'text-right',
                    col.align === 'left' && 'text-left',
                    !col.align && 'text-right',
                  )}
                >
                  {col.render ? col.render(item) : String(item[col.key] ?? '-')}
                </td>
              ))}
            </tr>
          ))}
          {sorted.length === 0 && (
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center text-sm text-slate-500">
                لا توجد بيانات متاحة
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
