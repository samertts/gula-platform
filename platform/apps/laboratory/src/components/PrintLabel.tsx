import { useState } from 'react';
import { cn } from '@gula/ui-platform';
import type { BarcodeLabel } from '@/utils/types';

interface PrintLabelProps {
  label: BarcodeLabel;
  onPrint?: (label: BarcodeLabel, copies: number) => void;
  onClose?: () => void;
  className?: string;
}

export function PrintLabel({ label, onPrint, onClose, className }: PrintLabelProps) {
  const [copies, setCopies] = useState(1);

  const renderBarcode = (code: string) => {
    const lines: boolean[] = [];
    const chars = code.split('');
    for (const char of chars) {
      const byte = char.charCodeAt(0);
      for (let i = 0; i < 8; i++) {
        lines.push((byte & (1 << (7 - i))) !== 0);
      }
    }

    return (
      <div className="flex items-end h-12 overflow-hidden" dir="ltr">
        {lines.map((filled, i) => (
          <div
            key={i}
            className={cn(
              'w-[1.5px]',
              filled ? 'bg-neutral-900 dark:bg-neutral-100' : 'bg-transparent',
            )}
            style={{ height: filled ? '100%' : '30%' }}
          />
        ))}
      </div>
    );
  };

  return (
    <div className={cn('space-y-4', className)}>
      <div className="bg-white dark:bg-neutral-800 rounded-2xl border-2 border-neutral-200 dark:border-neutral-700 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <span className="text-xs font-bold text-neutral-400 dark:text-neutral-500 uppercase tracking-wider">
            نموذج الطباعة
          </span>
          <span className="text-[10px] font-mono text-neutral-500 dark:text-neutral-400">
            {label.barcode}
          </span>
        </div>

        <div className="border-2 border-dashed border-neutral-300 dark:border-neutral-600 rounded-xl p-4 space-y-3">
          <div className="text-center">
            <span className="text-2xl font-black text-neutral-900 dark:text-neutral-100">
              {label.patientName}
            </span>
          </div>

          <div className="flex justify-center gap-8 text-xs">
            <div className="text-center">
              <span className="block text-neutral-400 dark:text-neutral-500 text-[9px] font-bold uppercase tracking-wider">
                رقم العينة
              </span>
              <span className="font-mono font-bold text-neutral-900 dark:text-neutral-100">
                {label.sampleId}
              </span>
            </div>
            <div className="text-center">
              <span className="block text-neutral-400 dark:text-neutral-500 text-[9px] font-bold uppercase tracking-wider">
                معرف المريض
              </span>
              <span className="font-mono font-bold text-neutral-900 dark:text-neutral-100">
                {label.patientId}
              </span>
            </div>
          </div>

          {renderBarcode(label.barcode)}

          <div className="text-center">
            <span className="font-mono text-[10px] text-neutral-600 dark:text-neutral-400">
              {label.barcode}
            </span>
          </div>

          <div className="flex justify-center gap-4 text-[9px] text-neutral-500 dark:text-neutral-400">
            <span>{specimenTypeArabic(label.specimenType)}</span>
            {label.container && <span>{label.container}</span>}
            {label.volume && <span>{label.volume} مل</span>}
          </div>

          {label.tests.length > 0 && (
            <div className="flex flex-wrap justify-center gap-1">
              {label.tests.map(test => (
                <span key={test} className="px-1.5 py-0.5 bg-neutral-100 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-300 rounded text-[8px]">
                  {test}
                </span>
              ))}
            </div>
          )}

          {label.notes && (
            <p className="text-center text-[8px] text-neutral-400 italic">{label.notes}</p>
          )}
        </div>

        <div className="flex items-center justify-between mt-4">
          <div className="flex items-center gap-2">
            <label className="text-xs font-medium text-neutral-600 dark:text-neutral-400">
              عدد النسخ:
            </label>
            <div className="flex items-center border-2 border-neutral-200 dark:border-neutral-600 rounded-xl">
              <button
                type="button"
                onClick={() => setCopies(Math.max(1, copies - 1))}
                className="px-3 py-1.5 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-700 transition-colors"
              >
                -
              </button>
              <span className="px-3 py-1.5 text-sm font-bold text-neutral-900 dark:text-neutral-100 min-w-[40px] text-center">
                {copies}
              </span>
              <button
                type="button"
                onClick={() => setCopies(Math.min(10, copies + 1))}
                className="px-3 py-1.5 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-700 transition-colors"
              >
                +
              </button>
            </div>
          </div>

          <div className="flex gap-2">
            {onClose && (
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-xs font-bold text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-700 rounded-xl transition-colors"
              >
                إغلاق
              </button>
            )}
            <button
              type="button"
              onClick={() => onPrint?.(label, copies)}
              disabled={copies < 1}
              className="px-5 py-2 bg-primary-500 text-white rounded-xl font-bold text-xs hover:bg-primary-600 transition-colors disabled:opacity-50"
            >
              طباعة ({copies})
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function specimenTypeArabic(type: string): string {
  const labels: Record<string, string> = {
    whole_blood: 'دم كامل', serum: 'مصل', plasma: 'بلازما', urine: 'بول',
    stool: 'براز', csf: 'سائل نخاعي', sputum: 'بلغم', swab: 'مسحة',
    tissue: 'نسيج', bone_marrow: 'نخاع عظمي', amniotic: 'سائل أمنيوسي',
    pleural: 'سائل جنبي', pericardial: 'سائل تأموري', peritoneal: 'سائل صفاقي',
    synovial: 'سائل زليلي', saliva: 'لعاب', hair: 'شعر', nail: 'ظفر', other: 'أخرى',
  };
  return labels[type] || type;
}
