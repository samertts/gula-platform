import { useEffect } from "react";
import { Outlet, useNavigate, useParams } from "react-router";
import { useTranslation } from "react-i18next";
import { Button, Badge } from "@/components/ui";
import { demoConfig } from "./config";
import { isDemoProfileId } from "./profiles";
import { exitDemo, readDemoSession } from "./session";
import { Eye, LogOut } from "lucide-react";

export function DemoLayout() {
  const { profile } = useParams();
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const lang = i18n.language === "en" ? "en" : "ar";

  useEffect(() => {
    if (!demoConfig.enabled) {
      exitDemo();
      navigate("/login", { replace: true });
      return;
    }
    const session = readDemoSession();
    if (!session || !profile || !isDemoProfileId(profile) || session.profileId !== profile) {
      navigate("/demo", { replace: true });
      return;
    }
    const onFocus = () => {
      if (!demoConfig.enabled) {
        exitDemo();
        navigate("/login", { replace: true });
      }
    };
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [navigate, profile]);

  const session = readDemoSession();
  if (
    !demoConfig.enabled ||
    !session ||
    !profile ||
    !isDemoProfileId(profile) ||
    session.profileId !== profile
  ) {
    return null;
  }

  const handleExit = () => {
    exitDemo();
    navigate("/login", { replace: true });
  };

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <div
        role="status"
        aria-label={t("demo.banner")}
        className="flex items-center justify-center gap-2 bg-amber-100 px-4 py-2 text-center text-sm font-semibold text-amber-900 dark:bg-amber-900/40 dark:text-amber-200"
      >
        <Eye className="h-4 w-4 shrink-0" />
        <span>{t("demo.banner")}</span>
        <Badge variant="warning">{t("demo.readOnly")}</Badge>
      </div>

      <header className="flex h-14 items-center justify-between gap-4 border-b bg-card px-6">
        <div className="flex items-center gap-3">
          <Eye className="h-5 w-5 text-primary" />
          <span className="font-bold">{t("demo.title")}</span>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="warning">DEMO</Badge>
          <div className="text-sm">
            <p className="font-medium">{lang === "en" ? session.displayNameEn : session.displayName}</p>
            <p className="text-xs text-muted-foreground">
              {lang === "en" ? "Read-only preview session" : "جلسة عرض للقراءة فقط"}
            </p>
          </div>
          <Button variant="destructive" size="sm" onClick={handleExit}>
            <LogOut className="h-4 w-4" />
            {t("demo.exit")}
          </Button>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}
