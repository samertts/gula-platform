import { cn } from '../../lib/utils';

interface SkeletonProps {
  className?: string;
  /** Provide a label for screen readers. Defaults to "Loading…". */
  ariaLabel?: string;
}

/**
 * Base shimmer block. Sized via Tailwind utility classes. Includes
 * `aria-busy` so assistive tech announces the loading state without
 * announcing the placeholder geometry.
 */
export function Skeleton({ className, ariaLabel }: SkeletonProps) {
  return (
    <div
      role="status"
      aria-busy="true"
      aria-label={ariaLabel ?? 'Loading'}
      className={cn('animate-pulse bg-slate-200/80 rounded-lg', className)}
    />
  );
}

/* ─── Composite skeletons ────────────────────────────────────────────── */

export function DashboardSkeleton() {
  return (
    <div
      className="p-8 space-y-8 max-w-7xl mx-auto"
      data-testid="dashboard-skeleton"
    >
      <div className="flex justify-between items-end">
        <div className="space-y-4">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-10 w-64" />
        </div>
        <Skeleton className="h-12 w-40" />
      </div>
      <StatGridSkeleton />
      <div className="grid grid-cols-12 gap-6">
        <Skeleton className="col-span-12 lg:col-span-8 h-64 rounded-2xl" />
        <Skeleton className="col-span-12 lg:col-span-4 h-64 rounded-2xl" />
        <Skeleton className="col-span-12 h-48 rounded-2xl" />
      </div>
    </div>
  );
}

export function StatGridSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div
      className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6"
      data-testid="stat-grid-skeleton"
    >
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="bg-white/40 p-8 rounded-[2.5rem] border border-white shadow-sm space-y-4"
        >
          <div className="flex justify-between">
            <Skeleton className="h-12 w-12 rounded-2xl" />
            <Skeleton className="h-5 w-16 rounded-full" />
          </div>
          <Skeleton className="h-3 w-1/2" />
          <Skeleton className="h-9 w-3/4" />
          <Skeleton className="h-1 w-full" />
        </div>
      ))}
    </div>
  );
}

/**
 * Table skeleton that preserves layout (column count + row height) so the
 * real table mounts without layout shift.
 */
export function TableSkeleton({
  rows = 6,
  columns = 5,
  showHeader = true,
}: {
  rows?: number;
  columns?: number;
  showHeader?: boolean;
}) {
  return (
    <div
      className="w-full bg-white rounded-2xl border border-slate-100 overflow-hidden"
      data-testid="table-skeleton"
    >
      {showHeader && (
        <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/60 flex gap-6">
          {Array.from({ length: columns }).map((_, i) => (
            <Skeleton key={i} className="h-3 flex-1" />
          ))}
        </div>
      )}
      <div className="divide-y divide-slate-100">
        {Array.from({ length: rows }).map((_, r) => (
          <div key={r} className="px-6 py-5 flex gap-6 items-center">
            <Skeleton className="h-8 w-8 rounded-full shrink-0" />
            {Array.from({ length: columns - 1 }).map((_, c) => (
              <Skeleton
                key={c}
                className={cn('h-4', c === 0 ? 'flex-1' : 'flex-1 max-w-[8rem]')}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export function ListSkeleton({ items = 5 }: { items?: number }) {
  return (
    <div className="space-y-3" data-testid="list-skeleton">
      {Array.from({ length: items }).map((_, i) => (
        <div
          key={i}
          className="flex items-center gap-4 p-4 bg-white rounded-2xl border border-slate-100"
        >
          <Skeleton className="h-10 w-10 rounded-2xl shrink-0" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-1/3" />
            <Skeleton className="h-3 w-2/3" />
          </div>
          <Skeleton className="h-6 w-16 rounded-full" />
        </div>
      ))}
    </div>
  );
}

export function CardSkeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'p-6 bg-white rounded-2xl border border-slate-100 space-y-4',
        className,
      )}
      data-testid="card-skeleton"
    >
      <div className="flex items-center gap-3">
        <Skeleton className="h-10 w-10 rounded-2xl" />
        <Skeleton className="h-4 w-32" />
      </div>
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-3 w-5/6" />
      <Skeleton className="h-3 w-3/4" />
    </div>
  );
}
