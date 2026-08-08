import { cn } from '@gula/ui-platform';

interface ReagentLevelProps {
  name: string;
  current: number;
  min: number;
  max: number;
  unit?: string;
  expiryDate?: string;
  lotNumber?: string;
  className?: string;
}

export function ReagentLevel({
  name,
  current,
  min,
  max,
  unit,
  expiryDate,
  lotNumber,
  className,
}: ReagentLevelProps) {
  const percentage = Math.min((current / max) * 100, 100);
  const isLow = current <= min;
  const isCritical = current <= min * 0.5;
  const isExpiring = expiryDate && new Date(expiryDate).getTime() - Date.now() < 30 * 24 * 60 * 60 * 1000;

  const barColor = isCritical
    ? 'bg-danger-500'
    : isLow
      ? 'bg-warning-500'
      : percentage > 80
        ? 'bg-success-500'
        : 'bg-primary-500';

  const statusLabel = isCritical
    ? 'حرج'
    : isLow
      ? 'منخفض'
      : 'جيد';

  const statusColor = isCritical
    ? 'text-danger-600 bg-danger-50 dark:bg-danger-900/30 dark:text-danger-400'
    : isLow
      ? 'text-warning-600 bg-warning-50 dark:bg-warning-900/30 dark:text-warning-400'
      : 'text-success-600 bg-success-50 dark:bg-success-900/30 dark:text-success-400';

  return (
    <div className={cn('p-4 bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700 shadow-sm', className)}>
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="min-w-0 flex-1">
          <h4 className="text-sm font-bold text-neutral-900 dark:text-neutral-100 truncate">{name}</h4>
          {lotNumber && (
            <p className="text-[10px] text-neutral-400 dark:text-neutral-500 font-mono mt-0.5">
              رقم الدفعة: {lotNumber}
            </p>
          )}
        </div>
        <span className={cn('px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider whitespace-nowrap', statusColor)}>
          {statusLabel}
        </span>
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs">
          <span className="font-bold text-neutral-900 dark:text-neutral-100">
            {current.toLocaleString('ar')} {unit}
          </span>
          <span className="text-neutral-400 dark:text-neutral-500">
            {max.toLocaleString('ar')} {unit}
          </span>
        </div>

        <div className="relative h-2.5 bg-neutral-100 dark:bg-neutral-700 rounded-full overflow-hidden">
          <div
            className={cn(
              'absolute top-0 right-0 h-full rounded-full transition-all duration-500',
              barColor,
              isCritical && 'animate-pulse',
            )}
            style={{ width: `${percentage}%` }}
          />
          <div
            className="absolute top-0 h-full rounded-full bg-neutral-900/10 dark:bg-white/10"
            style={{ right: `${(min / max) * 100}%`, width: '2px' }}
          />
        </div>

        <div className="flex items-center justify-between text-[10px] text-neutral-400 dark:text-neutral-500">
          <span>الحد الأدنى: {min.toLocaleString('ar')} {unit}</span>
          <span>المتبقي: {(current / min * 100).toFixed(0)}%</span>
        </div>
      </div>

      {expiryDate && (
        <div className={cn(
          'mt-3 pt-3 border-t border-neutral-100 dark:border-neutral-700 text-[10px] font-medium',
          isExpiring ? 'text-warning-500' : 'text-neutral-400 dark:text-neutral-500',
        )}>
          {isExpiring ? '⚠' : ''} ينتهي: {new Date(expiryDate).toLocaleDateString('ar-IQ')}
        </div>
      )}
    </div>
  );
}
