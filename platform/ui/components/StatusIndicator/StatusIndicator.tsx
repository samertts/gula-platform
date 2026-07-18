import { cn } from '../../utils/cn';

export type StatusType = 'online' | 'offline' | 'processing' | 'warning' | 'error' | 'idle';

export interface StatusIndicatorProps {
  status: StatusType;
  label?: string;
  showPulse?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const statusStyles: Record<StatusType, string> = {
  online: 'bg-success-500',
  offline: 'bg-neutral-400 dark:bg-neutral-500',
  processing: 'bg-warning-500',
  warning: 'bg-warning-500',
  error: 'bg-danger-500',
  idle: 'bg-neutral-300 dark:bg-neutral-600',
};

const sizeStyles = {
  sm: 'w-2 h-2',
  md: 'w-2.5 h-2.5',
  lg: 'w-3 h-3',
};

const labelColors: Record<StatusType, string> = {
  online: 'text-success-600 dark:text-success-400',
  offline: 'text-neutral-500 dark:text-neutral-400',
  processing: 'text-warning-600 dark:text-warning-400',
  warning: 'text-warning-600 dark:text-warning-400',
  error: 'text-danger-600 dark:text-danger-400',
  idle: 'text-neutral-400 dark:text-neutral-500',
};

export function StatusIndicator({
  status,
  label,
  showPulse = false,
  size = 'md',
  className,
}: StatusIndicatorProps) {
  return (
    <span className={cn('inline-flex items-center gap-2', className)}>
      <span className="relative inline-flex shrink-0">
        <span
          className={cn(
            'rounded-full',
            statusStyles[status],
            sizeStyles[size],
          )}
        />
        {showPulse && (
          <span
            className={cn(
              'absolute inset-0 rounded-full animate-ping opacity-75',
              statusStyles[status],
            )}
          />
        )}
      </span>
      {label && (
        <span className={cn('text-sm font-medium', labelColors[status])}>
          {label}
        </span>
      )}
    </span>
  );
}
