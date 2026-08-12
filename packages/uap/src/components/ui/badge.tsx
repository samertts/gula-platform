import React from 'react';
import { cn } from '../utils';
import { AlertCircle, AlertTriangle, CheckCircle2, Info, X } from 'lucide-react';

interface AlertProps {
  variant?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  children: React.ReactNode;
  onClose?: () => void;
  className?: string;
}

const icons = {
  info: Info,
  success: CheckCircle2,
  warning: AlertTriangle,
  error: AlertCircle,
};

const styles = {
  info: 'bg-info-50 dark:bg-info-950 border-info-200 dark:border-info-800 text-info-800 dark:text-info-200',
  success: 'bg-success-50 dark:bg-success-950 border-success-200 dark:border-success-800 text-success-800 dark:text-success-200',
  warning: 'bg-warning-50 dark:bg-warning-950 border-warning-200 dark:border-warning-800 text-warning-800 dark:text-warning-200',
  error: 'bg-error-50 dark:bg-error-950 border-error-200 dark:border-error-800 text-error-800 dark:text-error-200',
};

export const Alert: React.FC<AlertProps> = ({ variant = 'info', title, children, onClose, className }) => {
  const Icon = icons[variant];
  return (
    <div className={cn('flex gap-3 p-4 rounded-lg border', styles[variant], className)} role="alert">
      <Icon size={20} className="shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        {title && <p className="font-medium text-sm mb-1">{title}</p>}
        <div className="text-sm opacity-90">{children}</div>
      </div>
      {onClose && (
        <button onClick={onClose} className="shrink-0 opacity-60 hover:opacity-100 transition-opacity">
          <X size={16} />
        </button>
      )}
    </div>
  );
};

interface BadgeProps {
  variant?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  size?: 'sm' | 'md';
  children: React.ReactNode;
  className?: string;
}

const badgeStyles = {
  default: 'bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300',
  primary: 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300',
  secondary: 'bg-secondary-100 dark:bg-secondary-900/30 text-secondary-700 dark:text-secondary-300',
  success: 'bg-success-100 dark:bg-success-900/30 text-success-700 dark:text-success-300',
  warning: 'bg-warning-100 dark:bg-warning-900/30 text-warning-800 dark:text-warning-300',
  error: 'bg-error-100 dark:bg-error-900/30 text-error-700 dark:text-error-300',
  info: 'bg-info-100 dark:bg-info-900/30 text-info-700 dark:text-info-300',
};

export const Badge: React.FC<BadgeProps> = ({ variant = 'default', size = 'md', children, className }) => (
  <span className={cn(
    'inline-flex items-center font-medium rounded-full',
    size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-0.5 text-sm',
    badgeStyles[variant],
    className
  )}>
    {children}
  </span>
);

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({ size = 'md', className }) => {
  const sizeMap = { sm: 'h-4 w-4', md: 'h-6 w-6', lg: 'h-8 w-8' };
  return (
    <svg className={cn('animate-spin text-primary-600', sizeMap[size], className)} viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
};

export const EmptyState: React.FC<{
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}> = ({ icon, title, description, action }) => (
  <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
    {icon && <div className="mb-4 text-neutral-300 dark:text-neutral-600">{icon}</div>}
    <h3 className="text-lg font-medium text-neutral-900 dark:text-white">{title}</h3>
    {description && <p className="mt-1 text-sm text-neutral-500 max-w-sm">{description}</p>}
    {action && <div className="mt-4">{action}</div>}
  </div>
);

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className, variant = 'text', width, height }) => (
  <div
    className={cn(
      'animate-pulse bg-neutral-200 dark:bg-neutral-700',
      variant === 'circular' && 'rounded-full',
      variant === 'text' && 'rounded h-4',
      variant === 'rectangular' && 'rounded-lg',
      className
    )}
    style={{ width, height }}
  />
);
