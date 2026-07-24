import { useTranslation } from "react-i18next";
import { Card, CardContent, CardTitle } from "@/components/ui";
import { PageHeader } from "@/components/shared/PageComponents";
import { Settings2, Bell, Shield, Palette, Globe } from "lucide-react";

export function SettingsPage() {
  const { t } = useTranslation();

  const items = [
    { icon: Globe, title: t("settings.languageRegion"), desc: t("settings.languageRegionDesc") },
    { icon: Palette, title: t("settings.appearance"), desc: t("settings.appearanceDesc") },
    { icon: Bell, title: t("settings.notifications"), desc: t("settings.notificationsDesc") },
    { icon: Shield, title: t("settings.security"), desc: t("settings.securityDesc") },
    { icon: Settings2, title: t("settings.general"), desc: t("settings.generalDesc") },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title={t("settings.title")} description={t("settings.description")} />

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {items.map((item) => (
          <Card key={item.title} className="cursor-pointer hover:bg-accent transition-colors">
            <CardContent className="flex items-start gap-4 p-6">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10">
                <item.icon className="h-5 w-5 text-primary" />
              </div>
              <div>
                <CardTitle className="text-base">{item.title}</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">{item.desc}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}