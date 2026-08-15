import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  Bell,
  Menu,
  Monitor,
  Moon,
  Search,
  ShieldCheck,
  SunMedium,
  X,
} from "lucide-react";
import { Sidebar } from "./Sidebar";
import { useTheme } from "@/contexts/ThemeContext";
import { useLocale } from "@/contexts/LocaleContext";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui";
import { GuideAssistant } from "@/components/guide/GuideAssistant";
import { DemoEnvironmentBadge, GulaBrand } from "@/components/shared/GulaBrand";
import { WorkspaceSelector } from "@/components/workspace/WorkspaceSelector";
import { MobileBottomNav } from "@/components/navigation/MobileBottomNav";
import { localeOptions } from "@/i18n/locales";

export function DashboardLayout() {
  const { theme, setTheme } = useTheme();
  const { locale, setLocale, isRTL } = useLocale();
  const { user, demoMode } = useAuth();
  const { t } = useTranslation();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [showDemoNotice, setShowDemoNotice] = useState(true);
  const currentLocaleIndex = Math.max(
    0,
    localeOptions.findIndex((option) => option.code === locale),
  );
  const nextLocale =
    localeOptions[(currentLocaleIndex + 1) % localeOptions.length] ??
    localeOptions[0]!;

  const currentLabel =
    location.pathname === "/dashboard"
      ? t("nav.dashboard")
      : location.pathname.split("/").filter(Boolean).at(-1) ||
        t("nav.dashboard");

  return (
    <div
      className="flex min-h-[100dvh] overflow-x-clip bg-[#F8FAFC] text-foreground dark:bg-slate-950"
      dir={isRTL ? "rtl" : "ltr"}
    >
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:right-2 focus:top-2 focus:z-[9999] focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground focus:shadow-lg focus:outline-none"
      >
        {t("mobileNav.skipToContent")}
      </a>
      <Sidebar mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />
      <main
        id="main-content"
        className="flex min-h-screen min-w-0 flex-1 flex-col"
      >
        <header className="sticky top-0 z-30 flex min-h-[4.5rem] items-center gap-3 border-b border-slate-200/80 bg-white/90 px-4 shadow-[0_12px_32px_-28px_rgba(15,23,42,0.58)] backdrop-blur-xl dark:border-white/10 dark:bg-slate-950/85 md:px-7">
          <Button
            variant="ghost"
            size="icon"
            className="h-11 w-11 rounded-xl lg:hidden"
            onClick={() => setMobileOpen(true)}
            aria-label={t("mobileNav.openAllSections")}
          >
            <Menu className="h-5 w-5" />
          </Button>
          <div className="min-w-0 shrink-0 lg:hidden">
            <GulaBrand />
          </div>
          <div className="hidden min-w-0 lg:block">
            <p className="mb-1 text-[10px] font-bold uppercase tracking-[0.18em] text-[#0D9488]">
              GULA · مركز العمليات
            </p>
            <h1 className="truncate text-base font-bold">{currentLabel}</h1>
          </div>
          <div className="ms-auto flex min-w-0 items-center gap-1.5 sm:gap-2">
            {demoMode && (
              <div className="hidden sm:block">
                <DemoEnvironmentBadge />
              </div>
            )}
            <div className="hidden sm:block">
              <WorkspaceSelector />
            </div>
            <button
              type="button"
              className="hidden items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-muted-foreground transition hover:border-primary/30 hover:bg-primary/5 lg:flex dark:border-white/10 dark:bg-white/[0.04]"
              aria-label="بحث داخل المنصة"
            >
              <Search className="h-4 w-4" />
              <span>بحث داخل المنصة</span>
              <kbd className="rounded-md border bg-white px-1.5 py-0.5 font-mono text-[10px] dark:bg-white/10">
                ⌘K
              </kbd>
            </button>
            <Button
              variant="ghost"
              size="icon"
              className="hidden h-11 w-11 rounded-xl sm:inline-flex"
              aria-label="التنبيهات"
              title={t("nav.notifications")}
            >
              <Bell className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-11 w-11 rounded-xl"
              onClick={() => setLocale(nextLocale.code)}
              title={t("mobileNav.changeLanguage")}
              aria-label={t("mobileNav.changeLanguage")}
            >
              <span className="text-[11px] font-bold">
                {nextLocale.shortName}
              </span>
            </Button>
            <Button
              variant="outline"
              size="icon"
              className="h-11 w-11 rounded-xl bg-white/50 dark:bg-white/[0.04]"
              onClick={() =>
                setTheme(
                  theme === "dark"
                    ? "light"
                    : theme === "light"
                      ? "system"
                      : "dark",
                )
              }
              title={
                theme === "dark"
                  ? "المظهر الفاتح"
                  : theme === "light"
                    ? "مظهر النظام"
                    : "المظهر الداكن"
              }
              aria-label={
                theme === "dark"
                  ? "تفعيل المظهر الفاتح"
                  : theme === "light"
                    ? "استخدام مظهر النظام"
                    : "تفعيل المظهر الداكن"
              }
            >
              {theme === "dark" ? (
                <Moon className="h-4 w-4" aria-hidden="true" />
              ) : theme === "light" ? (
                <SunMedium className="h-4 w-4" aria-hidden="true" />
              ) : (
                <Monitor className="h-4 w-4" aria-hidden="true" />
              )}
            </Button>
            <div className="hidden items-center gap-2 border-r border-slate-200 pr-3 dark:border-white/10 sm:flex">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-[#0D9488] to-[#0F172A] text-sm font-bold text-white shadow-[0_10px_24px_-14px_rgba(15,23,42,0.8)]">
                {user?.name?.charAt(0) || "م"}
              </span>
              <div className="max-w-36">
                <p className="truncate text-xs font-bold">
                  {user?.name || "مستخدم GULA"}
                </p>
                <p className="truncate text-[10px] text-muted-foreground">
                  {user?.role || "مستخدم"}
                </p>
              </div>
            </div>
          </div>
        </header>

        {demoMode && showDemoNotice && (
          <div
            role="status"
            className="flex items-start gap-3 border-b border-amber-500/20 bg-gradient-to-l from-amber-50 to-white px-4 py-3 text-xs leading-6 text-amber-900 dark:from-amber-950/40 dark:to-slate-950 dark:text-amber-100 md:px-7"
          >
            <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-amber-500/15 text-amber-700 dark:text-amber-200">
              <ShieldCheck className="h-4 w-4" />
            </span>
            <span>
              <strong className="font-bold">وضع المعاينة مفعل.</strong> كل
              البيانات اصطناعية ومعزولة، ولا تتاح من هذه البيئة أي عملية سريرية
              أو بيانات مريض حقيقية.
            </span>
            <Button
              variant="ghost"
              size="icon"
              className="mr-auto -mt-1 h-7 w-7 shrink-0 rounded-lg text-amber-800 hover:bg-amber-500/10 dark:text-amber-200"
              onClick={() => setShowDemoNotice(false)}
              aria-label="إخفاء التنبيه"
            >
              <X className="h-3.5 w-3.5" />
            </Button>
          </div>
        )}
        <div className="flex-1 overflow-y-auto bg-[radial-gradient(circle_at_top_left,rgba(13,148,136,0.08),transparent_30%),radial-gradient(circle_at_bottom_right,rgba(14,165,233,0.06),transparent_34%)] p-4 pb-[calc(5.5rem+env(safe-area-inset-bottom))] md:p-7">
          <Outlet />
        </div>
      </main>
      <GuideAssistant />
      <MobileBottomNav
        onOpenMenu={() => setMobileOpen(true)}
        isMenuOpen={mobileOpen}
      />
    </div>
  );
}
