import { useState } from 'react';
import { cn } from '@gula/ui-platform';

interface CriticalValueFlagProps {
  testName: string;
  value: string;
  unit?: string;
  flag: 'critical_high' | 'critical_low' | 'panic';
  patientName: string;
  sampleId: string;
  acknowledged?: boolean;
  onAcknowledge?: () => void;
  onCallPhysician?: () => void;
  className?: string;
}

export function CriticalValueFlag({
  testName,
  value,
  unit,
  flag,
  patientName,
  sampleId,
  acknowledged = false,
  onAcknowledge,
  onCallPhysician,
  className,
}: CriticalValueFlagProps) {
  const [acknowledging, setAcknowledging] = useState(false);

  const handleAcknowledge = async () => {
    setAcknowledging(true);
    try {
      await onAcknowledge?.();
    } finally {
      setAcknowledging(false);
    }
  };

  const severityLabel = flag === 'panic' ? 'قيمة خطيرة' : 'قيمة حرجة';
  const severityColor = flag === 'panic' ? 'danger' : 'warning';

  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-2xl border-2 p-5 transition-all',
        !acknowledged && 'animate-pulse',
        severityColor === 'danger'
          ? 'bg-danger-50 dark:bg-danger-900/20 border-danger-300 dark:border-danger-700'
          : 'bg-warning-50 dark:bg-warning-900/20 border-warning-300 dark:border-warning-700',
        acknowledged && 'opacity-70',
        className,
      )}
    >
      <div className={cn(
        'absolute top-0 right-0 w-32 h-32 rounded-full blur-3xl opacity-20 -mr-8 -mt-8',
        severityColor === 'danger' ? 'bg-danger-500' : 'bg-warning-500',
      )} />

      <div className="relative z-10 space-y-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={cn(
              'w-10 h-10 rounded-xl flex items-center justify-center',
              severityColor === 'danger'
                ? 'bg-danger-100 dark:bg-danger-900/40 text-danger-600 dark:text-danger-400'
                : 'bg-warning-100 dark:bg-warning-900/40 text-warning-600 dark:text-warning-400',
            )}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className={cn(
                  'text-sm font-black uppercase tracking-wider',
                  severityColor === 'danger' ? 'text-danger-600 dark:text-danger-400' : 'text-warning-600 dark:text-warning-400',
                )}>
                  {severityLabel}
                </span>
                {!acknowledged && (
                  <span className="w-2 h-2 rounded-full bg-danger-500 animate-ping" />
                )}
              </div>
              <span className="text-xs font-medium text-neutral-500 dark:text-neutral-400">
                {testName}
              </span>
            </div>
          </div>

          {acknowledged && (
            <span className="px-2.5 py-1 bg-success-50 dark:bg-success-900/30 text-success-600 dark:text-success-400 rounded-full text-[10px] font-black uppercase tracking-wider">
              تم الإقرار
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 bg-white/60 dark:bg-neutral-800/60 rounded-xl">
            <span className="block text-[10px] font-black text-neutral-400 dark:text-neutral-500 uppercase tracking-wider mb-1">
              القيمة
            </span>
            <span className={cn(
              'text-2xl font-black',
              severityColor === 'danger' ? 'text-danger-600 dark:text-danger-400' : 'text-warning-600 dark:text-warning-400',
            )}>
              {value}
              {unit && <span className="text-sm font-bold mr-1">{unit}</span>}
            </span>
          </div>
          <div className="p-3 bg-white/60 dark:bg-neutral-800/60 rounded-xl">
            <span className="block text-[10px] font-black text-neutral-400 dark:text-neutral-500 uppercase tracking-wider mb-1">
              المريض
            </span>
            <span className="block text-sm font-bold text-neutral-900 dark:text-neutral-100">{patientName}</span>
            <span className="text-[10px] font-mono text-neutral-500 dark:text-neutral-400">{sampleId}</span>
          </div>
        </div>

        {!acknowledged && (
          <div className="flex gap-3">
            <button
              type="button"
              onClick={handleAcknowledge}
              disabled={acknowledging}
              className={cn(
                'flex-1 px-4 py-2.5 rounded-xl font-bold text-sm transition-all',
                'focus:outline-none focus-visible:ring-4',
                severityColor === 'danger'
                  ? 'bg-danger-500 text-white hover:bg-danger-600 focus-visible:ring-danger-200'
                  : 'bg-warning-500 text-white hover:bg-warning-600 focus-visible:ring-warning-200',
                'disabled:opacity-50',
              )}
            >
              {acknowledging ? 'جاري...' : 'إقرار الاستلام'}
            </button>
            {onCallPhysician && (
              <button
                type="button"
                onClick={onCallPhysician}
                className="px-4 py-2.5 bg-white dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 rounded-xl font-bold text-sm hover:bg-neutral-50 dark:hover:bg-neutral-700 transition-all border-2 border-neutral-200 dark:border-neutral-600"
              >
                اتصل بالطبيب
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
