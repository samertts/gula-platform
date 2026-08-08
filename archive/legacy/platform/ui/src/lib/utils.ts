import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function isRTL(locale: string): boolean {
  return ['ar', 'he', 'fa', 'ur'].includes(locale);
}

export function getDirection(locale: string): 'rtl' | 'ltr' {
  return isRTL(locale) ? 'rtl' : 'ltr';
}

export function formatLabValue(
  value: number,
  unit: string,
  decimals: number = 1,
): string {
  const formatted = value.toFixed(decimals);
  return `${formatted} ${unit}`;
}

export function getStatusColor(
  status: 'normal' | 'borderline' | 'abnormal' | 'critical' | 'pending' | 'cancelled',
): string {
  const colors = {
    normal: 'text-status-normal',
    borderline: 'text-status-borderline',
    abnormal: 'text-status-abnormal',
    critical: 'text-status-critical',
    pending: 'text-status-pending',
    cancelled: 'text-status-cancelled',
  };
  return colors[status] || 'text-surface-500';
}

export function getStatusBgColor(
  status: 'normal' | 'borderline' | 'abnormal' | 'critical' | 'pending' | 'cancelled',
): string {
  const colors = {
    normal: 'bg-clinical-green-50',
    borderline: 'bg-clinical-yellow-50',
    abnormal: 'bg-clinical-red-50',
    critical: 'bg-critical-50',
    pending: 'bg-surface-50',
    cancelled: 'bg-surface-100',
  };
  return colors[status] || 'bg-surface-50';
}

export function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}
