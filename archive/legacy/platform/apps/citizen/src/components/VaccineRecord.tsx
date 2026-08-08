import { cn } from '@gula/ui-platform';
import type { Vaccination } from '../types';

interface VaccineRecordProps {
  vaccination: Vaccination;
  className?: string;
}

export function VaccineRecord({ vaccination, className }: VaccineRecordProps) {
  const isCompleted = vaccination.status === 'completed';
  const isOverdue = vaccination.status === 'overdue';
  const hasNextDose = !!vaccination.nextDoseDate;

  return (
    <div className={cn('flex items-start gap-4', className)}>
      <div className="relative shrink-0">
        <div className={cn(
          'w-10 h-10 rounded-2xl flex items-center justify-center',
          isCompleted
            ? 'bg-success-100 dark:bg-success-900/30 text-success-600 dark:text-success-400'
            : isOverdue
              ? 'bg-danger-100 dark:bg-danger-900/30 text-danger-600 dark:text-danger-400'
              : 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400',
        )}>
          {isCompleted ? (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
          )}
        </div>
        <div className="absolute -bottom-1 -end-1">
          <div className={cn(
            'w-4 h-4 rounded-full flex items-center justify-center text-white text-[8px] font-black',
            isCompleted ? 'bg-success-500' : isOverdue ? 'bg-danger-500' : 'bg-primary-500',
          )}>
            {vaccination.doseNumber}
          </div>
        </div>
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <h4 className="font-bold text-neutral-900 dark:text-neutral-50 text-sm">{vaccination.vaccineName}</h4>
          <span className={cn(
            'px-1.5 py-0.5 rounded text-[9px] font-bold',
            isCompleted
              ? 'bg-success-50 text-success-600 dark:bg-success-900/20 dark:text-success-400'
              : isOverdue
                ? 'bg-danger-50 text-danger-600 dark:bg-danger-900/20 dark:text-danger-400'
                : 'bg-primary-50 text-primary-600 dark:bg-primary-900/20 dark:text-primary-400',
          )}>
            {isCompleted ? 'مكتمل' : isOverdue ? 'متأخر' : 'مجدول'}
          </span>
        </div>
        <p className="text-[11px] text-neutral-500 mt-0.5">
          الجرعة {vaccination.doseNumber} من {vaccination.totalDoses}
        </p>
        <div className="flex items-center gap-3 mt-1.5">
          <span className="text-[10px] text-neutral-400">
            {new Date(vaccination.administeredDate).toLocaleDateString('ar-IQ')}
          </span>
          {vaccination.administeredBy && (
            <>
              <span className="w-1 h-1 rounded-full bg-neutral-300" />
              <span className="text-[10px] text-neutral-400">{vaccination.administeredBy}</span>
            </>
          )}
        </div>
        {hasNextDose && (
          <div className={cn(
            'mt-2 px-3 py-1.5 rounded-xl text-[10px] font-bold flex items-center gap-1.5',
            isOverdue
              ? 'bg-danger-50 text-danger-600 dark:bg-danger-900/20 dark:text-danger-400'
              : 'bg-primary-50 text-primary-600 dark:bg-primary-900/20 dark:text-primary-400',
          )}>
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            الجرعة القادمة: {new Date(vaccination.nextDoseDate!).toLocaleDateString('ar-IQ')}
          </div>
        )}
      </div>
    </div>
  );
}
