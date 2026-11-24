import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import ar from "./ar";
import en from "./en";
import ku from "./ku";
import { getStoredLocale } from "./locales";

// The existing partial Sorani resource is exposed only under the approved
// identifier `ckb`. It is UI-only and must not be treated as clinical content.
i18n.use(initReactI18next).init({
  resources: {
    ar: { translation: ar },
    en: { translation: en },
    ckb: { translation: ku },
  },

  lng: getStoredLocale(),
  fallbackLng: "en",
  interpolation: { escapeValue: false },
  returnNull: false,
});

export default i18n;
