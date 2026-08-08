import { type ReactNode } from 'react';
import { cn } from '../../utils/cn';

export interface EmptyStateAction {
  label: string;
  onClick?: () => void;
  href?: string;
  variant?: 'primary' | 'secondary';
}

export interface EmptyStateProps {
  title: string;
  description?: ReactNode;
  icon?: ReactNode;
  actions?: EmptyStateAction[];
  hint?: ReactNode;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeClasses = {
  sm: 'p-8 gap-3',
  md: 'p-12 gap-4',
  lg: 'p-16 gap-5',
};

const iconSizes = { sm: 28, md: 36, lg: 48 };
const iconBoxSizes = { sm: 'h-14 w-14', md: 'h-20 w-20', lg: 'h-24 w-24' };

const defaultIcon = (
  <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
    <rect x="4" y="7" width="28" height="22" rx="4" stroke="currentColor" strokeWidth="1.5"/>
    <path d="M4 14h28" stroke="currentColor" strokeWidth="1.5"/>
    <circle cx="10" cy="11" r="1.5" fill="currentColor"/>
    <circle cx="14" cy="11" r="1.5" fill="currentColor"/>
  </svg>
);

export function EmptyState({
  title,
  description,
  icon,
  actions = [],
  hint,
  size = 'md',
  className,
}: EmptyStateProps) {
  return (
    <div
      role="status"
      className={cn(
        'flex flex-col items-center text-center bg-white dark:bg-neutral-900 rounded-2xl border border-neutral-200 dark:border-neutral-800',
        sizeClasses[size],
        className,
      )}
    >
      <div
        className={cn(
          'rounded-3xl bg-neutral-50 dark:bg-neutral-800 flex items-center justify-center text-neutral-300 dark:text-neutral-600',
          iconBoxSizes[size],
        )}
        aria-hidden="true"
      >
        <span style={{ width: iconSizes[size], height: iconSizes[size] }}>
          {icon || defaultIcon}
        </span>
      </div>
      <h3 className="text-lg sm:text-xl font-bold text-neutral-900 dark:text-neutral-50 tracking-tight">
        {title}
      </h3>
      {description && (
        <p className="text-sm text-neutral-500 dark:text-neutral-400 max-w-md leading-relaxed">
          {description}
        </p>
      )}
      {actions.length > 0 && (
        <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
          {actions.map((action, i) => {
            const isPrimary = action.variant ?? (i === 0 ? 'primary' : 'secondary');
            const base = 'px-5 py-2.5 rounded-xl text-sm font-bold transition-all active:scale-95 shadow-sm';
            const variants = isPrimary === 'primary'
              ? 'bg-primary-500 text-white shadow-primary-100 hover:bg-primary-600'
              : 'bg-neutral-100 text-neutral-700 border border-neutral-200 hover:bg-neutral-200 dark:bg-neutral-800 dark:text-neutral-300 dark:border-neutral-700 dark:hover:bg-neutral-700';
            return action.href ? (
              <a key={i} href={action.href} className={cn(base, variants)}>
                {action.label}
              </a>
            ) : (
              <button key={i} type="button" onClick={action.onClick} className={cn(base, variants)}>
                {action.label}
              </button>
            );
          })}
        </div>
      )}
      {hint && (
        <p className="text-[11px] font-bold uppercase tracking-widest text-neutral-400 dark:text-neutral-500 mt-1">
          {hint}
        </p>
      )}
    </div>
  );
}
