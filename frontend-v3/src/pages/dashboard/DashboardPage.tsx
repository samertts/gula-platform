import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/api/endpoints";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui";
import { Users, ClipboardList, FlaskConical, AlertTriangle } from "lucide-react";

const statCards = [
  { label: "إجمالي المرضى", key: "total_patients", icon: Users, color: "text-blue-600 bg-blue-100 dark:bg-blue-900/30" },
  { label: "الطلبات اليوم", key: "today_orders", icon: ClipboardList, color: "text-emerald-600 bg-emerald-100 dark:bg-emerald-900/30" },
  { label: "النتائج اليوم", key: "today_results", icon: FlaskConical, color: "text-purple-600 bg-purple-100 dark:bg-purple-900/30" },
  { label: "التنبيهات الحرجة", key: "critical_alerts", icon: AlertTriangle, color: "text-red-600 bg-red-100 dark:bg-red-900/30" },
];

export function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => dashboardApi.dashboard(),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">لوحة التحكم</h1>
        <p className="text-muted-foreground">نظرة عامة على أداء المختبر</p>
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
            <CardTitle>الطلبات الأخيرة</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">سيتم عرض الطلبات الأخيرة هنا</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>النشاط الحديث</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">سيتم عرض النشاط الحديث هنا</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
