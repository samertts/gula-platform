import { cn } from '@gula/ui-platform';
import type { HealthRecord } from '../types';

interface HealthTimelineProps {
  records: HealthRecord[];
  className?: string;
}

const typeIcons: Record<string, string> = {
  lab_result: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
  radiology: 'M12 4v16m8-8H4',
  prescription: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
  vaccination: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z',
  diagnosis: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
  procedure: 'M4 6h16M4 10h16M4 14h16M4 18h16',
  visit: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z',
};

const typeColors: Record<string, string> = {
  lab_result: 'bg-indigo-100 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-400',
  radiology: 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400',
  prescription: 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400',
  vaccination: 'bg-cyan-100 text-cyan-600 dark:bg-cyan-900/30 dark:text-cyan-400',
  diagnosis: 'bg-rose-100 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400',
  procedure: 'bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400',
  visit: 'bg-slate-100 text-slate-600 dark:bg-slate-900/30 dark:text-slate-400',
};

export function HealthTimeline({ records, className }: HealthTimelineProps) {
  if (records.length === 0) {
    return (
      <div className={cn('text-center py-12', className)}>
        <svg className="w-16 h-16 mx-auto text-neutral-300 dark:text-neutral-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p className="text-sm text-neutral-500">لا توجد سجلات طبية حتى الآن</p>
      </div>
    );
  }

  const groupedByDate = records.reduce<Record<string, HealthRecord[]>>((acc, record) => {
    const date = new Date(record.date).toLocaleDateString('ar-IQ', { year: 'numeric', month: 'long', day: 'numeric' });
    if (!acc[date]) acc[date] = [];
    acc[date].push(record);
    return acc;
  }, {});

  return (
    <div className={cn('space-y-8', className)}>
      {Object.entries(groupedByDate).map(([date, items]) => (
        <div key={date}>
          <div className="flex items-center gap-3 mb-4">
            <div className="h-px flex-1 bg-neutral-200 dark:bg-neutral-700" />
            <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest shrink-0">
              {date}
            </span>
            <div className="h-px flex-1 bg-neutral-200 dark:bg-neutral-700" />
          </div>

          <div className="space-y-3">
            {items.map((record, index) => (
              <div key={record.id} className="relative flex gap-4">
                {index < items.length - 1 && (
                  <div className="absolute top-10 bottom-0 right-[19px] w-0.5 bg-neutral-100 dark:bg-neutral-700" />
                )}
                <div className={cn('w-10 h-10 rounded-2xl flex items-center justify-center shrink-0', typeColors[record.type] || 'bg-neutral-100 text-neutral-500')}>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={typeIcons[record.type] || typeIcons.visit} />
                  </svg>
                </div>
                <div className="min-w-0 flex-1 pb-3">
                  <div className="bg-white dark:bg-neutral-800 rounded-2xl p-4 border border-neutral-200 dark:border-neutral-700 shadow-sm">
                    <h4 className="font-bold text-neutral-900 dark:text-neutral-50 text-sm">{record.title}</h4>
                    {record.description && (
                      <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">{record.description}</p>
                    )}
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-[10px] text-neutral-400">{record.provider}</span>
                      <span className="w-1 h-1 rounded-full bg-neutral-300" />
                      <span className="text-[10px] text-neutral-400">{record.facilityName}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
