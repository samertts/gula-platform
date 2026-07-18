import { cn } from '@gula/ui-platform';
import type { LabResult } from '../types';

interface ResultCardProps {
  result: LabResult;
  onClick?: (id: string) => void;
  className?: string;
}

const flagColors: Record<string, string> = {
  H: 'text-danger-600 bg-danger-50 dark:text-danger-400 dark:bg-danger-900/20',
  L: 'text-warning-600 bg-warning-50 dark:text-warning-400 dark:bg-warning-900/20',
  N: 'text-success-600 bg-success-50 dark:text-success-400 dark:bg-success-900/20',
  C: 'text-danger-600 bg-danger-50 dark:text-danger-400 dark:bg-danger-900/20 animate-pulse',
};

const flagLabels: Record<string, string> = {
  H: 'مرتفع',
  L: 'منخفض',
  N: 'طبيعي',
  C: 'حرج',
};

const statusColors: Record<string, string> = {
  pending: 'bg-warning-100 text-warning-700',
  completed: 'bg-success-100 text-success-700',
  verified: 'bg-primary-100 text-primary-700',
  amended: 'bg-neutral-100 text-neutral-600',
};

const statusLabels: Record<string, string> = {
  pending: 'قيد التنفيذ',
  completed: 'مكتمل',
  verified: 'معتمد',
  amended: 'معدل',
};

export function ResultCard({ result, onClick, className }: ResultCardProps) {
  return (
    <div
      className={cn(
        'bg-white dark:bg-neutral-800 rounded-2xl p-5 border border-neutral-200 dark:border-neutral-700 shadow-sm',
        onClick && 'cursor-pointer hover:shadow-md hover:border-primary-300 dark:hover:border-primary-600 transition-all',
        className,
      )}
      onClick={() => onClick?.(result.id)}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => e.key === 'Enter' && onClick(result.id) : undefined}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="min-w-0 flex-1">
          <h3 className="font-bold text-neutral-900 dark:text-neutral-50 truncate">{result.testName}</h3>
          <p className="text-[10px] text-neutral-500 mt-0.5">{result.labName}</p>
        </div>
        <span className={cn('px-2 py-0.5 rounded-lg text-[10px] font-bold', statusColors[result.status])}>
          {statusLabels[result.status]}
        </span>
      </div>

      <div className="flex items-end gap-3 mb-3">
        <div>
          <span className="text-2xl font-black text-neutral-900 dark:text-neutral-50">{result.value}</span>
          <span className="text-xs text-neutral-500 mr-1">{result.unit}</span>
        </div>
        <span className={cn('px-2 py-1 rounded-lg text-[10px] font-bold', flagColors[result.flag])}>
          {flagLabels[result.flag]}
        </span>
      </div>

      <div className="flex items-center justify-between text-[10px] text-neutral-400">
        <span>النطاق المرجعي: {result.referenceRange}</span>
        <span>{new Date(result.performedDate).toLocaleDateString('ar-IQ')}</span>
      </div>

      {result.interpretation && (
        <p className="mt-3 text-xs text-neutral-600 dark:text-neutral-400 bg-neutral-50 dark:bg-neutral-700/50 p-3 rounded-xl leading-relaxed">
          {result.interpretation}
        </p>
      )}

      {result.trend && result.trend.length > 1 && (
        <div className="mt-3 flex items-end gap-1 h-10">
          {result.trend.map((point, i) => {
            const max = Math.max(...result.trend!.map((p) => p.value));
            const height = (point.value / max) * 100;
            return (
              <div
                key={i}
                className="flex-1 bg-primary-200 dark:bg-primary-800 rounded-t"
                style={{ height: `${height}%` }}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}
