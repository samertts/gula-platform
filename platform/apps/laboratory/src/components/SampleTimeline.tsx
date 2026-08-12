import { cn } from '@gula/ui-platform';

interface TimelineEvent {
  status: string;
  timestamp: string;
  by?: string;
  notes?: string;
}

interface SampleTimelineProps {
  events: TimelineEvent[];
  currentStatus?: string;
  className?: string;
}

const statusLabels: Record<string, string> = {
  ordered: 'تم الطلب',
  registered: 'تم التسجيل',
  collected: 'تم الجمع',
  transporting: 'قيد النقل',
  received: 'تم الاستلام',
  accepted: 'مقبول',
  rejected: 'مرفوض',
  aliquoted: 'تم التقسيم',
  processing: 'قيد المعالجة',
  analyzing: 'قيد التحليل',
  analyzed: 'تم التحليل',
  verified: 'تم التحقق',
  validated: 'معتمد',
  released: 'تم النشر',
  archived: 'مؤرشف',
  disposed: 'تم التخلص',
};

export function SampleTimeline({
  events,
  currentStatus,
  className,
}: SampleTimelineProps) {
  if (events.length === 0) {
    return (
      <div className={cn('text-center py-8 text-neutral-400 dark:text-neutral-500 text-sm', className)}>
        لا توجد أحداث في الجدول الزمني
      </div>
    );
  }

  return (
    <div className={cn('relative', className)}>
      <div className="absolute right-4 top-0 bottom-0 w-0.5 bg-neutral-200 dark:bg-neutral-700" />

      <ol className="space-y-0">
        {events.map((event, index) => {
          const isCurrent = event.status === currentStatus;
          const isLast = index === events.length - 1;
          const isRejected = event.status === 'rejected';

          return (
            <li key={index} className="relative pb-8 last:pb-0">
              <div className="flex items-start gap-4">
                <div className="relative z-10 flex-shrink-0 mt-1">
                  <div className={cn(
                    'w-8 h-8 rounded-full border-2 flex items-center justify-center',
                    isCurrent
                      ? 'bg-primary-500 border-primary-500 text-white shadow-md shadow-primary-200 dark:shadow-primary-900'
                      : isRejected
                        ? 'bg-danger-50 border-danger-300 text-danger-500 dark:bg-danger-900/30 dark:border-danger-700 dark:text-danger-400'
                        : 'bg-white dark:bg-neutral-800 border-neutral-300 dark:border-neutral-600 text-neutral-500 dark:text-neutral-400',
                  )}>
                    {isCurrent ? (
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    ) : isRejected ? (
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                    ) : (
                      <div className="w-2 h-2 rounded-full bg-current" />
                    )}
                  </div>
                </div>

                <div className="flex-1 min-w-0 pt-1">
                  <div className="flex items-center gap-2">
                    <span className={cn(
                      'text-sm font-bold',
                      isCurrent
                        ? 'text-primary-600 dark:text-primary-400'
                        : 'text-neutral-900 dark:text-neutral-100',
                    )}>
                      {statusLabels[event.status] || event.status}
                    </span>
                    {isCurrent && (
                      <span className="px-1.5 py-0.5 bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 rounded text-[8px] font-black uppercase tracking-wider">
                        الحالي
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-3 mt-1 text-[11px] text-neutral-500 dark:text-neutral-400">
                    <span>
                      {new Date(event.timestamp).toLocaleString('ar-IQ', {
                        dateStyle: 'short',
                        timeStyle: 'short',
                      })}
                    </span>
                    {event.by && (
                      <>
                        <span>•</span>
                        <span>{event.by}</span>
                      </>
                    )}
                  </div>

                  {event.notes && (
                    <p className="mt-1.5 text-xs text-neutral-600 dark:text-neutral-400 bg-neutral-50 dark:bg-neutral-700/50 px-3 py-2 rounded-xl">
                      {event.notes}
                    </p>
                  )}
                </div>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
