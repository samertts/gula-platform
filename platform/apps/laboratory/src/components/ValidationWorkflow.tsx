import { useState, useCallback } from 'react';
import { cn } from '@gula/ui-platform';
import type { TestResult } from '@/utils/types';

interface ValidationWorkflowProps {
  results: TestResult[];
  onValidate: (ids: string[], action: 'approve' | 'reject', notes?: string) => Promise<void>;
  onReviewSingle: (result: TestResult) => void;
  className?: string;
}

export function ValidationWorkflow({
  results,
  onValidate,
  onReviewSingle,
  className,
}: ValidationWorkflowProps) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [view, setView] = useState<'all' | 'flagged' | 'pending'>('pending');
  const [batchNotes, setBatchNotes] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const filteredResults = results.filter(r => {
    if (view === 'flagged') return r.flag !== 'normal';
    if (view === 'pending') return r.status === 'pending' || r.status === 'in_progress';
    return true;
  });

  const toggleSelect = useCallback((id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const toggleSelectAll = useCallback(() => {
    if (selectedIds.size === filteredResults.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredResults.map(r => r.id)));
    }
  }, [filteredResults, selectedIds]);

  const handleBatchValidate = useCallback(async (action: 'approve' | 'reject') => {
    if (selectedIds.size === 0) return;
    setIsProcessing(true);
    try {
      await onValidate(Array.from(selectedIds), action, batchNotes);
      setSelectedIds(new Set());
      setBatchNotes('');
    } finally {
      setIsProcessing(false);
    }
  }, [selectedIds, onValidate, batchNotes]);

  const flagLabel = (flag: string) => {
    const labels: Record<string, string> = {
      normal: 'طبيعي', high: 'مرتفع', low: 'منخفض',
      critical_high: 'مرتفع حرج', critical_low: 'منخفض حرج',
      panic: 'خطير', delta_fail: 'فشل دلتا', invalid: 'غير صالح',
    };
    return labels[flag] || flag;
  };

  const flagColor = (flag: string) => {
    if (flag === 'normal') return 'text-success-600 bg-success-50 dark:bg-success-900/30 dark:text-success-400';
    if (flag === 'critical_high' || flag === 'critical_low' || flag === 'panic') return 'text-danger-600 bg-danger-50 dark:bg-danger-900/30 dark:text-danger-400';
    if (flag === 'high' || flag === 'low') return 'text-warning-600 bg-warning-50 dark:bg-warning-900/30 dark:text-warning-400';
    return 'text-neutral-500 bg-neutral-100 dark:bg-neutral-700 dark:text-neutral-400';
  };

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          {(['pending', 'flagged', 'all'] as const).map(v => (
            <button
              key={v}
              type="button"
              onClick={() => setView(v)}
              className={cn(
                'px-4 py-1.5 rounded-xl text-xs font-bold transition-all',
                view === v
                  ? 'bg-primary-500 text-white shadow-sm'
                  : 'bg-neutral-100 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200 dark:hover:bg-neutral-600',
              )}
            >
              {v === 'pending' ? 'قيد الانتظار' : v === 'flagged' ? 'ملحوظ' : 'الكل'}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 text-sm text-neutral-500 dark:text-neutral-400">
          <span>مختار: {selectedIds.size}</span>
        </div>
      </div>

      <div className="space-y-2">
        {filteredResults.map(result => (
          <div
            key={result.id}
            className={cn(
              'rounded-xl border-2 p-4 transition-all bg-white dark:bg-neutral-800',
              selectedIds.has(result.id)
                ? 'border-primary-500 shadow-sm'
                : 'border-neutral-200 dark:border-neutral-700 hover:border-neutral-300 dark:hover:border-neutral-600',
            )}
          >
            <div className="flex items-start gap-3">
              <input
                type="checkbox"
                checked={selectedIds.has(result.id)}
                onChange={() => toggleSelect(result.id)}
                className="mt-1 w-4 h-4 rounded border-neutral-300 text-primary-500 focus:ring-primary-400"
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-bold text-neutral-900 dark:text-neutral-100">
                    {result.testName}
                  </span>
                  <span className={cn('px-1.5 py-0.5 rounded text-[9px] font-bold', flagColor(result.flag))}>
                    {flagLabel(result.flag)}
                  </span>
                  {result.version > 1 && (
                    <span className="text-[9px] text-warning-500 font-bold">
                      v{result.version}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-4 text-xs text-neutral-500 dark:text-neutral-400">
                  <span className="font-bold text-neutral-900 dark:text-neutral-100">
                    {result.value} {result.unit}
                  </span>
                  <span>النطاق: {result.referenceRange}</span>
                  {result.instrument && <span>جهاز: {result.instrument}</span>}
                </div>

                {result.notes && (
                  <p className="mt-1 text-xs text-neutral-400 italic">{result.notes}</p>
                )}
              </div>

              <button
                type="button"
                onClick={() => onReviewSingle(result)}
                className="px-3 py-1.5 text-xs font-bold text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/30 rounded-xl transition-colors shrink-0"
              >
                مراجعة
              </button>
            </div>
          </div>
        ))}

        {filteredResults.length === 0 && (
          <div className="text-center py-12 text-neutral-400 dark:text-neutral-500 text-sm">
            لا توجد نتائج للمراجعة
          </div>
        )}
      </div>

      {selectedIds.size > 0 && (
        <div className="sticky bottom-4 p-4 bg-white dark:bg-neutral-800 rounded-2xl border-2 border-primary-200 dark:border-primary-700 shadow-xl">
          <div className="space-y-3">
            <textarea
              value={batchNotes}
              onChange={e => setBatchNotes(e.target.value)}
              placeholder="ملاحظات للدفعة (اختياري)..."
              rows={2}
              className="w-full px-4 py-2.5 bg-neutral-50 dark:bg-neutral-700 border border-neutral-200 dark:border-neutral-600 rounded-xl text-sm focus:outline-none focus:border-primary-400 resize-none dark:text-neutral-100"
            />
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => handleBatchValidate('approve')}
                disabled={isProcessing}
                className="flex-1 px-6 py-3 bg-success-500 text-white rounded-xl font-bold text-sm hover:bg-success-600 transition-colors disabled:opacity-50"
              >
                {isProcessing ? 'جاري...' : `اعتماد (${selectedIds.size})`}
              </button>
              <button
                type="button"
                onClick={() => handleBatchValidate('reject')}
                disabled={isProcessing}
                className="px-6 py-3 bg-danger-500 text-white rounded-xl font-bold text-sm hover:bg-danger-600 transition-colors disabled:opacity-50"
              >
                رفض
              </button>
              <button
                type="button"
                onClick={() => setSelectedIds(new Set())}
                className="px-4 py-3 bg-neutral-100 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-300 rounded-xl font-bold text-sm hover:bg-neutral-200 dark:hover:bg-neutral-600 transition-colors"
              >
                إلغاء التحديد
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
