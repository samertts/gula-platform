import { Outlet } from "react-router-dom";
import { Activity, ChevronDown, Globe2, LockKeyhole } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useTheme } from "@/contexts/ThemeContext";
import { useLocale } from "@/contexts/LocaleContext";
import { localeOptions, type Locale } from "@/i18n/locales";
import { Button } from "@/components/ui";
import { GulaBrand } from "@/components/shared/GulaBrand";

export function AuthLayout() {
  const { theme, setTheme } = useTheme();
  const { locale, setLocale, isRTL } = useLocale();
  const { t } = useTranslation();

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#f7fafb] text-foreground dark:bg-slate-950" dir={isRTL ? "rtl" : "ltr"}>
      <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
        <div className="absolute -right-24 -top-24 h-80 w-80 rounded-full bg-cyan-300/25 blur-3xl dark:bg-cyan-500/10" />
        <div className="absolute -bottom-40 -left-24 h-[28rem] w-[28rem] rounded-full bg-blue-300/20 blur-3xl dark:bg-blue-600/10" />
        <div className="absolute inset-0 opacity-[0.028] [background-image:linear-gradient(rgba(15,23,42,1)_1px,transparent_1px),linear-gradient(90deg,rgba(15,23,42,1)_1px,transparent_1px)] [background-size:42px_42px] dark:opacity-[0.05]" />
      </div>
      <a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:end-2 focus:top-2 focus:z-[9999] focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground focus:shadow-lg focus:outline-none">Skip to main content</a>
      <header className="relative z-10 flex min-h-20 items-center justify-between border-b border-white/75 bg-white/70 px-4 backdrop-blur-xl dark:border-white/10 dark:bg-slate-950/55 md:px-8">
        <GulaBrand />
        <div className="flex items-center gap-2">
          <span className="hidden items-center gap-2 rounded-full border border-primary/15 bg-primary/5 px-3 py-1.5 text-xs font-semibold text-primary sm:inline-flex"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> {t("loginPage.secureAccess")}</span>
          <label className="relative flex h-9 items-center gap-1.5 rounded-xl px-2 text-muted-foreground transition hover:bg-slate-100 dark:hover:bg-white/10">
            <Globe2 className="h-4 w-4" aria-hidden="true" />
            <span className="sr-only">{t("common.language")}</span>
            <select value={locale} onChange={(event) => setLocale(event.target.value as Locale)} className="max-w-24 appearance-none bg-transparent pe-4 text-xs font-semibold text-foreground outline-none" aria-label={t("common.language")}>
              {localeOptions.map((option) => <option key={option.code} value={option.code}>{option.nativeName}</option>)}
            </select>
            <ChevronDown className="pointer-events-none absolute end-2 h-3.5 w-3.5" aria-hidden="true" />
          </label>
          <Button variant="ghost" size="icon" className="rounded-xl" onClick={() => setTheme(theme === "dark" ? "light" : theme === "light" ? "system" : "dark")} aria-label="Toggle theme"><span className="text-sm">{theme === "dark" ? "☼" : "◐"}</span></Button>
        </div>
      </header>
      <main id="main-content" className="relative z-10 mx-auto flex min-h-[calc(100vh-5rem)] w-full max-w-7xl items-center justify-center px-4 py-8 sm:px-6 lg:px-8 lg:py-12">
        <div className="w-full max-w-5xl"><Outlet /></div>
      </main>
      <footer className="relative z-10 flex flex-col items-center justify-center gap-2 px-4 pb-7 text-center text-[11px] text-muted-foreground sm:flex-row">
        <span className="inline-flex items-center gap-1.5"><LockKeyhole className="h-3.5 w-3.5" /> {t("loginPage.secureAccess")}</span><span className="hidden sm:inline">•</span><span className="inline-flex items-center gap-1.5"><Activity className="h-3.5 w-3.5" /> © {new Date().getFullYear()} GULA</span>
      </footer>
    </div>
  );
}
