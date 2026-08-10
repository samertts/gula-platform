import { useParams } from "react-router";
import { useTranslation } from "react-i18next";
import { Card, CardHeader, CardTitle, CardContent, Badge } from "@/components/ui";
import { demoConfig } from "./config";
import { DEMO_VIEWS } from "./mockData";
import { isDemoProfileId } from "./profiles";
import { readDemoSession } from "./session";

export function DemoDashboardPage() {
  const { profile } = useParams();
  const { t, i18n } = useTranslation();

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

  const view = DEMO_VIEWS[profile];
  if (!view) return null;

  const lang = i18n.language === "en" ? "en" : "ar";

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-bold">{lang === "en" ? view.titleEn : view.title}</h1>
          <p className="text-muted-foreground">{lang === "en" ? view.subtitleEn : view.subtitle}</p>
        </div>
        <Badge variant="warning">{t("demo.readOnlyBadge")}</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {view.stats.map((stat) => (
          <Card key={stat.labelEn}>
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground">{lang === "en" ? stat.labelEn : stat.label}</p>
              <p className="text-2xl font-bold">{stat.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {view.cards.map((card) => (
          <Card key={card.titleEn}>
            <CardHeader>
              <CardTitle className="text-base">{lang === "en" ? card.titleEn : card.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <table className="w-full text-sm">
                <tbody>
                  {card.rows.map((row) => (
                    <tr key={row.labelEn} className="border-b last:border-0">
                      <td className="py-2 text-muted-foreground">
                        {lang === "en" ? row.labelEn : row.label}
                      </td>
                      <td className="py-2 text-end font-medium">
                        {lang === "en" && row.valueEn ? row.valueEn : row.value}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        ))}
      </div>

      <p className="text-center text-xs text-muted-foreground">{t("demo.notice")}</p>
    </div>
  );
}
