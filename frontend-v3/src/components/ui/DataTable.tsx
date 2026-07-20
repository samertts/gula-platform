import { useMemo, useState, type ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { ChevronUp, ChevronDown, ChevronsUpDown, Search } from 'lucide-react';
import { EmptyState } from './EmptyState';
import { TableSkeleton } from './Skeleton';
import { useTranslation } from 'react-i18next';

export interface Column<T> {
  key: string;
  header: string;
  render?: (item: T) => ReactNode;
  sortable?: boolean;
  width?: string;
  align?: 'left' | 'center' | 'right';
  sticky?: boolean;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (item: T) => string | number;
  isLoading?: boolean;
  onRowClick?: (item: T) => void;
  emptyTitle?: string;
  emptyDescription?: string;
  searchable?: boolean;
  searchKeys?: (keyof T)[];
}

export function DataTable<T>({
  columns, data, keyExtractor, isLoading, onRowClick,
  emptyTitle, emptyDescription, searchable, searchKeys,
}: DataTableProps<T>) {
  const { t } = useTranslation();
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [searchQuery, setSearchQuery] = useState('');

  const filtered = useMemo(() => {
    if (!searchQuery || !searchKeys) return data;
    const q = searchQuery.toLowerCase();
    return data.filter((item) =>
      searchKeys.some((key) => {
        const val = item[key];
        return val != null && String(val).toLowerCase().includes(q);
      })
    );
  }, [data, searchQuery, searchKeys]);

  const sorted = useMemo(() => {
    if (!sortKey) return filtered;
    return [...filtered].sort((a, b) => {
      const aVal = (a as any)[sortKey];
      const bVal = (b as any)[sortKey];
      if (aVal == null) return 1;
      if (bVal == null) return -1;
      const cmp = String(aVal).localeCompare(String(bVal), undefined, { numeric: true });
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [filtered, sortKey, sortDir]);

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  if (isLoading) return <TableSkeleton />;

  return (
    <div className="space-y-3">
      {searchable && (
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-on-surface-variant" />
          <input
            className="h-10 w-full rounded-lg border border-outline bg-surface pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40"
            placeholder={t('search')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      )}
      {sorted.length === 0 ? (
        <EmptyState
          title={emptyTitle || t('noData')}
          description={emptyDescription}
        />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-outline">
          <table className="w-full">
            <thead>
              <tr className="border-b border-outline bg-surface-container-low">
                {columns.map((col) => (
                  <th
                    key={col.key}
                    className={cn(
                      'px-4 py-3 text-xs font-semibold text-on-surface-variant uppercase tracking-wider',
                      col.align === 'right' && 'text-right',
                      col.align === 'center' && 'text-center',
                      col.sticky && 'sticky left-0 bg-surface-container-low z-10',
                      col.sortable && 'cursor-pointer select-none hover:text-on-surface'
                    )}
                    style={{ width: col.width }}
                    onClick={() => col.sortable && handleSort(col.key)}
                  >
                    <div className="inline-flex items-center gap-1">
                      {col.header}
                      {col.sortable && (
                        sortKey === col.key
                          ? (sortDir === 'asc' ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />)
                          : <ChevronsUpDown className="h-3 w-3 opacity-50" />
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-outline">
              {sorted.map((item) => (
                <tr
                  key={keyExtractor(item)}
                  className={cn(
                    'transition-colors hover:bg-surface-container-low',
                    onRowClick && 'cursor-pointer'
                  )}
                  onClick={() => onRowClick?.(item)}
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={cn(
                        'px-4 py-3 text-sm',
                        col.align === 'right' && 'text-right',
                        col.align === 'center' && 'text-center',
                        col.sticky && 'sticky left-0 bg-surface hover:bg-surface-container-low z-10'
                      )}
                    >
                      {col.render ? col.render(item) : (item as any)[col.key]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
