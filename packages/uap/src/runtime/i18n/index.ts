import { create } from 'zustand';

export type Locale = 'ar' | 'en' | 'ku' | 'tr' | 'fa' | 'ckb';

export type TranslationDict = Record<string, string>;

interface I18nState {
  locale: Locale;
  direction: 'ltr' | 'rtl';
  translations: Record<Locale, TranslationDict>;
  setLocale: (locale: Locale) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
  addTranslations: (locale: Locale, dict: TranslationDict) => void;
  getDirection: (locale: Locale) => 'ltr' | 'rtl';
}

const RTL_LOCALES: Locale[] = ['ar', 'ku', 'ckb', 'fa'];

export const useI18n = create<I18nState>((set, get) => ({
  locale: 'ar',
  direction: 'rtl',
  translations: {} as Record<Locale, TranslationDict>,

  setLocale: (locale: Locale) => {
    set({ locale, direction: get().getDirection(locale) });
  },

  t: (key: string, params?: Record<string, string | number>): string => {
    const { locale, translations } = get();
    const dict = translations[locale];
    if (!dict) return key;
    let value = dict[key];
    if (!value) return key;
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        value = value!.replace(`{${k}}`, String(v));
      });
    }
    return value;
  },

  addTranslations: (locale: Locale, dict: TranslationDict) => {
    set((state) => ({
      translations: {
        ...state.translations,
        [locale]: { ...state.translations[locale], ...dict },
      },
    }));
  },

  getDirection: (locale: Locale): 'ltr' | 'rtl' =>
    RTL_LOCALES.includes(locale) ? 'rtl' : 'ltr',
}));

export const t = (key: string, params?: Record<string, string | number>) =>
  useI18n.getState().t(key, params);

export const setLocale = (locale: Locale) => useI18n.getState().setLocale(locale);
