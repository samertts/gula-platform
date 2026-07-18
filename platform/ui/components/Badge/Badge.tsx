import { type ReactNode } from 'react';
import { cn } from '../../utils/cn';

export type BadgeVariant = 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'primary' | 'lab' | 'emergency';
export type BadgeSize = 'xs' | 'sm' | 'md' | 'lg';

export interface BadgeProps {
  variant?: BadgeVariant;
  size?: BadgeSize;
  children: ReactNode;
  dot?: boolean;
  removable?: boolean;
  onRemove?: () => void;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  success: 'bg-success-100 text-success-700 dark:bg-success-900/30 dark:text-success-400',
  warning: 'bg-warning-100 text-warning-700 dark:bg-warning-900/30 dark:text-warning-400',
  danger: 'bg-danger-100 text-danger-700 dark:bg-danger-900/30 dark:text-danger-400',
  info: 'bg-info-100 text-info-700 dark:bg-info-900/30 dark:text-info-400',
  neutral: 'bg-neutral-100 text-neutral-700 dark:bg-neutral-700 dark:text-neutral-300',
  primary: 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400',
  lab: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  emergency: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
};

const dotStyles: Record<BadgeVariant, string> = {
  success: 'bg-success-500',
  warning: 'bg-warning-500',
  danger: 'bg-danger-500',
  info: 'bg-info-500',
  neutral: 'bg-neutral-500',
  primary: 'bg-primary-500',
  lab: 'bg-purple-500',
  emergency: 'bg-orange-500',
};

const sizeStyles: Record<BadgeSize, string> = {
  xs: 'px-1.5 py-0.5 text-[10px] rounded',
  sm: 'px-2 py-0.5 text-xs rounded-md',
  md: 'px-2.5 py-1 text-xs rounded-lg',
  lg: 'px-3 py-1.5 text-sm rounded-xl',
};

export function Badge({
  variant = 'neutral',
  size = 'md',
  children,
  dot = false,
  removable = false,
  onRemove,
  className,
}: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 font-bold whitespace-nowrap',
        variantStyles[variant],
        sizeStyles[size],
        className,
      )}
    >
      {dot && <span className={cn('w-1.5 h-1.5 rounded-full shrink-0', dotStyles[variant])} />}
      {children}
      {removable && (
        <button
          type="button"
          onClick={onRemove}
          className="ml-0.5 rtl:ml-0 rtl:mr-0.5 hover:opacity-70 transition-opacity"
          aria-label="Remove badge"
        >
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M9 3L3 9M3 3l6 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      )}
    </span>
  );
}
