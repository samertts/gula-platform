import { useQuery } from "@tanstack/react-query";
import { criticalAlertsApi } from "@/api/endpoints";
import { Badge, Card, CardContent, CardHeader, CardTitle, DataTable } from "@/components/ui";
import { LoadingSpinner, ErrorDisplay, EmptyState } from "@/components/shared/PageComponents";
import type { ColumnDef } from "@tanstack/react-table";
import type { CriticalAlert } from "@/types";
import { AlertTriangle, CheckCircle2, ShieldCheck } from "lucide-react";

export function CriticalAlertsPage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["critical-alerts"],
    queryFn: () => criticalAlertsApi.list({}),
  });

  const columns: ColumnDef<CriticalAlert>[] = [
    { accessorKey: "order_id", header: "رقم الطلب" },
    {
      accessorKey: "critical_tests",
      header: "الفحوصات الحرجة",
      cell: ({ row }) => (row.original.critical_tests || []).join(", "),
    },
    { accessorKey: "token_prefix", header: "رمز" },
    { accessorKey: "created_at", header: "التاريخ" },
  ];

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  const alerts: CriticalAlert[] = Array.isArray(data) ? data : [];

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <section className="flex flex-col gap-4 rounded-[1.5rem] border border-rose-200/80 bg-white p-5 shadow-[0_18px_44px_-36px_rgba(15,23,42,0.48)] dark:border-rose-900/50 dark:bg-slate-900/70 sm:flex-row sm:items-end sm:justify-between sm:p-6">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-rose-100 bg-rose-50 px-3 py-1.5 text-xs font-bold text-rose-700 dark:border-rose-900/60 dark:bg-rose-950/35 dark:text-rose-200"><AlertTriangle className="h-3.5 w-3.5" /> أولوية سريرية</div>
          <h1 className="text-2xl font-bold tracking-tight text-[#0F172A] dark:text-white sm:text-3xl">التنبيهات الحرجة</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">واجهة متابعة عالية الوضوح للنتائج الحرجة المتاحة في سياقك. الاستعراض البصري لا يغيّر حالة أي تنبيه أو سجل سريري.</p>
        </div>
        <div className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-700 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-200"><ShieldCheck className="h-4 w-4 shrink-0 text-[#0D9488]" /><span><strong>عرض محكوم</strong><br /><span className="text-slate-500 dark:text-slate-400">لا يتم الإقرار أو الإغلاق تلقائيًا</span></span></div>
      </section>

      <Card className="overflow-hidden border-rose-100 dark:border-rose-900/40">
        <CardHeader className="flex flex-col gap-3 border-b border-rose-100/80 p-5 dark:border-rose-900/40 sm:flex-row sm:items-center sm:justify-between sm:p-6">
          <div><CardTitle className="flex items-center gap-2 text-base"><AlertTriangle className="h-5 w-5 text-rose-600" /> قائمة التنبيهات</CardTitle><p className="mt-1 text-xs text-muted-foreground">رتّب الأولويات بحسب سياسات العمل المعتمدة في منشأتك.</p></div>
          <Badge variant={alerts.length > 0 ? "destructive" : "secondary"} className="w-fit px-3 py-1.5 text-xs"><AlertTriangle className="h-3.5 w-3.5" />{alerts.length > 0 ? `${alerts.length} تنبيه` : "لا توجد تنبيهات"}</Badge>
        </CardHeader>
        <CardContent className="p-4 pt-4 sm:p-6 sm:pt-5">
          {alerts.length === 0 ? (
            <EmptyState icon={CheckCircle2} title="لا توجد تنبيهات حرجة" description="لا توجد عناصر حرجة ظاهرة ضمن الاستعلام الحالي." />
          ) : (
            <DataTable columns={columns} data={alerts} loading={isLoading} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
