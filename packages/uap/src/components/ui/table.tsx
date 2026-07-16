import React, { useState, useMemo } from 'react';
import { cn } from '../utils';
import { ChevronUp, ChevronDown, ChevronsUpDown, Search } from 'lucide-react';

interface Column<T> {
  key: string;
  header: string;
  render?: (item: T) => React.ReactNode;
  sortable?: boolean;
  filterable?: boolean;
  width?: string;
  align?: 'left' | 'center' | 'right';
}

interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  variant?: 'striped' | 'bordered' | 'hover' | 'compact';
  paginated?: boolean;
  pageSize?: number;
  searchable?: boolean;
  selectable?: boolean;
  onSelectionChange?: (selected: Set<string>) => void;
  rtl?: boolean;
  loading?: boolean;
  emptyMessage?: string;
  className?: string;
}

export function Table<T extends { id: string }>({
  columns,
  data,
  variant = 'striped',
  paginated = true,
  pageSize = 20,
  searchable = false,
  selectable = false,
  onSelectionChange,
  rtl = false,
  loading = false,
  emptyMessage = 'No data available',
  className,
}: TableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [page, setPage] = useState(0);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const filtered = useMemo(() => {
    if (!search) return data;
    const q = search.toLowerCase();
    return data.filter((item) =>
      columns.some((col) => {
        const val = String((item as any)[col.key] ?? '');
        return val.toLowerCase().includes(q);
      })
    );
  }, [data, search, columns]);

  const sorted = useMemo(() => {
    if (!sortKey) return filtered;
    return [...filtered].sort((a, b) => {
      const aVal = (a as any)[sortKey];
      const bVal = (b as any)[sortKey];
      const cmp = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [filtered, sortKey, sortDir]);

  const totalPages = Math.ceil(sorted.length / pageSize);
  const paged = paginated ? sorted.slice(page * pageSize, (page + 1) * pageSize) : sorted;

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const toggleSelect = (id: string) => {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelected(next);
    onSelectionChange?.(next);
  };

  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-12 bg-neutral-100 dark:bg-neutral-800 rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className={cn('w-full', className)}>
      {searchable && (
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" size={16} />
          <input
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(0); }}
            placeholder="Search..."
            className={cn(
              'w-full pl-10 pr-4 py-2 rounded-lg border border-neutral-300 dark:border-neutral-600',
              'bg-white dark:bg-neutral-800 text-sm',
              rtl && 'text-right'
            )}
          />
        </div>
      )}
      <div className="overflow-x-auto rounded-lg border border-neutral-200 dark:border-neutral-700">
        <table className={cn(
          'w-full text-sm',
          rtl && 'text-right',
          variant === 'compact' && 'text-xs'
        )}>
          <thead className="bg-neutral-50 dark:bg-neutral-900">
            <tr>
              {selectable && <th className="p-3 w-10"><input type="checkbox" disabled /></th>}
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={cn(
                    'p-3 font-medium text-neutral-600 dark:text-neutral-400',
                    'border-b border-neutral-200 dark:border-neutral-700',
                    col.sortable && 'cursor-pointer select-none hover:text-neutral-900 dark:hover:text-white',
                    col.align === 'right' && 'text-right',
                    col.align === 'center' && 'text-center'
                  )}
                  style={col.width ? { width: col.width } : undefined}
                  onClick={col.sortable ? () => handleSort(col.key) : undefined}
                >
                  <span className="inline-flex items-center gap-1">
                    {col.header}
                    {col.sortable && (
                      sortKey === col.key
                        ? sortDir === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                        : <ChevronsUpDown size={14} className="opacity-40" />
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paged.length === 0 ? (
              <tr>
                <td colSpan={columns.length + (selectable ? 1 : 0)} className="p-8 text-center text-neutral-400">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              paged.map((item, i) => (
                <tr
                  key={item.id}
                  className={cn(
                    'transition-colors duration-100',
                    variant === 'striped' && i % 2 === 1 && 'bg-neutral-50 dark:bg-neutral-800/50',
                    variant === 'hover' && 'hover:bg-neutral-50 dark:hover:bg-neutral-800',
                    selected.has(item.id) && 'bg-primary-50 dark:bg-primary-900/20',
                  )}
                >
                  {selectable && (
                    <td className="p-3">
                      <input
                        type="checkbox"
                        checked={selected.has(item.id)}
                        onChange={() => toggleSelect(item.id)}
                      />
                    </td>
                  )}
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={cn(
                        'p-3 border-b border-neutral-100 dark:border-neutral-800',
                        variant === 'bordered' && 'border-r dark:border-neutral-700',
                        variant === 'compact' && 'p-2',
                        col.align === 'right' && 'text-right',
                        col.align === 'center' && 'text-center'
                      )}
                    >
                      {col.render ? col.render(item) : String((item as any)[col.key] ?? '')}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      {paginated && totalPages > 1 && (
        <div className={cn('flex items-center justify-between mt-4 text-sm', rtl && 'flex-row-reverse')}>
          <span className="text-neutral-500">
            {page * pageSize + 1}-{Math.min((page + 1) * pageSize, sorted.length)} of {sorted.length}
          </span>
          <div className="flex gap-1">
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="px-3 py-1 rounded border border-neutral-300 dark:border-neutral-600 disabled:opacity-50 hover:bg-neutral-50 dark:hover:bg-neutral-800"
            >
              Prev
            </button>
            {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
              const start = Math.max(0, Math.min(page - 2, totalPages - 5));
              const p = start + i;
              return (
                <button
                  key={p}
                  onClick={() => setPage(p)}
                  className={cn(
                    'px-3 py-1 rounded border',
                    p === page
                      ? 'bg-primary-600 text-white border-primary-600'
                      : 'border-neutral-300 dark:border-neutral-600 hover:bg-neutral-50 dark:hover:bg-neutral-800'
                  )}
                >
                  {p + 1}
                </button>
              );
            })}
            <button
              onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
              disabled={page >= totalPages - 1}
              className="px-3 py-1 rounded border border-neutral-300 dark:border-neutral-600 disabled:opacity-50 hover:bg-neutral-50 dark:hover:bg-neutral-800"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
