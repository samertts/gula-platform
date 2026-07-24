import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { dashboardApi } from "@/api/endpoints";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui";
import { Users, ClipboardList, FlaskConical, AlertTriangle } from "lucide-react";

export function DashboardPage() {
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => dashboardApi.dashboard(),
  });

  const statCards = [
    { label: t("dashboard.totalPatients"), key: "total_patients", icon: Users, color: "text-blue-600 bg-blue-100 dark:bg-blue-900/30" },
    { label: t("dashboard.todayOrders"), key: "today_orders", icon: ClipboardList, color: "text-emerald-600 bg-emerald-100 dark:bg-emerald-900/30" },
    { label: t("dashboard.todayResults"), key: "today_results", icon: FlaskConical, color: "text-purple-600 bg-purple-100 dark:bg-purple-900/30" },
    { label: t("dashboard.criticalAlerts"), key: "critical_alerts", icon: AlertTriangle, color: "text-red-600 bg-red-100 dark:bg-red-900/30" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t("dashboard.title")}</h1>
        <p className="text-muted-foreground">{t("dashboard.subtitle")}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {statCards.map((card) => (
          <Card key={card.key}>
            <CardContent className="flex items-center gap-4 p-6">
              <div className={`flex h-12 w-12 items-center justify-center rounded-full ${card.color}`}>
                <card.icon className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">{card.label}</p>
                <p className="text-2xl font-bold">
                  {isLoading ? "..." : (data as any)?.[card.key] ?? 0}
                </p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>{t("dashboard.recentOrders")}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{t("dashboard.recentOrdersPlaceholder")}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>{t("dashboard.recentActivity")}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{t("dashboard.recentActivityPlaceholder")}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}