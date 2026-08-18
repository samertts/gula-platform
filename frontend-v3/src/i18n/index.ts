import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import ar from "./ar";
import en from "./en";
import ku from "./ku";
import syr from "./syr";
import tk from "./tk";
import { getStoredLocale } from "./locales";

i18n.use(initReactI18next).init({
  resources: {
    ar: { translation: ar },
    en: { translation: en },
    ku: { translation: ku },
    tk: { translation: tk },
    syr: { translation: syr },
  },

  lng: getStoredLocale(),
  fallbackLng: "en",
  interpolation: { escapeValue: false },
  returnNull: false,
});

export default i18n;
