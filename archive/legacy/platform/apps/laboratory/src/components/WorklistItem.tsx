import { cn } from '@gula/ui-platform';
import type { Sample, Priority } from '@/utils/types';

interface WorklistItemProps {
  sample: Sample;
  onSelect?: (sample: Sample) => void;
  onStart?: (sample: Sample) => void;
  selected?: boolean;
  compact?: boolean;
  className?: string;
}

const priorityConfig: Record<Priority, { label: string; color: string }> = {
  stat: { label: 'STAT', color: 'bg-danger-500 text-white' },
  urgent: { label: 'عاجل', color: 'bg-warning-500 text-white' },
  routine: { label: 'روتين', color: 'bg-neutral-100 text-neutral-600 dark:bg-neutral-700 dark:text-neutral-300' },
};

const statusConfig: Record<string, { label: string; color: string }> = {
  ordered: { label: 'مطلوب', color: 'bg-neutral-100 text-neutral-600 dark:bg-neutral-700 dark:text-neutral-300' },
  registered: { label: 'مسجل', color: 'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' },
  collected: { label: 'مجموع', color: 'bg-primary-50 text-primary-600 dark:bg-primary-900/30 dark:text-primary-400' },
  transporting: { label: 'قيد النقل', color: 'bg-warning-50 text-warning-600 dark:bg-warning-900/30 dark:text-warning-400' },
  received: { label: 'مستلم', color: 'bg-info-50 text-info-600 dark:bg-info-900/30 dark:text-info-400' },
  accepted: { label: 'مقبول', color: 'bg-success-50 text-success-600 dark:bg-success-900/30 dark:text-success-400' },
  rejected: { label: 'مرفوض', color: 'bg-danger-50 text-danger-600 dark:bg-danger-900/30 dark:text-danger-400' },
  processing: { label: 'قيد المعالجة', color: 'bg-warning-50 text-warning-600 dark:bg-warning-900/30 dark:text-warning-400' },
  analyzing: { label: 'قيد التحليل', color: 'bg-primary-50 text-primary-600 dark:bg-primary-900/30 dark:text-primary-400' },
  analyzed: { label: 'تم التحليل', color: 'bg-success-50 text-success-600 dark:bg-success-900/30 dark:text-success-400' },
  verified: { label: 'تم التحقق', color: 'bg-success-50 text-success-600 dark:bg-success-900/30 dark:text-success-400' },
  validated: { label: 'معتمد', color: 'bg-success-50 text-success-600 dark:bg-success-900/30 dark:text-success-400' },
  released: { label: 'منشور', color: 'bg-neutral-100 text-neutral-600 dark:bg-neutral-700 dark:text-neutral-300' },
};

export function WorklistItem({
  sample,
  onSelect,
  onStart,
  selected,
  compact = false,
  className,
}: WorklistItemProps) {
  const priority = priorityConfig[sample.priority] || priorityConfig.routine;
  const status = statusConfig[sample.status] || { label: sample.status, color: 'bg-neutral-100 text-neutral-600' };

  const timeSinceCreation = () => {
    const diff = Date.now() - new Date(sample.createdAt).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins} د`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours} س`;
    return `${Math.floor(hours / 24)} ي`;
  };

  if (compact) {
    return (
      <button
        type="button"
        onClick={() => onSelect?.(sample)}
        className={cn(
          'w-full text-right p-3 rounded-xl border-2 transition-all',
          'hover:shadow-sm focus:outline-none focus-visible:ring-4 focus-visible:ring-primary-200',
          selected
            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 dark:border-primary-400'
            : 'border-transparent bg-white dark:bg-neutral-800 hover:border-neutral-200 dark:hover:border-neutral-600',
          className,
        )}
      >
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 min-w-0">
            <span className={cn('px-1.5 py-0.5 rounded text-[9px] font-black uppercase tracking-wider shrink-0', priority.color)}>
              {priority.label}
            </span>
            <span className="font-mono text-xs font-bold text-neutral-700 dark:text-neutral-300 truncate">
              {sample.sampleId}
            </span>
          </div>
          <span className="text-[10px] text-neutral-400 dark:text-neutral-500 shrink-0">{timeSinceCreation()}</span>
        </div>
        <div className="flex items-center gap-2 mt-1.5">
          <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100 truncate">
            {sample.patientName}
          </span>
          <span className={cn('px-1.5 py-0.5 rounded text-[8px] font-bold', status.color)}>
            {status.label}
          </span>
        </div>
      </button>
    );
  }

  return (
    <div
      className={cn(
        'rounded-2xl border-2 p-5 transition-all bg-white dark:bg-neutral-800',
        selected ? 'border-primary-500 shadow-md' : 'border-neutral-200 dark:border-neutral-700 hover:border-neutral-300 dark:hover:border-neutral-600 shadow-sm',
        className,
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={cn('px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider', priority.color)}>
              {priority.label}
            </span>
            <span className="font-mono text-xs font-bold text-neutral-500 dark:text-neutral-400">
              {sample.sampleId}
            </span>
            <span className="text-[10px] text-neutral-400 dark:text-neutral-500">
              منذ {timeSinceCreation()}
            </span>
          </div>
          <h4 className="text-base font-bold text-neutral-900 dark:text-neutral-100 truncate">
            {sample.patientName}
          </h4>
          <div className="flex items-center gap-3 mt-1.5">
            <span className="text-xs text-neutral-500 dark:text-neutral-400">
              معرف المريض: {sample.patientId}
            </span>
            {sample.patientPhone && (
              <span className="text-xs text-neutral-500 dark:text-neutral-400" dir="ltr">
                {sample.patientPhone}
              </span>
            )}
          </div>
          <div className="flex flex-wrap gap-1.5 mt-2">
            {sample.tests.slice(0, 3).map(test => (
              <span key={test} className="px-2 py-1 bg-neutral-100 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-300 rounded-lg text-[10px] font-medium">
                {test}
              </span>
            ))}
            {sample.tests.length > 3 && (
              <span className="px-2 py-1 bg-neutral-100 dark:bg-neutral-700 text-neutral-400 dark:text-neutral-500 rounded-lg text-[10px] font-medium">
                +{sample.tests.length - 3}
              </span>
            )}
          </div>
        </div>

        <div className="flex flex-col items-end gap-2 shrink-0">
          {sample.notes && (
            <div className="relative group">
              <span className="text-neutral-400 dark:text-neutral-500 cursor-help">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" /><path d="M12 16v-4M12 8h.01" />
                </svg>
              </span>
              <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 px-3 py-2 bg-neutral-900 dark:bg-neutral-700 text-white text-xs rounded-xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none w-48 text-center whitespace-pre-wrap">
                {sample.notes}
              </div>
            </div>
          )}
          <span className={cn('px-2.5 py-1 rounded-full text-[10px] font-bold', status.color)}>
            {status.label}
          </span>
        </div>
      </div>

      <div className="flex items-center justify-between mt-4 pt-4 border-t border-neutral-100 dark:border-neutral-700">
        <div className="flex items-center gap-2">
          {sample.specimenType && (
            <span className="text-xs text-neutral-500 dark:text-neutral-400">
              {specimenTypeLabel(sample.specimenType)}
            </span>
          )}
          {sample.volume && (
            <span className="text-xs text-neutral-400 dark:text-neutral-500">
              حجم: {sample.volume} مل
            </span>
          )}
        </div>
        <div className="flex gap-2">
          {onSelect && (
            <button
              type="button"
              onClick={() => onSelect(sample)}
              className="px-4 py-1.5 text-xs font-bold text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/30 rounded-xl transition-colors"
            >
              تفاصيل
            </button>
          )}
          {onStart && ['ordered', 'registered', 'collected', 'received', 'accepted'].includes(sample.status) && (
            <button
              type="button"
              onClick={() => onStart(sample)}
              className="px-4 py-1.5 text-xs font-bold bg-primary-500 text-white hover:bg-primary-600 rounded-xl transition-colors"
            >
              بدء المعالجة
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export function specimenTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    whole_blood: 'دم كامل', serum: 'مصل', plasma: 'بلازما', urine: 'بول',
    stool: 'براز', csf: 'سائل نخاعي', sputum: 'بلغم', swab: 'مسحة',
    tissue: 'نسيج', bone_marrow: 'نخاع عظمي', amniotic: 'سائل أمنيوسي',
    pleural: 'سائل جنبي', pericardial: 'سائل تأموري', peritoneal: 'سائل صفاقي',
    synovial: 'سائل زليلي', saliva: 'لعاب', hair: 'شعر', nail: 'ظفر', other: 'أخرى',
  };
  return labels[type] || type;
}
