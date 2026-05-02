import { cn } from '../../lib/utils';

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div className={cn("animate-pulse bg-slate-200 rounded-lg", className)} />
  );
}

export function DashboardSkeleton() {
  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-end">
        <div className="space-y-4">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-10 w-64" />
        </div>
        <Skeleton className="h-12 w-40" />
      </div>
      <div className="grid grid-cols-12 gap-6">
        <Skeleton className="col-span-8 h-64 rounded-2xl" />
        <Skeleton className="col-span-4 h-64 rounded-2xl" />
        <Skeleton className="col-span-12 h-48 rounded-2xl" />
      </div>
    </div>
  );
}
