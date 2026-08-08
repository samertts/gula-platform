import { cn } from '@gula/ui-platform';
import type { Analyzer, AnalyzerStatus } from '@/utils/types';

interface InstrumentCardProps {
  analyzer: Analyzer;
  onSelect?: (analyzer: Analyzer) => void;
  compact?: boolean;
  className?: string;
}

const statusConfig: Record<AnalyzerStatus, { label: string; color: string }> = {
  online: { label: 'متصل', color: 'text-success-600 bg-success-50 dark:bg-success-900/30 dark:text-success-400' },
  offline: { label: 'غير متصل', color: 'text-neutral-500 bg-neutral-100 dark:bg-neutral-700 dark:text-neutral-400' },
  maintenance: { label: 'صيانة', color: 'text-warning-600 bg-warning-50 dark:bg-warning-900/30 dark:text-warning-400' },
  calibrating: { label: 'معايرة', color: 'text-info-600 bg-info-50 dark:bg-info-900/30 dark:text-info-400' },
  qc_failed: { label: 'فشل الجودة', color: 'text-danger-600 bg-danger-50 dark:bg-danger-900/30 dark:text-danger-400' },
  error: { label: 'خطأ', color: 'text-danger-600 bg-danger-50 dark:bg-danger-900/30 dark:text-danger-400' },
  disabled: { label: 'معطل', color: 'text-neutral-500 bg-neutral-100 dark:bg-neutral-700 dark:text-neutral-400' },
};

export function InstrumentCard({
  analyzer,
  onSelect,
  compact = false,
  className,
}: InstrumentCardProps) {
  const status = statusConfig[analyzer.status];

  if (compact) {
    return (
      <button
        type="button"
        onClick={() => onSelect?.(analyzer)}
        className={cn(
          'w-full text-right p-4 rounded-2xl border-2 transition-all bg-white dark:bg-neutral-800',
          'hover:shadow-md focus:outline-none focus-visible:ring-4 focus-visible:ring-primary-200',
          analyzer.status === 'online' ? 'border-success-200 dark:border-success-700' :
          analyzer.status === 'error' || analyzer.status === 'qc_failed' ? 'border-danger-200 dark:border-danger-700' :
          analyzer.status === 'offline' ? 'border-neutral-200 dark:border-neutral-600' :
          'border-warning-200 dark:border-warning-700',
          className,
        )}
      >
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className={cn(
              'w-3 h-3 rounded-full shrink-0',
              analyzer.status === 'online' ? 'bg-success-500' :
              analyzer.status === 'error' || analyzer.status === 'qc_failed' ? 'bg-danger-500 animate-pulse' :
              analyzer.status === 'calibrating' ? 'bg-info-500 animate-pulse' :
              analyzer.status === 'maintenance' ? 'bg-warning-500' :
              'bg-neutral-400',
            )} />
            <div className="min-w-0">
              <p className="text-sm font-bold text-neutral-900 dark:text-neutral-100 truncate">
                {analyzer.name}
              </p>
              <p className="text-[10px] text-neutral-500 dark:text-neutral-400 truncate">
                {analyzer.model}
              </p>
            </div>
          </div>
          <span className={cn('px-2 py-0.5 rounded-full text-[9px] font-bold whitespace-nowrap', status.color)}>
            {status.label}
          </span>
        </div>
      </button>
    );
  }

  return (
    <div
      className={cn(
        'rounded-2xl border-2 p-6 transition-all bg-white dark:bg-neutral-800 shadow-sm',
        'hover:shadow-md',
        analyzer.status === 'online' ? 'border-success-200 dark:border-success-700' :
        analyzer.status === 'error' || analyzer.status === 'qc_failed' ? 'border-danger-200 dark:border-danger-700' :
        analyzer.status === 'offline' ? 'border-neutral-200 dark:border-neutral-600' :
        'border-warning-200 dark:border-warning-700',
        className,
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-2">
            <div className={cn(
              'w-3.5 h-3.5 rounded-full shrink-0',
              analyzer.status === 'online' ? 'bg-success-500 shadow-lg shadow-success-500/30' :
              analyzer.status === 'error' || analyzer.status === 'qc_failed' ? 'bg-danger-500 animate-pulse' :
              analyzer.status === 'calibrating' ? 'bg-info-500 animate-pulse' :
              analyzer.status === 'maintenance' ? 'bg-warning-500' :
              'bg-neutral-400',
            )} />
            <h3 className="text-lg font-bold text-neutral-900 dark:text-neutral-100 truncate">
              {analyzer.name}
            </h3>
            <span className={cn('px-2.5 py-0.5 rounded-full text-[9px] font-bold', status.color)}>
              {status.label}
            </span>
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-neutral-500 dark:text-neutral-400">
            <span>الطراز: {analyzer.model}</span>
            <span>الرقم التسلسلي: {analyzer.serialNumber}</span>
            <span>الشركة: {analyzer.manufacturer}</span>
          </div>
          {analyzer.location && (
            <span className="text-xs text-neutral-400 dark:text-neutral-500 mt-1 block">
              الموقع: {analyzer.location}
            </span>
          )}
        </div>

        {onSelect && (
          <button
            type="button"
            onClick={() => onSelect(analyzer)}
            className="px-4 py-2 text-xs font-bold text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/30 rounded-xl transition-colors shrink-0"
          >
            تفاصيل
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-5 pt-5 border-t border-neutral-100 dark:border-neutral-700">
        <div className="text-center">
          <p className="text-lg font-black text-neutral-900 dark:text-neutral-100">
            {analyzer.metrics?.testsProcessed || 0}
          </p>
          <p className="text-[9px] text-neutral-400 dark:text-neutral-500 font-bold uppercase tracking-wider mt-1">
            إجمالي الفحوصات
          </p>
        </div>
        <div className="text-center">
          <p className="text-lg font-black text-neutral-900 dark:text-neutral-100">
            {analyzer.metrics?.throughput || 0}
          </p>
          <p className="text-[9px] text-neutral-400 dark:text-neutral-500 font-bold uppercase tracking-wider mt-1">
            لكل ساعة
          </p>
        </div>
        <div className="text-center">
          <p className={cn(
            'text-lg font-black',
            analyzer.metrics?.errorRate && analyzer.metrics.errorRate > 5 ? 'text-danger-500' : 'text-neutral-900 dark:text-neutral-100',
          )}>
            {analyzer.metrics?.errorRate?.toFixed(1) || 0}%
          </p>
          <p className="text-[9px] text-neutral-400 dark:text-neutral-500 font-bold uppercase tracking-wider mt-1">
            نسبة الأخطاء
          </p>
        </div>
        <div className="text-center">
          <p className="text-lg font-black text-neutral-900 dark:text-neutral-100">
            {analyzer.metrics?.uptime ? `${analyzer.metrics.uptime}%` : '---'}
          </p>
          <p className="text-[9px] text-neutral-400 dark:text-neutral-500 font-bold uppercase tracking-wider mt-1">
            زمن التشغيل
          </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5 mt-4">
        {analyzer.tests.slice(0, 5).map(test => (
          <span key={test} className="px-2 py-0.5 bg-neutral-100 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-300 rounded text-[9px] font-medium">
            {test}
          </span>
        ))}
        {analyzer.tests.length > 5 && (
          <span className="px-2 py-0.5 bg-neutral-100 dark:bg-neutral-700 text-neutral-400 dark:text-neutral-500 rounded text-[9px] font-medium">
            +{analyzer.tests.length - 5}
          </span>
        )}
      </div>

      {analyzer.lastCalibration && (
        <div className="flex items-center gap-4 mt-4 pt-4 border-t border-neutral-100 dark:border-neutral-700 text-xs text-neutral-500 dark:text-neutral-400">
          <span>آخر معايرة: {new Date(analyzer.lastCalibration).toLocaleDateString('ar-IQ')}</span>
          {analyzer.lastQC && <span>آخر QC: {new Date(analyzer.lastQC).toLocaleDateString('ar-IQ')}</span>}
        </div>
      )}
    </div>
  );
}
