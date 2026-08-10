import { useEffect } from "react";
import { useNavigate } from "react-router";
import { useTranslation } from "react-i18next";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, Button } from "@/components/ui";
import { demoConfig } from "./config";
import { DEMO_PROFILES, DEMO_PROFILE_IDS, type DemoProfileId } from "./profiles";
import { enterDemo } from "./session";
import {
  User,
  Stethoscope,
  TestTube,
  HeartPulse,
  Building2,
  Eye,
  ArrowLeft,
  ArrowRight,
} from "lucide-react";

const iconMap = {
  User,
  Stethoscope,
  TestTube,
  HeartPulse,
  Building2,
} as const;

export function DemoLoginPage() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const isRTL = i18n.language !== "en";

  useEffect(() => {
    if (!demoConfig.enabled) {
      navigate("/login", { replace: true });
    }
  }, [navigate]);

  if (!demoConfig.enabled) return null;

  const handleSelect = (id: DemoProfileId) => {
    const session = enterDemo(id);
    if (session) {
      navigate(`/demo/${id}`);
    }
  };

  const BackIcon = isRTL ? ArrowRight : ArrowLeft;

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader className="text-center">
          <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
            <Eye className="h-6 w-6 text-primary" />
          </div>
          <CardTitle className="text-2xl">{t("demo.title")}</CardTitle>
          <CardDescription>{t("demo.subtitle")}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2">
            {DEMO_PROFILE_IDS.map((id) => {
              const profile = DEMO_PROFILES[id]!;
              const Icon = iconMap[profile.icon as keyof typeof iconMap] ?? User;
              return (
                <Button
                  key={id}
                  type="button"
                  variant="outline"
                  className="flex h-auto flex-col items-start gap-2 p-4 text-start"
                  onClick={() => handleSelect(id)}
                >
                  <span className="flex items-center gap-2 font-semibold">
                    <Icon className="h-5 w-5 text-primary" />
                    <span>{t(`demo.profiles.${id}`)}</span>
                  </span>
                  <span className="text-xs text-muted-foreground">{t(`demo.profilesDesc.${id}`)}</span>
                </Button>
              );
            })}
          </div>
          <div className="mt-6 flex justify-center">
            <Button variant="ghost" onClick={() => navigate("/login")}>
              <BackIcon className="h-4 w-4" />
              {t("auth.back")}
            </Button>
          </div>
          <p className="mt-4 text-center text-xs text-muted-foreground">{t("demo.notice")}</p>
        </CardContent>
      </Card>
    </div>
  );
}
