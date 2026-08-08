import { useState, useMemo, type ReactNode } from 'react';
import { cn } from '../../utils/cn';
import { SearchInput } from '../SearchInput/SearchInput';
import { Pagination } from '../Pagination/Pagination';
import { LoadingSpinner } from '../LoadingSpinner/LoadingSpinner';

export interface DataTableColumn<T> {
  key: string;
  header: string;
  sortable?: boolean;
  filterable?: boolean;
  render?: (row: T) => ReactNode;
  align?: 'left' | 'center' | 'right';
  width?: string;
  hideOnMobile?: boolean;
  hidden?: boolean;
}

export interface DataTableAction<T> {
  label: string;
  icon?: ReactNode;
  onClick: (rows: T[]) => void;
  variant?: 'primary' | 'danger' | 'ghost';
}

export interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  data: T[];
  getRowKey: (row: T) => string | number;
  pageSize?: number;
  searchable?: boolean;
  searchPlaceholder?: string;
  searchKeys?: (keyof T)[];
  selectable?: boolean;
  actions?: DataTableAction<T>[];
  sortable?: boolean;
  loading?: boolean;
  emptyMessage?: string;
  emptyIcon?: ReactNode;
  onRowClick?: (row: T) => void;
  rowClassName?: string | ((row: T) => string);
  stickyHeader?: boolean;
  compact?: boolean;
  exportable?: boolean;
  onExport?: (rows: T[]) => void;
  className?: string;
  title?: string;
}

export function DataTable<T extends Record<string, any>>({
  columns,
  data,
  getRowKey,
  pageSize = 10,
  searchable = false,
  searchPlaceholder = 'Search...',
  searchKeys,
  selectable = false,
  actions,
  sortable = false,
  loading = false,
  emptyMessage = 'No data found',
  emptyIcon,
  onRowClick,
  rowClassName,
  stickyHeader = false,
  compact = false,
  exportable = false,
  onExport,
  className,
  title,
}: DataTableProps<T>) {
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Set<string | number>>(new Set());
  const [selectAll, setSelectAll] = useState(false);

  const filtered = useMemo(() => {
    if (!search) return data;
    const lowered = search.toLowerCase();
    return data.filter(row => {
      const keys = searchKeys || columns.map(c => c.key);
      return keys.some(key => {
        const val = row[key as string];
        return val != null && String(val).toLowerCase().includes(lowered);
      });
    });
  }, [data, search, searchKeys, columns]);

  const sorted = useMemo(() => {
    if (!sortKey) return filtered;
    return [...filtered].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      if (aVal == null) return 1;
      if (bVal == null) return -1;
      const cmp = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [filtered, sortKey, sortDir]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const paginated = sorted.slice((page - 1) * pageSize, page * pageSize);

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const handleSelectAll = () => {
    if (selectAll) {
      setSelected(new Set());
      setSelectAll(false);
    } else {
      setSelected(new Set(paginated.map(r => getRowKey(r))));
      setSelectAll(true);
    }
  };

  const handleSelect = (key: string | number) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
    setSelectAll(false);
  };

  const handleSearch = (val: string) => {
    setSearch(val);
    setPage(1);
  };

  const isRtl = typeof document !== 'undefined' && document.documentElement.dir === 'rtl';

  const visibleColumns = columns.filter(c => !c.hidden);

  return (
    <div className={cn('w-full bg-white dark:bg-neutral-900 rounded-2xl border border-neutral-200 dark:border-neutral-800', className)}>
      {/* Toolbar */}
      {(searchable || title || actions || exportable || selectable) && (
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-4 border-b border-neutral-100 dark:border-neutral-800">
          <div className="flex items-center gap-3">
            {title && <h3 className="text-lg font-bold text-neutral-900 dark:text-neutral-50">{title}</h3>}
            {selectable && selected.size > 0 && (
              <span className="text-sm font-medium text-primary-600 dark:text-primary-400">
                {selected.size} selected
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 w-full sm:w-auto">
            {searchable && (
              <SearchInput
                value={search}
                onChange={handleSearch}
                placeholder={searchPlaceholder}
                className="w-full sm:w-64"
              />
            )}
            {exportable && onExport && (
              <button
                onClick={() => onExport(selected.size > 0 ? data.filter(r => selected.has(getRowKey(r))) : data)}
                className="px-3 py-2 text-sm font-bold text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-xl transition-colors"
                aria-label="Export data"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M8 3v7M5 7l3 3 3-3M3 11v1.5c0 .8.7 1.5 1.5 1.5h7c.8 0 1.5-.7 1.5-1.5V11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            )}
            {actions && actions.length > 0 && selected.size > 0 && (
              <div className="flex items-center gap-1">
                {actions.map((action, i) => (
                  <button
                    key={i}
                    onClick={() => action.onClick(data.filter(r => selected.has(getRowKey(r))))}
                    className={cn(
                      'px-3 py-2 text-sm font-bold rounded-xl transition-colors',
                      action.variant === 'danger'
                        ? 'text-danger-600 hover:bg-danger-50 dark:text-danger-400 dark:hover:bg-danger-900/20'
                        : action.variant === 'ghost'
                          ? 'text-neutral-600 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:bg-neutral-800'
                          : 'text-primary-600 hover:bg-primary-50 dark:text-primary-400 dark:hover:bg-primary-900/20',
                    )}
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className={cn(
              'border-b border-neutral-200 dark:border-neutral-700',
              stickyHeader && 'sticky top-0 bg-white dark:bg-neutral-900 z-10',
            )}>
              {selectable && (
                <th className="px-4 py-3 w-10">
                  <input
                    type="checkbox"
                    checked={selectAll && paginated.length > 0}
                    onChange={handleSelectAll}
                    className="w-4 h-4 rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
                    aria-label="Select all rows"
                  />
                </th>
              )}
              {visibleColumns.map(col => (
                <th
                  key={col.key}
                  onClick={() => sortable && col.sortable && handleSort(col.key)}
                  className={cn(
                    'px-4 py-3 text-xs font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400',
                    col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left',
                    col.sortable && sortable && 'cursor-pointer select-none hover:text-neutral-700 dark:hover:text-neutral-200',
                    col.width && `w-[${col.width}]`,
                    col.hideOnMobile && 'hidden md:table-cell',
                    compact && 'px-3 py-2',
                  )}
                  style={col.width ? { width: col.width } : undefined}
                >
                  <div className="flex items-center gap-1.5">
                    <span>{col.header}</span>
                    {col.sortable && sortable && sortKey === col.key && (
                      <span className="text-primary-500">{sortDir === 'asc' ? '\u25B2' : '\u25BC'}</span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: pageSize }, (_, i) => (
                <tr key={`skel-${i}`} className="border-b border-neutral-100 dark:border-neutral-800">
                  {selectable && <td className="px-4 py-3"><div className="h-4 w-4 bg-neutral-200 dark:bg-neutral-700 rounded animate-pulse" /></td>}
                  {visibleColumns.map(col => (
                    <td key={col.key} className={cn('px-4 py-3', col.hideOnMobile && 'hidden md:table-cell')}>
                      <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded animate-pulse w-3/4" />
                    </td>
                  ))}
                </tr>
              ))
            ) : paginated.length === 0 ? (
              <tr>
                <td colSpan={visibleColumns.length + (selectable ? 1 : 0)} className="px-4 py-16">
                  <div className="flex flex-col items-center justify-center text-center">
                    {emptyIcon || (
                      <svg width="48" height="48" viewBox="0 0 48 48" fill="none" className="text-neutral-300 dark:text-neutral-600 mb-4">
                        <rect x="6" y="10" width="36" height="28" rx="4" stroke="currentColor" strokeWidth="2"/>
                        <path d="M6 18h36" stroke="currentColor" strokeWidth="2"/>
                        <circle cx="14" cy="14" r="1.5" fill="currentColor"/>
                        <circle cx="18" cy="14" r="1.5" fill="currentColor"/>
                      </svg>
                    )}
                    <p className="text-neutral-500 dark:text-neutral-400 font-medium">{emptyMessage}</p>
                    {search && (
                      <button
                        onClick={() => handleSearch('')}
                        className="mt-2 text-sm text-primary-600 dark:text-primary-400 hover:underline font-medium"
                      >
                        Clear search
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ) : (
              paginated.map(row => {
                const rowKey = getRowKey(row);
                return (
                  <tr
                    key={rowKey}
                    onClick={() => onRowClick?.(row)}
                    className={cn(
                      'border-b border-neutral-100 dark:border-neutral-800 transition-colors',
                      onRowClick && 'cursor-pointer',
                      'hover:bg-neutral-50 dark:hover:bg-neutral-800/50',
                      selected.has(rowKey) && 'bg-primary-50/50 dark:bg-primary-900/10',
                      typeof rowClassName === 'function' ? rowClassName(row) : rowClassName,
                    )}
                  >
                    {selectable && (
                      <td className="px-4 py-3 w-10">
                        <input
                          type="checkbox"
                          checked={selected.has(rowKey)}
                          onChange={() => handleSelect(rowKey)}
                          onClick={e => e.stopPropagation()}
                          className="w-4 h-4 rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
                          aria-label={`Select row ${rowKey}`}
                        />
                      </td>
                    )}
                    {visibleColumns.map(col => (
                      <td
                        key={col.key}
                        className={cn(
                          'px-4 py-3 text-sm text-neutral-700 dark:text-neutral-300',
                          col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left',
                          col.hideOnMobile && 'hidden md:table-cell',
                          compact && 'px-3 py-2',
                        )}
                      >
                        {col.render ? col.render(row) : (row[col.key] as ReactNode)}
                      </td>
                    ))}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="border-t border-neutral-100 dark:border-neutral-800 px-4 py-3">
          <Pagination
            currentPage={page}
            totalPages={totalPages}
            onPageChange={setPage}
            totalItems={sorted.length}
            pageSize={pageSize}
            compact
          />
        </div>
      )}
    </div>
  );
}
