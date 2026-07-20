import { cn } from '@/lib/utils';
import type { ReactNode } from 'react';

const variants = {
  default: 'bg-surface-container-high text-on-surface',
  primary: 'bg-primary-light text-primary',
  success: 'bg-success-container text-on-success-container',
  warning: 'bg-warning-container text-on-warning-container',
  danger: 'bg-error-container text-on-error-container',
  info: 'bg-blue-50 text-blue-700',
  critical: 'bg-red-100 text-red-800',
};

const sizes = { sm: 'px-1.5 py-0.5 text-[10px]', md: 'px-2.5 py-0.5 text-xs', lg: 'px-3 py-1 text-sm' };

interface BadgeProps {
  children: ReactNode;
  variant?: keyof typeof variants;
  size?: keyof typeof sizes;
  className?: string;
}

export function Badge({ children, variant = 'default', size = 'md', className }: BadgeProps) {
  return (
    <span className={cn('inline-flex items-center rounded-full font-medium', variants[variant], sizes[size], className)}>
      {children}
    </span>
  );
}

const STATUS_MAP: Record<string, keyof typeof variants> = {
  pending: 'warning', completed: 'success', validated: 'info', cancelled: 'danger',
  active: 'success', inactive: 'default', collected: 'info', received: 'primary',
  processing: 'warning', analyzed: 'success', rejected: 'danger',
  pass: 'success', warning: 'warning', fail: 'danger',
  normal: 'success', high: 'warning', low: 'warning', critical: 'critical',
  draft: 'default', submitted: 'info', accepted: 'success', paid: 'success',
  open: 'warning', closed: 'default',
  scheduled: 'primary', confirmed: 'success', in_progress: 'warning',
  online: 'success', offline: 'default', error: 'danger',
};

export function StatusBadge({ status, className }: { status: string; className?: string }) {
  return (
    <Badge variant={STATUS_MAP[status.toLowerCase()] || 'default'} size="sm" className={className}>
      {status}
    </Badge>
  );
}
