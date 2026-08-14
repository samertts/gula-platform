import { useQuery } from "@tanstack/react-query";
import { qcApi } from "@/api/endpoints";
import { Badge, Card, CardContent, CardHeader, CardTitle, DataTable } from "@/components/ui";
import { LoadingSpinner, ErrorDisplay, EmptyState } from "@/components/shared/PageComponents";
import type { ColumnDef } from "@tanstack/react-table";
import type { QualityControl } from "@/types";
import { CheckCircle2, CircleAlert, ClipboardCheck, ShieldCheck } from "lucide-react";

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
  passed: "success",
  failed: "destructive",
  warning: "warning",
  pending: "secondary",
};

const statusLabel: Record<string, string> = {
  passed: "مطابق",
  failed: "غير مطابق",
  warning: "يحتاج مراجعة",
  pending: "قيد التقييم",
};

export function QCPage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["qc"],
    queryFn: () => qcApi.list({ limit: 50 }),
  });

  const columns: ColumnDef<QualityControl>[] = [
    { accessorKey: "test_code", header: "رمز الفحص" },
    { accessorKey: "lot_number", header: "رقم التشغيلة" },
    { accessorKey: "measured_value", header: "القيمة" },
    { accessorKey: "expected_value", header: "القيمة المستهدفة" },
    {
      accessorKey: "status",
      header: "الحالة",
      cell: ({ row }) => (
        <Badge variant={statusVariant[row.original.status] || "secondary"} className="whitespace-nowrap">
          {statusLabel[row.original.status] || row.original.status}
        </Badge>
      ),
    },
    { accessorKey: "created_at", header: "التاريخ" },
  ];

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  const items = data?.qc_results ?? [];
  const passedCount = items.filter((item) => item.status === "passed").length;
  const attentionCount = items.filter((item) => item.status === "failed" || item.status === "warning").length;

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <section className="flex flex-col gap-4 rounded-[1.5rem] border border-emerald-100 bg-white p-5 shadow-[0_18px_44px_-36px_rgba(15,23,42,0.48)] dark:border-emerald-900/40 dark:bg-slate-900/70 sm:flex-row sm:items-end sm:justify-between sm:p-6">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-emerald-100 bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-700 dark:border-emerald-900/60 dark:bg-emerald-950/35 dark:text-emerald-200"><ClipboardCheck className="h-3.5 w-3.5" /> ضمان جودة تشغيلي</div>
          <h1 className="text-2xl font-bold tracking-tight text-[#0F172A] dark:text-white sm:text-3xl">مراقبة الجودة</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">عرض منضبط لآخر نتائج ضبط الجودة المتاحة داخل مساحة العمل. أي إجراءات تحليلية أو تصحيحية تبقى ضمن الإجراء المؤسسي المعتمد.</p>
        </div>
        <div className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-700 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-200"><ShieldCheck className="h-4 w-4 shrink-0 text-[#0D9488]" /><span><strong>وضع الاستعراض</strong><br /><span className="text-slate-500 dark:text-slate-400">لا تُنشأ أو تُعدّل نتائج من هذه الصفحة</span></span></div>
      </section>

      <section className="grid gap-3 sm:grid-cols-3">
        <Card className="border-emerald-100 dark:border-emerald-900/40"><CardContent className="p-4"><p className="text-xs font-medium text-muted-foreground">العناصر المعروضة</p><p className="mt-2 text-2xl font-bold text-[#0F172A] dark:text-white">{items.length}</p></CardContent></Card>
        <Card className="border-emerald-100 dark:border-emerald-900/40"><CardContent className="p-4"><p className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground"><CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" /> مطابقة</p><p className="mt-2 text-2xl font-bold text-emerald-700 dark:text-emerald-300">{passedCount}</p></CardContent></Card>
        <Card className="border-amber-100 dark:border-amber-900/40"><CardContent className="p-4"><p className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground"><CircleAlert className="h-3.5 w-3.5 text-amber-600" /> تحتاج انتباهًا</p><p className="mt-2 text-2xl font-bold text-amber-700 dark:text-amber-300">{attentionCount}</p></CardContent></Card>
      </section>

      <Card className="overflow-hidden border-emerald-100 dark:border-emerald-900/40">
        <CardHeader className="border-b border-emerald-100/80 p-5 dark:border-emerald-900/40 sm:p-6"><CardTitle className="flex items-center gap-2 text-base"><ShieldCheck className="h-5 w-5 text-[#0D9488]" /> سجل نتائج ضبط الجودة</CardTitle><p className="mt-1 text-xs text-muted-foreground">آخر 50 سجلًا وفق النطاق والصلاحيات المفروضة من الخادم.</p></CardHeader>
        <CardContent className="p-4 pt-4 sm:p-6 sm:pt-5">
          {items.length === 0 ? (
            <EmptyState icon={ShieldCheck} title="لا توجد نتائج جودة" description="لا توجد نتائج QC ظاهرة ضمن مساحة العمل والاستعلام الحالي." />
          ) : (
            <DataTable columns={columns} data={items} loading={isLoading} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
