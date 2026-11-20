export const supportedLocales = ["ar", "en", "ckb"] as const;

export type Locale = (typeof supportedLocales)[number];

export interface LocaleOption {
  code: Locale;
  nativeName: string;
  shortName: string;
  dir: "rtl" | "ltr";
}

// Only approved local core languages are shown. Dynamic foreign packs are
// selected through the GULS lifecycle after explicit user choice and install.
export const localeOptions: readonly LocaleOption[] = [
  { code: "ar", nativeName: "العربية الفصحى", shortName: "ع", dir: "rtl" },
  { code: "en", nativeName: "English", shortName: "EN", dir: "ltr" },
  { code: "ckb", nativeName: "کوردیی ناوەندی", shortName: "ک", dir: "rtl" },
] as const;

export const defaultLocale: Locale = "en";

const legacyLocaleMap: Partial<Record<string, Locale>> = {
  ku: "ckb",
  tk: "en",
  syr: "en",
};

export function isLocale(value: string | null | undefined): value is Locale {
  return Boolean(value && (supportedLocales as readonly string[]).includes(value));
}

export function normalizeLocale(value: string | null | undefined): Locale {
  if (isLocale(value)) return value;
  if (value) {
    const mapped: Locale | undefined = legacyLocaleMap[value];
    if (mapped) return mapped;
  }
  return defaultLocale;
}

export function getLocaleDirection(locale: Locale): "rtl" | "ltr" {
  return localeOptions.find((option) => option.code === locale)?.dir ?? "ltr";
}

export function getStoredLocale(): Locale {
  const stored = typeof window === "undefined" ? null : window.localStorage.getItem("gula.locale");
  const normalized = normalizeLocale(stored);
  if (stored && stored !== normalized && typeof window !== "undefined") {
    window.localStorage.setItem("gula.locale", normalized);
  }
  return normalized;
}
