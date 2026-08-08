import { cn } from '@gula/ui-platform';
import type { Prescription } from '../types';

interface MedicationReminderProps {
  prescription: Prescription;
  onMarkTaken?: (id: string) => void;
  className?: string;
}

export function MedicationReminder({ prescription, onMarkTaken, className }: MedicationReminderProps) {
  const isExpired = new Date(prescription.expiryDate) < new Date();
  const isActive = prescription.status === 'active';

  return (
    <div className={cn(
      'flex items-start gap-4 p-4 rounded-2xl border',
      isActive && !isExpired
        ? 'bg-white dark:bg-neutral-800 border-neutral-200 dark:border-neutral-700'
        : 'bg-neutral-50 dark:bg-neutral-800/50 border-neutral-100 dark:border-neutral-700/50',
      className,
    )}>
      <div className={cn(
        'w-12 h-12 rounded-2xl flex items-center justify-center shrink-0',
        isActive && !isExpired
          ? 'bg-success-50 dark:bg-success-900/20 text-success-600 dark:text-success-400'
          : 'bg-neutral-100 dark:bg-neutral-700 text-neutral-400',
      )}>
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <h4 className="font-bold text-neutral-900 dark:text-neutral-50 text-sm truncate">
            {prescription.medicationName}
          </h4>
          {onMarkTaken && isActive && !isExpired && (
            <button
              onClick={() => onMarkTaken(prescription.id)}
              className="shrink-0 px-3 py-1 bg-success-500 text-white rounded-xl text-[10px] font-bold hover:bg-success-600 transition-colors"
            >
              تم
            </button>
          )}
        </div>

        <div className="flex items-center flex-wrap gap-x-3 gap-y-1 mt-1">
          <span className="text-[11px] text-neutral-500">{prescription.dosage}</span>
          <span className="w-1 h-1 rounded-full bg-neutral-300" />
          <span className="text-[11px] text-neutral-500">{prescription.frequency}</span>
        </div>

        <div className="flex items-center gap-3 mt-1.5">
          <span className="text-[10px] text-neutral-400">وصف: {prescription.prescribedBy}</span>
          {prescription.refills > 0 && (
            <>
              <span className="w-1 h-1 rounded-full bg-neutral-300" />
              <span className="text-[10px] text-neutral-400">تبقى {prescription.refills} إعادة</span>
            </>
          )}
        </div>

        <div className="flex items-center gap-2 mt-2">
          {isExpired && (
            <span className="px-2 py-0.5 bg-danger-50 dark:bg-danger-900/20 text-danger-600 dark:text-danger-400 rounded-lg text-[9px] font-bold">
              منتهي الصلاحية
            </span>
          )}
          {!isActive && (
            <span className="px-2 py-0.5 bg-neutral-100 dark:bg-neutral-700 text-neutral-500 rounded-lg text-[9px] font-bold">
              {prescription.status === 'completed' ? 'مكتمل' : 'ملغي'}
            </span>
          )}
          <span className="text-[10px] text-neutral-400">
            الكمية: {prescription.quantity}
          </span>
          {prescription.pharmacy && (
            <>
              <span className="w-1 h-1 rounded-full bg-neutral-300" />
              <span className="text-[10px] text-neutral-400">{prescription.pharmacy}</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
