import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getDir(lang?: string): 'rtl' | 'ltr' {
  return lang === 'AR' || lang === 'KU' ? 'rtl' : 'ltr';
}

export function formatDate(date: string | Date, locale = 'en'): string {
  const d = new Date(date);
  return d.toLocaleDateString(locale === 'ar' ? 'ar-IQ' : 'en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatDateTime(date: string | Date, locale = 'en'): string {
  const d = new Date(date);
  return d.toLocaleDateString(locale === 'ar' ? 'ar-IQ' : 'en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatNumber(n: number | string | null | undefined, locale = 'en'): string {
  if (n == null) return '—';
  const num = typeof n === 'string' ? Number(n) : n;
  if (isNaN(num)) return '—';
  return new Intl.NumberFormat(locale === 'ar' ? 'ar-IQ' : 'en-US').format(num);
}

export function getAge(birthDate: string): number {
  const today = new Date();
  const birth = new Date(birthDate);
  let age = today.getFullYear() - birth.getFullYear();
  const m = today.getMonth() - birth.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
  return age;
}

export function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

export function truncate(str: string, len: number): string {
  if (str.length <= len) return str;
  return str.slice(0, len) + '...';
}

export function paginationParams(skip = 0, limit = 20): { skip: number; limit: number } {
  return { skip, limit };
}

export function buildQueryString(params: Record<string, any>): string {
  const filtered = Object.entries(params).filter(([_, v]) => v !== undefined && v !== null && v !== '');
  if (filtered.length === 0) return '';
  return '?' + filtered.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join('&');
}
