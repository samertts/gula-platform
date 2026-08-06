import { Outlet } from "react-router";
import { useTheme } from "@/contexts/ThemeContext";
import { useLocale } from "@/contexts/LocaleContext";
import { Moon, Sun, Languages } from "lucide-react";
import { Button } from "@/components/ui";

export function AuthLayout() {
  const { theme, setTheme } = useTheme();
  const { locale, setLocale } = useLocale();

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[9999] focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-md focus:shadow-lg focus:outline-none"
      >
        {locale === "ar" ? "تخطى إلى المحتوى الرئيسي" : "Skip to main content"}
      </a>
      <header className="flex h-14 items-center justify-end gap-2 border-b bg-card px-6">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setLocale(locale === "ar" ? "en" : "ar")}
        >
          <Languages className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(theme === "dark" ? "light" : theme === "light" ? "system" : "dark")}
        >
          {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>
      </header>
      <main id="main-content" className="flex flex-1 items-center justify-center p-4">
        <div className="w-full max-w-md">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
