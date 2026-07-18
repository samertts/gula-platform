import { useState, useCallback } from 'react';
import { cn } from '@gula/ui-platform';

interface BatchItem {
  id: string;
  label: string;
  subtitle?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'skipped';
  error?: string;
  data?: Record<string, unknown>;
}

interface BatchProcessorProps {
  title: string;
  items: BatchItem[];
  onProcessAll: () => Promise<void>;
  onProcessSingle: (id: string) => Promise<void>;
  onRetryFailed?: () => Promise<void>;
  className?: string;
}

export function BatchProcessor({
  title,
  items,
  onProcessAll,
  onProcessSingle,
  onRetryFailed,
  className,
}: BatchProcessorProps) {
  const [isProcessing, setIsProcessing] = useState(false);

  const pending = items.filter(i => i.status === 'pending').length;
  const completed = items.filter(i => i.status === 'completed').length;
  const failed = items.filter(i => i.status === 'failed').length;
  const progress = items.length > 0 ? Math.round((completed / items.length) * 100) : 0;

  const handleProcessAll = useCallback(async () => {
    setIsProcessing(true);
    try {
      await onProcessAll();
    } finally {
      setIsProcessing(false);
    }
  }, [onProcessAll]);

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">{title}</h3>
          <p className="text-sm text-neutral-500 dark:text-neutral-400">
            {items.length} عنصر - {completed} مكتمل - {failed} فاشل - {pending} معلق
          </p>
        </div>

        <div className="flex gap-2">
          {failed > 0 && onRetryFailed && (
            <button
              type="button"
              onClick={onRetryFailed}
              disabled={isProcessing}
              className="px-4 py-2 bg-warning-500 text-white rounded-xl font-bold text-xs hover:bg-warning-600 transition-colors disabled:opacity-50"
            >
              إعادة الفاشلة
            </button>
          )}
          <button
            type="button"
            onClick={handleProcessAll}
            disabled={isProcessing || pending === 0}
            className="px-4 py-2 bg-primary-500 text-white rounded-xl font-bold text-xs hover:bg-primary-600 transition-colors disabled:opacity-50"
          >
            {isProcessing ? 'جاري المعالجة...' : `معالجة الكل (${pending})`}
          </button>
        </div>
      </div>

      <div className="w-full bg-neutral-100 dark:bg-neutral-700 rounded-full h-2 overflow-hidden">
        <div
          className={cn(
            'h-full rounded-full transition-all duration-500',
            progress === 100 ? 'bg-success-500' : 'bg-primary-500',
          )}
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="space-y-2 max-h-96 overflow-y-auto">
        {items.map(item => (
          <div
            key={item.id}
            className={cn(
              'flex items-center gap-3 p-3 rounded-xl border transition-all bg-white dark:bg-neutral-800',
              item.status === 'completed' && 'border-success-200 dark:border-success-700 bg-success-50/30 dark:bg-success-900/10',
              item.status === 'failed' && 'border-danger-200 dark:border-danger-700 bg-danger-50/30 dark:bg-danger-900/10',
              item.status === 'processing' && 'border-primary-200 dark:border-primary-700 bg-primary-50/30 dark:bg-primary-900/10',
              item.status === 'pending' && 'border-neutral-200 dark:border-neutral-700',
            )}
          >
            <div className="flex-1 min-w-0">
              <p className="text-sm font-bold text-neutral-900 dark:text-neutral-100 truncate">
                {item.label}
              </p>
              {item.subtitle && (
                <p className="text-xs text-neutral-500 dark:text-neutral-400 truncate">{item.subtitle}</p>
              )}
              {item.error && (
                <p className="text-xs text-danger-500 mt-0.5">{item.error}</p>
              )}
            </div>

            <div className="flex items-center gap-2 shrink-0">
              {item.status === 'completed' && (
                <span className="w-6 h-6 rounded-full bg-success-100 dark:bg-success-900/30 text-success-600 dark:text-success-400 flex items-center justify-center">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </span>
              )}
              {item.status === 'failed' && (
                <button
                  type="button"
                  onClick={() => onProcessSingle(item.id)}
                  className="w-6 h-6 rounded-full bg-danger-100 dark:bg-danger-900/30 text-danger-600 dark:text-danger-400 flex items-center justify-center hover:bg-danger-200 dark:hover:bg-danger-900/50 transition-colors"
                  title="إعادة المحاولة"
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <polyline points="23 4 23 10 17 10" /><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
                  </svg>
                </button>
              )}
              {item.status === 'processing' && (
                <div className="w-5 h-5 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
              )}
              {item.status === 'pending' && (
                <button
                  type="button"
                  onClick={() => onProcessSingle(item.id)}
                  className="px-3 py-1 text-xs font-bold text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/30 rounded-lg transition-colors"
                >
                  تنفيذ
                </button>
              )}
              {item.status === 'skipped' && (
                <span className="text-xs text-neutral-400">تم التخطي</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
