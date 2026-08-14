import { useQuery } from "@tanstack/react-query";
import { Badge, Card, CardContent, CardHeader, CardTitle, DataTable, Input } from "@/components/ui";
import { EmptyState } from "@/components/ui/EmptyState";
import { WorkspaceReadBlockedError, workspaceScopedReads } from "@/api/workspaceScopedReads";
import type { ClinicalOrderRead } from "@/api/workspaceScopedReads";
import { ClipboardList, Search, ShieldAlert, ShieldCheck } from "lucide-react";
import { useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import { formatDate } from "@/lib/utils";

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
  pending: "warning",
  completed: "success",
  validated: "default",
  cancelled: "destructive",
  in_progress: "secondary",
};

const statusLabel: Record<string, string> = {
  pending: "قيد الانتظار",
  completed: "مكتمل",
  validated: "مُعتمد",
  cancelled: "ملغى",
  in_progress: "قيد التنفيذ",
};

export function OrdersPage() {
  const [search, setSearch] = useState("");
  const query = useQuery({
    queryKey: ["orders", "orders.read", search],
    queryFn: () => workspaceScopedReads.listOrders({ search, limit: 50 }),
    retry: false,
  });
  const blockedMessage = query.error instanceof WorkspaceReadBlockedError ? query.error.message : null;

  const columns: ColumnDef<ClinicalOrderRead>[] = [
    { accessorKey: "id", header: "رقم الطلب" },
    { accessorKey: "patient_display_name", header: "اسم المريض" },
    { accessorKey: "practitioner_display_name", header: "اسم الطبيب" },
    {
      accessorKey: "status",
      header: "الحالة",
      cell: ({ row }) => (
        <Badge variant={statusVariant[row.original.status] || "secondary"}>
          {statusLabel[row.original.status] || row.original.status}
        </Badge>
      ),
    },
    {
      accessorKey: "test_count",
      header: "عدد الفحوصات",
      cell: ({ row }) => row.original.test_count ?? "-",
    },
    {
      accessorKey: "created_at",
      header: "تاريخ الإنشاء",
      cell: ({ row }) => formatDate(row.original.created_at),
    },
  ];

  return (
    <div
      className="mx-auto max-w-7xl space-y-6"
      data-contract-id="orders.read"
      data-permission="orders.read"
      data-workspace-context="required"
    >
      <section className="flex flex-col gap-4 rounded-[1.5rem] border border-slate-200/80 bg-white p-5 shadow-[0_18px_44px_-36px_rgba(15,23,42,0.48)] dark:border-white/10 dark:bg-slate-900/70 sm:flex-row sm:items-end sm:justify-between sm:p-6">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-sky-100 bg-sky-50 px-3 py-1.5 text-xs font-bold text-sky-700 dark:border-sky-900/60 dark:bg-sky-950/35 dark:text-sky-200"><ClipboardList className="h-3.5 w-3.5" /> سير طلبات الفحوصات</div>
          <h1 className="text-2xl font-bold tracking-tight text-[#0F172A] dark:text-white sm:text-3xl">الطلبات المصرّح بها</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">تابع مراحل الطلبات ضمن مساحة العمل الحالية فقط. لا يتيح هذا السطح أي انتقال سريري أو عملية كتابة غير مصادق عليها من الخادم.</p>
        </div>
        <div className="inline-flex items-center gap-2 rounded-2xl border border-emerald-100 bg-emerald-50 px-3.5 py-2.5 text-xs text-emerald-800 dark:border-emerald-900/50 dark:bg-emerald-950/25 dark:text-emerald-200"><ShieldCheck className="h-4 w-4 shrink-0" /><span><strong>قراءة محكومة</strong><br /><span className="text-emerald-700/75 dark:text-emerald-200/70">الحالة الفعلية تأتي من العقد المعتمد</span></span></div>
      </section>

      <Card className="overflow-hidden">
        <CardHeader className="flex flex-col gap-3 border-b border-slate-100 p-5 dark:border-white/10 sm:flex-row sm:items-center sm:justify-between sm:p-6">
          <div><CardTitle className="flex items-center gap-2 text-base"><ClipboardList className="h-5 w-5 text-sky-600" /> قائمة الطلبات</CardTitle><p className="mt-1 text-xs text-muted-foreground">ابحث عن الطلبات المتاحة في نطاق منشأتك فقط.</p></div>
          <span className="w-fit rounded-full bg-slate-100 px-2.5 py-1 text-[10px] font-bold text-slate-600 dark:bg-white/10 dark:text-slate-300">قراءة فقط</span>
        </CardHeader>
        <CardContent className="p-4 pt-4 sm:p-6 sm:pt-5">
          {blockedMessage ? (
            <EmptyState icon={ShieldAlert} title="قراءة الطلبات غير متاحة لهذه الجلسة" description={blockedMessage} />
          ) : <DataTable
            columns={columns}
            data={query.data ?? []}
            loading={query.isLoading}
            toolbar={
              <div className="relative w-full sm:w-80">
                <label className="sr-only" htmlFor="order-search">بحث ضمن الطلبات المصرح بها</label>
                <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-sky-600" />
                <Input id="order-search" placeholder="بحث ضمن الطلبات المصرح بها…" value={search} onChange={(event) => setSearch(event.target.value)} className="h-10 w-full rounded-xl border-slate-200 bg-slate-50 ps-9 shadow-sm focus-visible:border-sky-400 dark:border-white/10 dark:bg-white/[0.04]" />
              </div>
            }
          />}
        </CardContent>
      </Card>
    </div>
  );
}
