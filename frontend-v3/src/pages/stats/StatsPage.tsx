import { useQuery } from "@tanstack/react-query";
import { statsApi } from "@/api/endpoints";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui";
import { PageHeader, LoadingSpinner, ErrorDisplay } from "@/components/shared/PageComponents";
import { TrendingUp, Activity, Users, Clock } from "lucide-react";

export function StatsPage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["stats"],
    queryFn: () => statsApi.summary(),
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  return (
    <div className="space-y-6">
      <PageHeader title="الإحصائيات" description="إحصائيات وتحليلات أداء المختبر" />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="flex items-center gap-4 p-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30">
              <TrendingUp className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">إجمالي المرضى</p>
              <p className="text-2xl font-bold">{(data as any)?.total_patients ?? 0}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 p-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/30">
              <Activity className="h-6 w-6 text-emerald-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">إجمالي الطلبات</p>
              <p className="text-2xl font-bold">{(data as any)?.total_orders ?? 0}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 p-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-purple-100 dark:bg-purple-900/30">
              <Users className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">المستخدمين النشطين</p>
              <p className="text-2xl font-bold">{(data as any)?.active_users ?? 0}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 p-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-900/30">
              <Clock className="h-6 w-6 text-amber-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">مدة الإنجاز</p>
              <p className="text-2xl font-bold">{(data as any)?.avg_turnaround ?? "-"}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>الاتجاهات اليومية</CardTitle></CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">سيتم عرض الرسم البياني للاتجاهات اليومية هنا</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>توزيع الفحوصات</CardTitle></CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">سيتم عرض الرسم البياني لتوزيع الفحوصات هنا</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
