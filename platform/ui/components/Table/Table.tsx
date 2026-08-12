import { useState, type ReactNode, type HTMLAttributes, type ThHTMLAttributes } from 'react';
import { cn } from '../../utils/cn';

export interface Column<T> {
  key: string;
  header?: string;
  label?: string;
  labelAr?: string;
  sortable?: boolean;
  render?: (row: T) => ReactNode;
  align?: 'left' | 'center' | 'right';
  width?: string;
  className?: string;
  hideOnMobile?: boolean;
}

export interface TableProps<T> extends HTMLAttributes<HTMLDivElement> {
  columns: Column<T>[];
  data: T[];
  getRowKey?: (row: T) => string | number;
  sortable?: boolean;
  onSort?: (key: string, direction: 'asc' | 'desc') => void;
  emptyMessage?: string;
  loading?: boolean;
  loadingRows?: number;
  rowClassName?: string | ((row: T) => string);
  onRowClick?: (row: T) => void;
  stickyHeader?: boolean;
  compact?: boolean;
}

export function Table<T>({
  columns,
  data,
  getRowKey,
  sortable = false,
  onSort,
  emptyMessage = 'No data',
  loading = false,
  loadingRows = 5,
  rowClassName,
  onRowClick,
  stickyHeader = false,
  compact = false,
  className,
  ...props
}: TableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const isRtl = typeof document !== 'undefined' && document.documentElement.dir === 'rtl';

  const handleSort = (col: Column<T>) => {
    if (!col.sortable) return;
    const newDir = sortKey === col.key && sortDir === 'asc' ? 'desc' : 'asc';
    setSortKey(col.key);
    setSortDir(newDir);
    onSort?.(col.key, newDir);
  };

  const loadingRowsArray = Array.from({ length: loadingRows }, (_, i) => i);

  return (
    <div className={cn('w-full overflow-x-auto', className)} {...props}>
      <table className="w-full border-collapse">
        <thead>
          <tr className={cn(
            'border-b border-neutral-200 dark:border-neutral-700',
            stickyHeader && 'sticky top-0 bg-white dark:bg-neutral-800 z-10',
          )}>
            {columns.map(col => (
              <th
                key={col.key}
                onClick={() => sortable && handleSort(col)}
                className={cn(
                  'px-4 py-3 text-xs font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400',
                  col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left',
                  col.sortable && sortable && 'cursor-pointer select-none hover:text-neutral-700 dark:hover:text-neutral-200',
                  col.width && `w-[${col.width}]`,
                  col.hideOnMobile && 'hidden md:table-cell',
                  compact && 'px-3 py-2',
                )}
                style={col.width ? { width: col.width } : undefined}
                aria-sort={sortKey === col.key ? (sortDir === 'asc' ? 'ascending' : 'descending') : undefined}
              >
                <div className="flex items-center gap-1.5">
                  <span>{col.header ?? col.labelAr ?? col.label ?? col.key}</span>
                  {col.sortable && sortable && sortKey === col.key && (
                    <span className="text-primary-500">
                      {sortDir === 'asc' ? '\u25B2' : '\u25BC'}
                    </span>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            loadingRowsArray.map(idx => (
              <tr key={`skeleton-${idx}`} className="border-b border-neutral-100 dark:border-neutral-800">
                {columns.map(col => (
                  <td key={col.key} className={cn('px-4 py-3', compact && 'px-3 py-2', col.hideOnMobile && 'hidden md:table-cell')}>
                    <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded animate-pulse w-3/4" />
                  </td>
                ))}
              </tr>
            ))
          ) : data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-12 text-center text-neutral-500 dark:text-neutral-400"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, index) => (
              <tr
                key={getRowKey?.(row) ?? (row as { id?: string | number }).id ?? index}
                onClick={() => onRowClick?.(row)}
                className={cn(
                  'border-b border-neutral-100 dark:border-neutral-800 transition-colors',
                  onRowClick && 'cursor-pointer hover:bg-neutral-50 dark:hover:bg-neutral-800/50',
                  typeof rowClassName === 'function' ? rowClassName(row) : rowClassName,
                )}
              >
                {columns.map(col => (
                  <td
                    key={col.key}
                    className={cn(
                      'px-4 py-3 text-sm text-neutral-700 dark:text-neutral-300',
                      col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left',
                      col.hideOnMobile && 'hidden md:table-cell',
                      compact && 'px-3 py-2',
                      col.className,
                    )}
                  >
                    {col.render ? col.render(row) : (row as any)[col.key] as ReactNode}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
