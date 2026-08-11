import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Bell, Menu, Search, ShieldCheck, X } from "lucide-react";
import { Sidebar } from "./Sidebar";
import { useTheme } from "@/contexts/ThemeContext";
import { useLocale } from "@/contexts/LocaleContext";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui";
import { GuideAssistant } from "@/components/guide/GuideAssistant";
import { DemoEnvironmentBadge, GulaBrand } from "@/components/shared/GulaBrand";

export function DashboardLayout() {
  const { theme, setTheme } = useTheme();
  const { locale, setLocale } = useLocale();
  const { user, demoMode } = useAuth();
  const { t } = useTranslation();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const currentLabel = location.pathname === "/dashboard"
    ? t("nav.dashboard")
    : location.pathname.split("/").filter(Boolean).at(-1) || t("nav.dashboard");

  return (
    <div className="flex min-h-screen bg-background text-foreground" dir={locale === "ar" ? "rtl" : "ltr"}>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:right-2 focus:top-2 focus:z-[9999] focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground focus:shadow-lg focus:outline-none"
      >
        {locale === "ar" ? "تخطى إلى المحتوى الرئيسي" : "Skip to main content"}
      </a>

      <Sidebar mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />

      <main id="main-content" className="flex min-h-screen min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex min-h-16 items-center gap-3 border-b bg-card/95 px-4 backdrop-blur md:px-6">
          <Button variant="ghost" size="icon" className="md:hidden" onClick={() => setMobileOpen(true)} aria-label="فتح القائمة">
            <Menu className="h-5 w-5" />
          </Button>
          <div className="md:hidden">
            <GulaBrand />
          </div>
          <div className="hidden min-w-0 md:block">
            <p className="text-[10px] font-medium text-muted-foreground">منصة غولا · مركز العمليات</p>
            <h1 className="truncate text-sm font-semibold">{currentLabel}</h1>
          </div>

          <div className="mr-auto flex items-center gap-1">
            {demoMode && <DemoEnvironmentBadge />}
            <div className="hidden items-center gap-2 rounded-lg border bg-background px-3 py-2 text-xs text-muted-foreground lg:flex">
              <Search className="h-4 w-4" />
              <span>بحث داخل المنصة</span>
              <kbd className="rounded border bg-muted px-1.5 py-0.5 font-mono text-[10px]">⌘K</kbd>
            </div>
            <Button variant="ghost" size="icon" aria-label="التنبيهات" title={t("nav.notifications")}>
              <Bell className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setLocale(locale === "ar" ? "en" : "ar")}
              title={locale === "ar" ? "English" : "العربية"}
              aria-label={locale === "ar" ? "التبديل إلى الإنجليزية" : "التبديل إلى العربية"}
            >
              <span className="text-[11px] font-semibold">{locale === "ar" ? "EN" : "AR"}</span>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme(theme === "dark" ? "light" : theme === "light" ? "system" : "dark")}
              title={theme === "dark" ? "الوضع الفاتح" : "الوضع الداكن"}
              aria-label="تغيير المظهر"
            >
              <span className="text-sm">{theme === "dark" ? "☼" : "◐"}</span>
            </Button>
            <div className="hidden items-center gap-2 border-r pr-3 sm:flex">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">{user?.name?.charAt(0) || "م"}</span>
              <div className="max-w-32">
                <p className="truncate text-xs font-semibold">{user?.name || "مستخدم GULA"}</p>
                <p className="truncate text-[10px] text-muted-foreground">{user?.role || "مستخدم"}</p>
              </div>
            </div>
          </div>
        </header>

        {demoMode && (
          <div className="flex items-start gap-2 border-b border-amber-500/20 bg-amber-500/10 px-4 py-2.5 text-xs leading-5 text-amber-800 dark:text-amber-200 md:px-6">
            <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" />
            <span><strong>عرض توضيحي فقط.</strong> البيانات اصطناعية ومعزولة، ولا تتاح من هذه البيئة أي عملية سريرية أو بيانات مريض حقيقية.</span>
            <Button variant="ghost" size="icon" className="mr-auto -mt-1 h-6 w-6 text-amber-800 dark:text-amber-200" aria-label="إخفاء التنبيه">
              <X className="h-3.5 w-3.5" />
            </Button>
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </div>
      </main>
      <GuideAssistant />
    </div>
  );
}
