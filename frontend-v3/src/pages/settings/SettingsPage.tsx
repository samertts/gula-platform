import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { Card, CardContent, CardTitle, Button } from "@/components/ui";
import { PageHeader } from "@/components/shared/PageComponents";
import { useLocale } from "@/contexts/LocaleContext";
import { useTheme } from "@/contexts/ThemeContext";
import { Settings2, Bell, Shield, Palette, Globe, Sun, Moon, Monitor, ChevronLeft } from "lucide-react";

export function SettingsPage() {
  const { t } = useTranslation();
  const { locale, setLocale } = useLocale();
  const { theme, setTheme, resolvedTheme } = useTheme();

  const themeOptions = [
    { value: "light" as const, label: t("common.lightMode"), icon: Sun },
    { value: "dark" as const, label: t("common.darkMode"), icon: Moon },
    { value: "system" as const, label: t("settings.systemMode"), icon: Monitor },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title={t("settings.title")} description={t("settings.description")} />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10">
                <Globe className="h-5 w-5 text-primary" />
              </div>
              <div>
                <CardTitle className="text-base">{t("settings.languageRegion")}</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">{t("settings.languageRegionDesc")}</p>
              </div>
            </div>
            <div className="mt-4 flex gap-2">
              <Button
                variant={locale === "ar" ? "default" : "outline"}
                onClick={() => setLocale("ar")}
              >
                العربية
              </Button>
              <Button
                variant={locale === "en" ? "default" : "outline"}
                onClick={() => setLocale("en")}
              >
                English
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10">
                <Palette className="h-5 w-5 text-primary" />
              </div>
              <div>
                <CardTitle className="text-base">{t("settings.appearance")}</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">{t("settings.appearanceDesc")}</p>
              </div>
            </div>
            <div className="mt-4 flex gap-2">
              {themeOptions.map((option) => (
                <Button
                  key={option.value}
                  variant={theme === option.value ? "default" : "outline"}
                  onClick={() => setTheme(option.value)}
                >
                  <option.icon className="h-4 w-4" />
                  {option.label}
                </Button>
              ))}
            </div>
            <p className="mt-3 text-xs text-muted-foreground">
              {t("settings.currentTheme")}: {resolvedTheme}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10">
                <Shield className="h-5 w-5 text-primary" />
              </div>
              <div>
                <CardTitle className="text-base">{t("settings.security")}</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">{t("settings.securityDesc")}</p>
              </div>
            </div>
            <div className="mt-4">
              <Link
                to="/security"
                className="inline-flex h-9 items-center justify-center gap-2 rounded-md border border-input bg-background px-4 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
              >
                {t("settings.openSecurity")}
                <ChevronLeft className="h-4 w-4 rtl:rotate-180" />
              </Link>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10">
                <Bell className="h-5 w-5 text-primary" />
              </div>
              <div>
                <CardTitle className="text-base">{t("settings.notifications")}</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">{t("settings.notificationsDesc")}</p>
              </div>
            </div>
            <div className="mt-4">
              <Link
                to="/notifications"
                className="inline-flex h-9 items-center justify-center gap-2 rounded-md border border-input bg-background px-4 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
              >
                {t("nav.notifications")}
                <ChevronLeft className="h-4 w-4 rtl:rotate-180" />
              </Link>
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardContent className="flex items-start gap-4 p-6">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10">
              <Settings2 className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-base">{t("settings.general")}</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">{t("settings.generalDesc")}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
