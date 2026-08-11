import { useTranslation } from "react-i18next";
import { useNavigate, Link } from "react-router";
import { useTheme } from "@/contexts/ThemeContext";
import { useLocale } from "@/contexts/LocaleContext";
import { Moon, Sun, Languages, ArrowRight, FlaskConical } from "lucide-react";
import { Button, Card } from "@/components/ui";

type LegalKind = "privacy" | "terms";

interface LegalPageProps {
  kind: LegalKind;
}

export function LegalPage({ kind }: LegalPageProps) {
  const { t } = useTranslation();
  const { theme, setTheme } = useTheme();
  const { locale, setLocale } = useLocale();
  const navigate = useNavigate();

  const isPrivacy = kind === "privacy";
  const title = t(`legal.${isPrivacy ? "privacyTitle" : "termsTitle"}`);
  const updated = t(`legal.${isPrivacy ? "privacyUpdated" : "termsUpdated"}`);
  const intro = t(`legal.${isPrivacy ? "privacyIntro" : "termsIntro"}`);

  const sectionCount = isPrivacy ? 6 : 10;
  const sections = Array.from({ length: sectionCount }, (_, i) => {
    const n = i + 1;
    return {
      title: t(`legal.${isPrivacy ? "privacySection" : "termsSection"}${n}Title`),
      p1: t(`legal.${isPrivacy ? "privacySection" : "termsSection"}${n}P1`),
      p2: isPrivacy || n >= 2 ? t(`legal.${isPrivacy ? "privacySection" : "termsSection"}${n}P2`) : undefined,
    };
  });

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <a
        href="#legal-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[9999] focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-md focus:shadow-lg focus:outline-none"
      >
        {locale === "ar" ? "تخطى إلى المحتوى" : "Skip to content"}
      </a>
      <header className="flex h-14 items-center justify-between gap-2 border-b bg-card px-6">
        <Link to="/login" className="flex items-center gap-2 text-sm font-semibold">
          <FlaskConical className="h-5 w-5 text-primary" />
          <span>{t("app.name")}</span>
        </Link>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" onClick={() => setLocale(locale === "ar" ? "en" : "ar")}>
            <Languages className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === "dark" ? "light" : theme === "light" ? "system" : "dark")}
          >
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>
        </div>
      </header>
      <main id="legal-content" className="flex-1 px-4 py-10">
        <div className="mx-auto max-w-3xl">
          <Button
            variant="ghost"
            size="sm"
            className="mb-6"
            onClick={() => navigate("/login")}
          >
            <ArrowRight className="h-4 w-4 rtl:rotate-180" />
            {t("legal.backToLogin")}
          </Button>
          <Card>
            <div className="border-b p-6">
              <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
              <p className="mt-2 text-sm text-muted-foreground">{updated}</p>
            </div>
            <div className="p-6 space-y-8">
              <p className="leading-relaxed text-card-foreground/90">{intro}</p>
              {sections.map((section, i) => (
                <section key={i} className="space-y-3">
                  <h2 className="text-lg font-semibold">{section.title}</h2>
                  <p className="leading-relaxed text-card-foreground/90">{section.p1}</p>
                  {section.p2 ? (
                    <p className="leading-relaxed text-card-foreground/90">{section.p2}</p>
                  ) : null}
                </section>
              ))}
            </div>
          </Card>
        </div>
      </main>
      <footer className="border-t bg-card px-6 py-4">
        <div className="mx-auto flex max-w-3xl items-center justify-between gap-2 text-xs text-muted-foreground">
          <span>© {new Date().getFullYear()} {t("app.name")}</span>
          <div className="flex gap-4">
            <Link to="/privacy" className="hover:text-foreground">
              {t("legal.privacyTitle")}
            </Link>
            <Link to="/terms" className="hover:text-foreground">
              {t("legal.termsTitle")}
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
