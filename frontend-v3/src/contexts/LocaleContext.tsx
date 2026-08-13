import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import {
  defaultLocale,
  getLocaleDirection,
  getStoredLocale,
  type Locale,
} from "@/i18n/locales";

interface LocaleContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  isRTL: boolean;
}

const LocaleContext = createContext<LocaleContextType | null>(null);

export function LocaleProvider({ children }: { children: ReactNode }) {
  const { i18n } = useTranslation();
  const [locale, setLocaleState] = useState<Locale>(getStoredLocale);
  const isRTL = getLocaleDirection(locale) === "rtl";

  const setLocale = (nextLocale: Locale) => {
    window.localStorage.setItem("gula.locale", nextLocale);
    setLocaleState(nextLocale);
    void i18n.changeLanguage(nextLocale);

    const direction = getLocaleDirection(nextLocale);
    document.documentElement.lang = nextLocale;
    document.documentElement.dir = direction;
    document.documentElement.style.setProperty("--gula-reading-direction", direction);
  };

  useEffect(() => {
    setLocale(locale || defaultLocale);
    // Synchronize the stored preference on initial mount.
  }, []);

  return (
    <LocaleContext.Provider value={{ locale, setLocale, isRTL }}>
      {children}
    </LocaleContext.Provider>
  );
}

export function useLocale() {
  const ctx = useContext(LocaleContext);
  if (!ctx) throw new Error("useLocale must be used within LocaleProvider");
  return ctx;
}
