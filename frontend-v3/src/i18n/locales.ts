export const supportedLocales = ["ar-IQ", "ar", "en", "ku", "tk", "syr", "fa"] as const;

export type Locale = (typeof supportedLocales)[number];

export interface LocaleOption {
  code: Locale;
  nativeName: string;
  shortName: string;
  dir: "rtl" | "ltr";
}

export const localeOptions: readonly LocaleOption[] = [
  { code: "ar-IQ", nativeName: "العربية العراقية", shortName: "ع-ع", dir: "rtl" },
  { code: "ar", nativeName: "العربية الفصحى", shortName: "ع", dir: "rtl" },
  { code: "en", nativeName: "English", shortName: "EN", dir: "ltr" },
  { code: "ku", nativeName: "کوردی", shortName: "ک", dir: "rtl" },
  { code: "tk", nativeName: "Türkmençe", shortName: "TM", dir: "ltr" },
  { code: "syr", nativeName: "ܣܘܪܝܬ", shortName: "ܣ", dir: "rtl" },
  { code: "fa", nativeName: "فارسی", shortName: "فا", dir: "rtl" },
] as const;

export const defaultLocale: Locale = "ar";

export function isLocale(value: string | null | undefined): value is Locale {
  return Boolean(value && supportedLocales.includes(value as Locale));
}

export function getLocaleDirection(locale: Locale): "rtl" | "ltr" {
  return localeOptions.find((option) => option.code === locale)?.dir ?? "rtl";
}

export function getStoredLocale(): Locale {
  const stored = typeof window === "undefined" ? null : window.localStorage.getItem("gula.locale");
  return isLocale(stored) ? stored : defaultLocale;
}
