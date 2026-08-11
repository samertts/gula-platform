import { Outlet } from "react-router-dom";
import { useTheme } from "@/contexts/ThemeContext";
import { useLocale } from "@/contexts/LocaleContext";
import { Button } from "@/components/ui";
import { GulaBrand } from "@/components/shared/GulaBrand";

export function AuthLayout() {
  const { theme, setTheme } = useTheme();
  const { locale, setLocale } = useLocale();

  return (
    <div className="min-h-screen bg-background" dir={locale === "ar" ? "rtl" : "ltr"}>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:right-2 focus:top-2 focus:z-[9999] focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground focus:shadow-lg focus:outline-none"
      >
        {locale === "ar" ? "تخطى إلى المحتوى الرئيسي" : "Skip to main content"}
      </a>
      <header className="flex min-h-16 items-center justify-between border-b bg-card/95 px-4 backdrop-blur md:px-8">
        <GulaBrand />
        <div className="flex items-center gap-2">
          <span className="hidden rounded-full border border-primary/20 bg-primary/5 px-3 py-1.5 text-xs font-medium text-primary sm:inline-flex">وصول مؤسسي وتجريبي</span>
          <Button variant="ghost" size="icon" onClick={() => setLocale(locale === "ar" ? "en" : "ar")} aria-label="تغيير اللغة">
            <span className="text-[11px] font-semibold">{locale === "ar" ? "EN" : "AR"}</span>
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === "dark" ? "light" : theme === "light" ? "system" : "dark")}
            aria-label="تغيير المظهر"
          >
            <span className="text-sm">{theme === "dark" ? "☼" : "◐"}</span>
          </Button>
        </div>
      </header>
      <main id="main-content" className="grid min-h-[calc(100vh-4rem)] place-items-center bg-gradient-to-br from-background via-background to-primary/5 p-4 md:p-8">
        <div className="w-full max-w-md">
          <Outlet />
        </div>
      </main>
      <footer className="fixed bottom-3 left-0 right-0 text-center text-[10px] text-muted-foreground">
        © {new Date().getFullYear()} GULA · نظام معلومات المختبرات الطبية
      </footer>
    </div>
  );
}
