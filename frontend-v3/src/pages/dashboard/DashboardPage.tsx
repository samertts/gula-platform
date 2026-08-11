import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/api/endpoints";
import { useAuth } from "@/contexts/AuthContext";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui";
import { Activity, AlertTriangle, ClipboardList, FlaskConical, ShieldCheck, Users } from "lucide-react";

const statCards = [
  { label: "إجمالي المرضى", key: "total_patients", icon: Users, color: "text-blue-600 bg-blue-100 dark:bg-blue-900/30" },
  { label: "الطلبات اليوم", key: "today_orders", icon: ClipboardList, color: "text-emerald-600 bg-emerald-100 dark:bg-emerald-900/30" },
  { label: "النتائج اليوم", key: "today_results", icon: FlaskConical, color: "text-purple-600 bg-purple-100 dark:bg-purple-900/30" },
  { label: "التنبيهات الحرجة", key: "critical_alerts", icon: AlertTriangle, color: "text-red-600 bg-red-100 dark:bg-red-900/30" },
];

export function DashboardPage() {
  const { demoMode } = useAuth();
  const { data, isLoading } = useQuery<Record<string, unknown>>({
    queryKey: ["dashboard", demoMode ? "demo" : "institution"],
    queryFn: async () => {
      if (demoMode) return dashboardApi.demo();
      const institutionDashboard = await dashboardApi.dashboard();
      return institutionDashboard as unknown as Record<string, unknown>;
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold text-primary">مركز العمليات</p>
          <h1 className="text-2xl font-bold tracking-tight">لوحة التحكم</h1>
          <p className="text-sm text-muted-foreground">نظرة موحّدة على سير العمل والحالة التشغيلية.</p>
        </div>
        {demoMode && (
          <span className="inline-flex items-center gap-2 self-start rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1.5 text-xs text-amber-700 dark:text-amber-300 sm:self-auto">
            <ShieldCheck className="h-4 w-4" /> بيانات اصطناعية فقط
          </span>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {statCards.map((card) => (
          <Card key={card.key} className="transition-shadow hover:shadow-md">
            <CardContent className="flex items-center gap-4 p-5">
              <div className={`flex h-12 w-12 items-center justify-center rounded-2xl ${card.color}`}>
                <card.icon className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">{card.label}</p>
                <p className="text-2xl font-bold">
                  {isLoading ? "..." : data?.[card.key] as string | number ?? 0}
                </p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Activity className="h-5 w-5 text-primary" /> الطلبات الأخيرة</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">سيتم عرض الطلبات الأخيرة هنا ضمن نفس مساحة العمل.</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><ShieldCheck className="h-5 w-5 text-primary" /> حالة التشغيل</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">حالة الصلاحيات، المزامنة، وسجل التدقيق ستظهر ضمن السياق نفسه.</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
