import en from './locales/en.json';
import ar from './locales/ar.json';

export type Locale = 'ar' | 'en';

export type TranslationKey = keyof typeof en;

export const translations: Record<Locale, Record<string, string>> = {
  en: en as Record<string, string>,
  ar: ar as Record<string, string>,
};

export type I18nMessages = typeof en;

let currentLocale: Locale = 'en';

export function setLocale(locale: Locale): void {
  currentLocale = locale;
  if (typeof document !== 'undefined') {
    document.documentElement.lang = locale;
    document.documentElement.dir = locale === 'ar' ? 'rtl' : 'ltr';
    localStorage.setItem('gula-locale', locale);
  }
}

export function getCurrentLocale(): Locale {
  if (typeof document !== 'undefined') {
    const saved = localStorage.getItem('gula-locale') as Locale | null;
    if (saved === 'ar' || saved === 'en') return saved;
  }
  return currentLocale;
}

export function t(key: TranslationKey, locale?: Locale): string {
  const loc = locale ?? getCurrentLocale();
  return translations[loc]?.[key] ?? translations.en[key] ?? key;
}

export function tpl(key: TranslationKey, params: Record<string, string | number>, locale?: Locale): string {
  let message = t(key, locale);
  Object.entries(params).forEach(([k, v]) => {
    message = message.replace(`{${k}}`, String(v));
  });
  return message;
}

export function getDirection(locale?: Locale): 'rtl' | 'ltr' {
  return (locale ?? getCurrentLocale()) === 'ar' ? 'rtl' : 'ltr';
}
