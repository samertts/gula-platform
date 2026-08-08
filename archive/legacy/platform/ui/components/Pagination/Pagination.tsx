import { type MouseEvent } from 'react';
import { cn } from '../../utils/cn';

export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  totalItems?: number;
  pageSize?: number;
  siblingCount?: number;
  showFirstLast?: boolean;
  showPrevNext?: boolean;
  compact?: boolean;
  className?: string;
}

export function Pagination({
  currentPage,
  totalPages,
  onPageChange,
  totalItems,
  pageSize,
  siblingCount = 1,
  showFirstLast = true,
  showPrevNext = true,
  compact = false,
  className,
}: PaginationProps) {
  const isRtl = typeof document !== 'undefined' && document.documentElement.dir === 'rtl';

  const range = (start: number, end: number) =>
    Array.from({ length: end - start + 1 }, (_, i) => start + i);

  const getPageNumbers = (): (number | 'ellipsis')[] => {
    const total = totalPages;
    const current = currentPage;
    const siblings = siblingCount;

    if (total <= 5 + siblings * 2) return range(1, total);

    const leftEnd = Math.min(2 + siblings, total);
    const rightStart = Math.max(total - 1 - siblings, 1);
    const middleStart = Math.max(current - siblings, leftEnd + 1);
    const middleEnd = Math.min(current + siblings, rightStart - 1);

    const pages: (number | 'ellipsis')[] = range(1, leftEnd);
    if (middleStart > leftEnd + 1) pages.push('ellipsis');
    if (middleStart <= middleEnd) pages.push(...range(middleStart, middleEnd));
    if (middleEnd < rightStart - 1) pages.push('ellipsis');
    pages.push(...range(rightStart, total));
    return pages;
  };

  const pageNumbers = getPageNumbers();

  const handleClick = (e: MouseEvent, page: number) => {
    e.preventDefault();
    if (page < 1 || page > totalPages) return;
    onPageChange(page);
  };

  if (totalPages <= 1 && !totalItems) return null;

  const btnBase = cn(
    'flex items-center justify-center font-bold transition-all duration-200',
    'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',
    compact
      ? 'w-8 h-8 text-xs rounded-lg'
      : 'w-10 h-10 text-sm rounded-xl',
  );

  const btnActive = 'bg-primary-500 text-white shadow-sm';
  const btnInactive = 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 hover:text-neutral-900 dark:hover:text-neutral-200';
  const btnDisabled = 'opacity-40 cursor-not-allowed';

  return (
    <nav aria-label="Pagination" className={cn('flex items-center gap-1', className)}>
      {totalItems !== undefined && !compact && (
        <span className="text-sm text-neutral-500 dark:text-neutral-400 mr-3 rtl:mr-0 rtl:ml-3">
          {totalItems} items
          {pageSize ? ` (page ${currentPage} of ${totalPages})` : ''}
        </span>
      )}

      {showFirstLast && (
        <button
          onClick={e => handleClick(e, 1)}
          disabled={currentPage === 1}
          className={cn(btnBase, currentPage === 1 ? btnDisabled : btnInactive)}
          aria-label="First page"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className={cn(isRtl && 'rotate-180')}>
            <path d="M11 4l-4 4 4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M6 4v8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
        </button>
      )}

      {showPrevNext && (
        <button
          onClick={e => handleClick(e, currentPage - 1)}
          disabled={currentPage === 1}
          className={cn(btnBase, currentPage === 1 ? btnDisabled : btnInactive)}
          aria-label="Previous page"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className={cn(isRtl && 'rotate-180')}>
            <path d="M10 4l-4 4 4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      )}

      {pageNumbers.map((page, idx) =>
        page === 'ellipsis' ? (
          <span key={`ellipsis-${idx}`} className={cn(btnBase, 'cursor-default text-neutral-400')}>
            ...
          </span>
        ) : (
          <button
            key={page}
            onClick={e => handleClick(e, page)}
            disabled={page === currentPage}
            className={cn(btnBase, page === currentPage ? btnActive : btnInactive)}
            aria-label={`Page ${page}`}
            aria-current={page === currentPage ? 'page' : undefined}
          >
            {page}
          </button>
        ),
      )}

      {showPrevNext && (
        <button
          onClick={e => handleClick(e, currentPage + 1)}
          disabled={currentPage === totalPages}
          className={cn(btnBase, currentPage === totalPages ? btnDisabled : btnInactive)}
          aria-label="Next page"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className={cn(isRtl && 'rotate-180')}>
            <path d="M6 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      )}

      {showFirstLast && (
        <button
          onClick={e => handleClick(e, totalPages)}
          disabled={currentPage === totalPages}
          className={cn(btnBase, currentPage === totalPages ? btnDisabled : btnInactive)}
          aria-label="Last page"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className={cn(isRtl && 'rotate-180')}>
            <path d="M5 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M10 4v8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
        </button>
      )}
    </nav>
  );
}
