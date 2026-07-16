import { ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const rtl = (lang: string): 'rtl' | 'ltr' =>
  ['ar', 'ku', 'ckb', 'sd', 'ur', 'fa', 'he', 'ps'].includes(lang.toLowerCase().split('-')[0]) ? 'rtl' : 'ltr';

export const isRtl = (lang: string): boolean => rtl(lang) === 'rtl';
