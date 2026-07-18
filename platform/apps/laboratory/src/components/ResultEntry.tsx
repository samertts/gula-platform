import { useState, useCallback } from 'react';
import { cn } from '@gula/ui-platform';
import type { TestResult, ResultFlag } from '@/utils/types';

interface ResultEntryProps {
  result?: Partial<TestResult>;
  onSave: (data: Partial<TestResult>) => void;
  onCancel?: () => void;
  readOnly?: boolean;
  className?: string;
}

const flagOptions: { value: ResultFlag; label: string; color: string }[] = [
  { value: 'normal', label: 'طبيعي', color: 'text-success-600 bg-success-50 dark:bg-success-900/30 dark:text-success-400' },
  { value: 'high', label: 'مرتفع', color: 'text-warning-600 bg-warning-50 dark:bg-warning-900/30 dark:text-warning-400' },
  { value: 'low', label: 'منخفض', color: 'text-warning-600 bg-warning-50 dark:bg-warning-900/30 dark:text-warning-400' },
  { value: 'critical_high', label: 'مرتفع حرج', color: 'text-danger-600 bg-danger-50 dark:bg-danger-900/30 dark:text-danger-400' },
  { value: 'critical_low', label: 'منخفض حَرِج', color: 'text-danger-600 bg-danger-50 dark:bg-danger-900/30 dark:text-danger-400' },
  { value: 'panic', label: 'خطير', color: 'text-danger-600 bg-danger-50 dark:bg-danger-900/30 dark:text-danger-400 animate-pulse' },
  { value: 'invalid', label: 'غير صالح', color: 'text-neutral-500 bg-neutral-100 dark:bg-neutral-700 dark:text-neutral-400' },
];

export function ResultEntry({
  result = {},
  onSave,
  onCancel,
  readOnly = false,
  className,
}: ResultEntryProps) {
  const [value, setValue] = useState(result.value || '');
  const [flag, setFlag] = useState<ResultFlag>(result.flag || 'normal');
  const [notes, setNotes] = useState(result.notes || '');
  const [method, setMethod] = useState(result.method || '');
  const [saving, setSaving] = useState(false);

  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      const numericValue = parseFloat(value);
      await onSave({
        value,
        numericValue: isNaN(numericValue) ? undefined : numericValue,
        flag,
        notes,
        method: method || undefined,
      });
    } finally {
      setSaving(false);
    }
  }, [value, flag, notes, method, onSave]);

  return (
    <div className={cn('space-y-5', className)}>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400">
            القيمة
          </label>
          <input
            type="text"
            value={value}
            onChange={e => setValue(e.target.value)}
            readOnly={readOnly}
            placeholder={result.unit ? `مثال: 5.2 ${result.unit}` : 'أدخل القيمة'}
            className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-lg font-bold text-neutral-900 dark:text-neutral-100 focus:border-primary-500 dark:focus:border-primary-400 focus:outline-none transition-colors"
            dir="auto"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400">
            الوحدة
          </label>
          <div className="px-4 py-3 bg-neutral-50 dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm font-medium text-neutral-600 dark:text-neutral-400">
            {result.unit || '---'}
          </div>
        </div>
      </div>

      {result.referenceLow !== undefined && result.referenceHigh !== undefined && (
        <div className="px-4 py-3 bg-neutral-50 dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700">
          <span className="text-xs font-bold text-neutral-500 dark:text-neutral-400">
            النطاق المرجعي: {result.referenceLow} - {result.referenceHigh} {result.unit}
          </span>
        </div>
      )}

      <div className="space-y-2">
        <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400">
          العلم (Flag)
        </label>
        <div className="flex flex-wrap gap-2">
          {flagOptions.map(opt => (
            <button
              key={opt.value}
              type="button"
              onClick={() => !readOnly && setFlag(opt.value)}
              disabled={readOnly}
              className={cn(
                'px-3 py-1.5 rounded-xl text-xs font-bold transition-all border-2',
                flag === opt.value
                  ? `${opt.color} border-current`
                  : 'border-transparent text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-700 dark:text-neutral-400',
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400">
          طريقة التحليل
        </label>
        <input
          type="text"
          value={method}
          onChange={e => setMethod(e.target.value)}
          readOnly={readOnly}
          placeholder="الطريقة المستخدمة"
          className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm font-medium focus:border-primary-500 dark:focus:border-primary-400 focus:outline-none transition-colors dark:text-neutral-100"
        />
      </div>

      <div className="space-y-2">
        <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400">
          ملاحظات
        </label>
        <textarea
          value={notes}
          onChange={e => setNotes(e.target.value)}
          readOnly={readOnly}
          rows={3}
          placeholder="أي ملاحظات إضافية..."
          className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm font-medium focus:border-primary-500 dark:focus:border-primary-400 focus:outline-none transition-colors resize-none dark:text-neutral-100"
        />
      </div>

      {!readOnly && (
        <div className="flex gap-3 pt-2">
          <button
            type="button"
            onClick={handleSave}
            disabled={saving || !value}
            className={cn(
              'flex-1 px-6 py-3 bg-primary-500 text-white rounded-xl font-bold text-sm hover:bg-primary-600 active:bg-primary-700 transition-colors',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'focus:outline-none focus-visible:ring-4 focus-visible:ring-primary-200',
            )}
          >
            {saving ? (
              <span className="inline-flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                جاري الحفظ...
              </span>
            ) : (
              'حفظ النتيجة'
            )}
          </button>
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-6 py-3 bg-neutral-100 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-300 rounded-xl font-bold text-sm hover:bg-neutral-200 dark:hover:bg-neutral-600 transition-colors"
            >
              إلغاء
            </button>
          )}
        </div>
      )}
    </div>
  );
}
