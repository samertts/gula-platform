import { cn } from '@gula/ui-platform';
import type { ShiftHandover } from '@/utils/types';
import { getShiftArabic } from '@/utils/routes';

interface ShiftSummaryProps {
  handover: ShiftHandover;
  onEdit?: () => void;
  onShare?: () => void;
}

export function ShiftSummary({ handover, onEdit, onShare }: ShiftSummaryProps) {
  return (
    <div className="bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700 overflow-hidden">
      <div className="bg-primary-500 p-4 text-white">
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-bold">تسليم الوردية</h3>
          <span className="text-xs bg-white/20 px-2 py-0.5 rounded-lg font-bold">
            {getShiftArabic(handover.shift)}
          </span>
        </div>
        <p className="text-xs text-white/70">
          {new Date(handover.date).toLocaleDateString('ar-IQ', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
        </p>
      </div>

      <div className="p-4 space-y-4">
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'المرضى', value: handover.totalPatients, color: 'text-primary-600' },
            { label: 'قبول', value: handover.admissions, color: 'text-success-600' },
            { label: 'خروج', value: handover.discharges, color: 'text-warning-600' },
            { label: 'تحويل', value: handover.transfers, color: 'text-blue-600' },
            { label: 'حالات حرجة', value: handover.criticalPatients, color: 'text-danger-600' },
            { label: 'مهام معلقة', value: handover.pendingTasks, color: 'text-warning-600' },
          ].map(s => (
            <div key={s.label} className="bg-neutral-50 dark:bg-neutral-700/50 p-3 rounded-xl text-center">
              <p className={cn('text-xl font-black', s.color)}>{s.value}</p>
              <p className="text-[10px] text-neutral-500 dark:text-neutral-400 mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>

        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-neutral-500 dark:text-neutral-400">الممرض المسؤول</span>
            <span className="font-bold text-neutral-700 dark:text-neutral-300">{handover.nurseInCharge}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-neutral-500 dark:text-neutral-400">تم التسليم إلى</span>
            <span className="font-bold text-neutral-700 dark:text-neutral-300">{handover.handoverTo}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-neutral-500 dark:text-neutral-400">الجناح</span>
            <span className="font-bold text-neutral-700 dark:text-neutral-300">{handover.ward}</span>
          </div>
        </div>

        {handover.notes && (
          <div className="bg-neutral-50 dark:bg-neutral-700/50 p-3 rounded-xl">
            <p className="text-xs font-bold text-neutral-600 dark:text-neutral-400 mb-1">ملاحظات الوردية</p>
            <p className="text-sm text-neutral-700 dark:text-neutral-300">{handover.notes}</p>
          </div>
        )}

        {handover.incidents.length > 0 && (
          <div>
            <p className="text-xs font-bold text-danger-600 dark:text-danger-400 mb-2">
              الحوادث ({handover.incidents.length})
            </p>
            <div className="space-y-1.5">
              {handover.incidents.map((inc, i) => (
                <div key={i} className="flex items-start gap-2 text-sm text-neutral-700 dark:text-neutral-300">
                  <span className="text-danger-500 shrink-0 mt-0.5">•</span>
                  <span>{inc}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex gap-3 pt-2 border-t border-neutral-100 dark:border-neutral-700">
          {onEdit && (
            <button
              type="button"
              onClick={onEdit}
              className="flex-1 py-2 text-sm font-bold bg-neutral-100 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-300 rounded-xl hover:bg-neutral-200 transition-colors"
            >
              تعديل
            </button>
          )}
          {onShare && (
            <button
              type="button"
              onClick={onShare}
              className="flex-1 py-2 text-sm font-bold bg-primary-500 text-white rounded-xl hover:bg-primary-600 transition-colors"
            >
              مشاركة التقرير
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
