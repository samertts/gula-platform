import { useState, useCallback } from 'react';

export type Locale = 'ar' | 'en';

export interface LocalizationResult {
  locale: Locale;
  isRtl: boolean;
  setLocale: (locale: Locale) => void;
  toggleLocale: () => void;
}

export function useLocalization(defaultLocale: Locale = 'en'): LocalizationResult {
  const [locale, setLocaleState] = useState<Locale>(() => {
    if (typeof document !== 'undefined') {
      const saved = localStorage.getItem('gula-locale') as Locale | null;
      if (saved === 'ar' || saved === 'en') return saved;
      const htmlLang = document.documentElement.lang;
      if (htmlLang === 'ar') return 'ar';
    }
    return defaultLocale;
  });

  const setLocale = useCallback((newLocale: Locale) => {
    setLocaleState(newLocale);
    document.documentElement.lang = newLocale;
    document.documentElement.dir = newLocale === 'ar' ? 'rtl' : 'ltr';
    localStorage.setItem('gula-locale', newLocale);
  }, []);

  const toggleLocale = useCallback(() => {
    setLocale(locale === 'ar' ? 'en' : 'ar');
  }, [locale, setLocale]);

  return {
    locale,
    isRtl: locale === 'ar',
    setLocale,
    toggleLocale,
  };
}
