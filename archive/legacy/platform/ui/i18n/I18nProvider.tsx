import { createContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import { setLocale, getCurrentLocale, t as translateFn, type Locale, type TranslationKey } from './i18n';

export interface I18nContextValue {
  locale: Locale;
  isRtl: boolean;
  setLocale: (locale: Locale) => void;
  t: (key: TranslationKey) => string;
}

export const I18nContext = createContext<I18nContextValue | null>(null);

export interface I18nProviderProps {
  children: ReactNode;
  defaultLocale?: Locale;
}

export function I18nProvider({ children, defaultLocale = 'en' }: I18nProviderProps) {
  const [locale, setLocaleState] = useState<Locale>(() => {
    return getCurrentLocale() || defaultLocale;
  });

  useEffect(() => {
    setLocale(locale);
  }, [locale]);

  const handleSetLocale = useCallback((newLocale: Locale) => {
    setLocaleState(newLocale);
    setLocale(newLocale);
  }, []);

  const isRtl = locale === 'ar';

  const t = useCallback(
    (key: TranslationKey): string => {
      return translateFn(key, locale);
    },
    [locale],
  );

  return (
    <I18nContext.Provider value={{ locale, isRtl, setLocale: handleSetLocale, t }}>
      <div dir={isRtl ? 'rtl' : 'ltr'} lang={locale}>
        {children}
      </div>
    </I18nContext.Provider>
  );
}
