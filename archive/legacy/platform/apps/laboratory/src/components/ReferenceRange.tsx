import { cn } from '@gula/ui-platform';

interface ReferenceRangeProps {
  low?: number;
  high?: number;
  unit?: string;
  value?: number;
  currentValue?: string;
  className?: string;
}

export function ReferenceRange({
  low,
  high,
  unit,
  value,
  currentValue,
  className,
}: ReferenceRangeProps) {
  if (low === undefined || high === undefined) {
    return (
      <span className={cn('text-xs text-neutral-400 dark:text-neutral-500', className)}>
        {currentValue || '---'}
      </span>
    );
  }

  const isOut = value !== undefined && (value < low || value > high);
  const isLow = value !== undefined && value < low;
  const isHigh = value !== undefined && value > high;

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div className="relative flex-1 h-2 bg-neutral-100 dark:bg-neutral-700 rounded-full overflow-hidden">
        <div
          className="absolute top-0 h-full bg-primary-500/30 dark:bg-primary-400/30 rounded-full"
          style={{ left: '0%', right: '0%' }}
        />
        {value !== undefined && low !== high && (
          <div
            className={cn(
              'absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full border-2 border-white shadow-md transition-all',
              isOut ? 'bg-danger-500' : 'bg-success-500',
            )}
            style={{
              left: `${Math.max(0, Math.min(100, ((value - low) / (high - low)) * 100))}%`,
            }}
          />
        )}
      </div>
      <div className="flex items-center gap-1.5 text-xs font-medium whitespace-nowrap">
        <span className={cn(
          isLow ? 'text-danger-600 dark:text-danger-400 font-bold' : 'text-neutral-500 dark:text-neutral-400',
        )}>
          {low.toLocaleString('ar')}
        </span>
        <span className="text-neutral-300 dark:text-neutral-600">-</span>
        <span className={cn(
          isHigh ? 'text-danger-600 dark:text-danger-400 font-bold' : 'text-neutral-500 dark:text-neutral-400',
        )}>
          {high.toLocaleString('ar')}
        </span>
        {unit && <span className="text-neutral-400 dark:text-neutral-500">{unit}</span>}
      </div>
      {isOut && (
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          className={cn(
            isLow ? 'text-danger-500' : 'text-danger-500',
            'shrink-0',
          )}
        >
          {isLow ? (
            <polyline points="12 19 12 5 5 12" />
          ) : (
            <polyline points="12 5 12 19 19 12" />
          )}
          <line x1="5" y1="12" x2="19" y2="12" />
        </svg>
      )}
    </div>
  );
}
