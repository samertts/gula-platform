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
  const { data: daily } = useQuery({
    queryKey: ["stats", "daily"],
    queryFn: () => statsApi.dailyTrends({ days: 14 }),
  });
  const { data: tests } = useQuery({
    queryKey: ["stats", "tests"],
    queryFn: () => statsApi.testFrequency({ days: 14, limit: 8 }),
  });
  const { data: flags } = useQuery({
    queryKey: ["stats", "flags"],
    queryFn: () => statsApi.flagDistribution({ days: 14 }),
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  const series = daily?.series ?? [];
  const maxOrders = Math.max(...series.map((p) => p.orders ?? 0), 1);
  const testSeries = tests?.series ?? [];
  const maxTests = Math.max(...testSeries.map((t) => t.count), 1);
  const flagEntries = Object.entries(flags?.distribution ?? {});

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
              <p className="text-2xl font-bold">{data?.total_patients ?? 0}</p>
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
              <p className="text-2xl font-bold">{data?.total_orders ?? 0}</p>
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
              <p className="text-2xl font-bold">{data?.active_users ?? 0}</p>
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
              <p className="text-2xl font-bold">{data?.avg_turnaround ?? "-"}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>الاتجاهات اليومية</CardTitle></CardHeader>
          <CardContent>
            {series.length > 0 ? (
              <div className="space-y-2">
                {series.slice(-14).map((p) => (
                  <div key={p.date} className="flex items-center gap-2">
                    <span className="w-16 shrink-0 text-xs text-muted-foreground" dir="ltr">{p.date}</span>
                    <div className="h-4 flex-1 rounded bg-muted" dir="ltr">
                      <div
                        className="h-4 rounded bg-indigo-500"
                        style={{ width: `${Math.max(((p.orders ?? 0) / maxOrders) * 100, 2)}%` }}
                      />
                    </div>
                    <span className="w-8 shrink-0 text-end text-xs font-medium" dir="ltr">{p.orders ?? 0}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">لا توجد بيانات اتجاهات بعد</p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>توزيع الفحوصات</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {testSeries.length > 0 ? (
              <div className="space-y-2">
                {testSeries.map((t) => (
                  <div key={t.test_name} className="flex items-center gap-2">
                    <span className="w-32 shrink-0 truncate text-xs" dir="ltr">{t.test_name}</span>
                    <div className="h-4 flex-1 rounded bg-muted" dir="ltr">
                      <div
                        className="h-4 rounded bg-emerald-500"
                        style={{ width: `${Math.max((t.count / maxTests) * 100, 2)}%` }}
                      />
                    </div>
                    <span className="w-8 shrink-0 text-end text-xs font-medium" dir="ltr">{t.count}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">لا توجد بيانات توزيع بعد</p>
            )}
            {flagEntries.length > 0 && (
              <div className="border-t pt-3">
                <p className="mb-2 text-sm font-medium">توزيع العلامات (Westgard)</p>
                <div className="space-y-1">
                  {flagEntries.map(([flag, info]) => (
                    <div key={flag} className="flex items-center justify-between text-sm">
                      <span dir="ltr" className="font-mono text-xs">{flag}</span>
                      <span className="text-xs text-muted-foreground" dir="ltr">
                        {info.count} ({info.percentage}%)
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
