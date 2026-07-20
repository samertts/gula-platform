import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import { ar } from './ar';
import { en } from './en';

const resources = { ar: { translation: ar }, en: { translation: en } };

i18n.use(LanguageDetector).use(initReactI18next).init({
  resources,
  fallbackLng: 'ar',
  lng: localStorage.getItem('language') || 'ar',
  interpolation: { escapeValue: false },
  detection: {
    order: ['localStorage', 'navigator'],
    caches: ['localStorage'],
    lookupLocalStorage: 'language',
  },
});

export default i18n;
