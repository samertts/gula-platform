import { ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const getDir = (lang: string): 'rtl' | 'ltr' => {
  return ['AR', 'KU', 'SY'].includes(lang) ? 'rtl' : 'ltr';
};
