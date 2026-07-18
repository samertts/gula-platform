import { cn } from '@gula/ui-platform';
import type { NursingTask, Priority, TaskType } from '@/utils/types';
import { getPriorityArabic, getStatusArabic } from '@/utils/routes';

interface TaskItemProps {
  task: NursingTask;
  onClick?: () => void;
  compact?: boolean;
}

const priorityColors: Record<Priority, string> = {
  low: 'bg-neutral-100 dark:bg-neutral-700 border-neutral-300 dark:border-neutral-600',
  medium: 'bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700',
  high: 'bg-warning-50 dark:bg-warning-900/20 border-warning-400 dark:border-warning-700',
  urgent: 'bg-danger-50 dark:bg-danger-900/20 border-danger-400 dark:border-danger-700',
  stat: 'bg-danger-100 dark:bg-danger-900/30 border-danger-500 dark:border-danger-600 animate-pulse',
};

const priorityDots: Record<Priority, string> = {
  low: 'bg-neutral-400',
  medium: 'bg-blue-500',
  high: 'bg-warning-500',
  urgent: 'bg-danger-500',
  stat: 'bg-danger-600',
};

const typeIcons: Record<TaskType, string> = {
  medication: '💊',
  vitals: '❤️',
  wound_care: '🏥',
  catheter: '🩺',
  dressing: '🩹',
  observation: '👁️',
  feeding: '🍽️',
  mobilization: '🚶',
  education: '📚',
  assessment: '📋',
  other: '📌',
};

const statusStyles: Record<string, string> = {
  pending: 'bg-neutral-100 text-neutral-600 dark:bg-neutral-700 dark:text-neutral-400',
  'in-progress': 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400',
  completed: 'bg-success-100 text-success-600 dark:bg-success-900/30 dark:text-success-400',
  cancelled: 'bg-neutral-100 text-neutral-500 dark:bg-neutral-700 dark:text-neutral-400 line-through',
  delayed: 'bg-warning-100 text-warning-600 dark:bg-warning-900/30 dark:text-warning-400',
};

const isOverdue = (due: string) => new Date(due) < new Date();

export function TaskItem({ task, onClick, compact }: TaskItemProps) {
  const overdue = task.status === 'pending' && isOverdue(task.due);

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'w-full text-right p-3 rounded-2xl border-2 transition-all duration-200 hover:shadow-md',
        priorityColors[task.priority],
        overdue && 'ring-2 ring-danger-500/50',
      )}
    >
      <div className="flex items-start gap-3">
        <span className="text-xl shrink-0 mt-0.5">{typeIcons[task.type] || '📌'}</span>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={cn('w-2 h-2 rounded-full shrink-0', priorityDots[task.priority])} />
            <span className="font-bold text-sm text-neutral-900 dark:text-neutral-100 truncate">
              {task.description}
            </span>
          </div>

          {!compact && (
            <>
              <div className="flex items-center gap-2 text-xs text-neutral-500 dark:text-neutral-400">
                <span>{task.patientName}</span>
                <span>•</span>
                <span>{task.bed}</span>
              </div>

              <div className="flex items-center gap-2 mt-2">
                <span className={cn('text-[10px] px-2 py-0.5 rounded-lg font-bold', statusStyles[task.status])}>
                  {getStatusArabic(task.status)}
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded-lg font-bold bg-neutral-100 dark:bg-neutral-700 text-neutral-500">
                  {getPriorityArabic(task.priority)}
                </span>
                {overdue && (
                  <span className="text-[10px] px-2 py-0.5 rounded-lg font-bold bg-danger-100 dark:bg-danger-900/30 text-danger-600 dark:text-danger-400">
                    متأخر
                  </span>
                )}
              </div>

              <p className="text-[10px] text-neutral-400 dark:text-neutral-500 mt-1.5">
                مستحق: {new Date(task.due).toLocaleString('ar-IQ')}
              </p>
            </>
          )}
        </div>

        <svg className="w-4 h-4 text-neutral-400 shrink-0 mt-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M9 18l6-6-6-6" />
        </svg>
      </div>
    </button>
  );
}
