import { ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const getDir = (lang: string): 'rtl' | 'ltr' => {
  return ['AR', 'KU', 'SY'].includes(lang) ? 'rtl' : 'ltr';
};

const LOCALE_MAP: Record<string, string> = {
  EN: 'en-US',
  AR: 'ar-IQ',
  KU: 'ku-TR',
  TR: 'tr-TR',
  SY: 'ar-SY',
};

export function getLocale(language: string): string {
  return LOCALE_MAP[language] || 'en-US';
}

export function formatDate(date: Date | number | string, language: string, options?: Intl.DateTimeFormatOptions): string {
  return new Intl.DateTimeFormat(getLocale(language), options).format(date instanceof Date ? date : new Date(date));
}

export function formatNumber(num: number, language: string, options?: Intl.NumberFormatOptions): string {
  return new Intl.NumberFormat(getLocale(language), options).format(num);
}

export function formatTime(date: Date | number | string, language: string, options?: Intl.DateTimeFormatOptions): string {
  return new Intl.DateTimeFormat(getLocale(language), {
    hour: '2-digit',
    minute: '2-digit',
    ...options,
  }).format(date instanceof Date ? date : new Date(date));
}
