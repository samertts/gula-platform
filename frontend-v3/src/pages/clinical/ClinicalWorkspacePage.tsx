import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import type { ColumnDef } from "@tanstack/react-table";
import { Activity, ClipboardList, FlaskConical, Search, ShieldAlert, ShieldCheck, Users } from "lucide-react";
import { workspaceScopedReads, WorkspaceReadBlockedError } from "@/api/workspaceScopedReads";
import type { ClinicalOrderRead, ClinicalPatientRead } from "@/api/workspaceScopedReads";
import { Badge, Card, CardContent, CardHeader, CardTitle, DataTable, Input } from "@/components/ui";
import { EmptyState } from "@/components/ui/EmptyState";

 type ClinicalTab = "patients" | "orders";

const orderStatus: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" | "success" | "warning" }> = {
  pending: { label: "قيد الانتظار", variant: "warning" },
  in_progress: { label: "قيد التنفيذ", variant: "secondary" },
  completed: { label: "مكتمل", variant: "success" },
  validated: { label: "مُعتمد", variant: "default" },
  cancelled: { label: "ملغى", variant: "destructive" },
};

export function ClinicalWorkspacePage() {
  const [tab, setTab] = useState<ClinicalTab>("patients");
  const [search, setSearch] = useState("");
  const patients = useQuery({
    queryKey: ["clinicalWorkspace", "patients", search],
    queryFn: () => workspaceScopedReads.listPatients({ search: search || undefined, limit: 50 }),
    retry: false,
  });
  const orders = useQuery({
    queryKey: ["clinicalWorkspace", "orders", search],
    queryFn: () => workspaceScopedReads.listOrders({ search: search || undefined, limit: 50 }),
    retry: false,
  });

  const activeQuery = tab === "patients" ? patients : orders;
  const blockedMessage = activeQuery.error instanceof WorkspaceReadBlockedError ? activeQuery.error.message : null;

  const patientColumns: ColumnDef<ClinicalPatientRead>[] = [
    { accessorKey: "display_name", header: "اسم المريض" },
    { accessorKey: "gender", header: "الجنس", cell: ({ row }) => row.original.gender ?? "—" },
    { accessorKey: "birth_date", header: "تاريخ الميلاد", cell: ({ row }) => row.original.birth_date ?? "—" },
  ];
  const orderColumns: ColumnDef<ClinicalOrderRead>[] = [
    { accessorKey: "id", header: "رقم الطلب" },
    { accessorKey: "patient_display_name", header: "المريض", cell: ({ row }) => row.original.patient_display_name ?? "—" },
    { accessorKey: "practitioner_display_name", header: "الطبيب", cell: ({ row }) => row.original.practitioner_display_name ?? "—" },
    { accessorKey: "status", header: "الحالة", cell: ({ row }) => { const state = orderStatus[row.original.status] ?? { label: row.original.status, variant: "outline" as const }; return <Badge variant={state.variant}>{state.label}</Badge>; } },
    { accessorKey: "test_count", header: "الفحوصات" },
  ];

  return (
    <div className="mx-auto max-w-7xl space-y-6" dir="rtl" data-contract-id={tab === "patients" ? "patients.read" : "orders.read"} data-workspace-context="required">
      <section className="rounded-[1.5rem] border border-sky-100 bg-gradient-to-l from-sky-50 via-white to-teal-50 p-5 shadow-sm dark:border-white/10 dark:from-sky-950/30 dark:via-slate-900 dark:to-teal-950/25 sm:p-6">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-3xl">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-sky-100 bg-white/80 px-3 py-1.5 text-xs font-bold text-sky-700 dark:border-sky-900/60 dark:bg-white/5 dark:text-sky-200"><Activity className="h-3.5 w-3.5" /> مساحة سريرية محكومة</div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-3xl">ابدأ يومك السريري من صورة موثوقة</h1>
            <p className="mt-2 text-sm leading-7 text-muted-foreground">قائمة المرضى والطلبات ضمن مساحة العمل الحالية فقط. لا تعتمد هذه الصفحة على رقم هاتف أو سياق يختاره العميل، وكل قراءة تمر من البوابة الخادمية المعتمدة.</p>
          </div>
          <div className="flex items-center gap-2 rounded-2xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-xs text-emerald-800 dark:border-emerald-900/50 dark:bg-emerald-950/25 dark:text-emerald-200"><ShieldCheck className="h-4 w-4" /> قراءة محكومة وعزل مؤسسي</div>
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-2"><Metric icon={Users} label="المرضى المصرح لهم" value={patients.data?.length ?? 0} /><Metric icon={ClipboardList} label="الطلبات المصرح بها" value={orders.data?.length ?? 0} /></div>

      <Card className="overflow-hidden">
        <CardHeader className="flex flex-col gap-3 border-b p-5 sm:flex-row sm:items-center sm:justify-between">
          <div><CardTitle className="flex items-center gap-2 text-base"><FlaskConical className="h-5 w-5 text-sky-600" /> العمليات السريرية</CardTitle><p className="mt-1 text-xs text-muted-foreground">النتائج الظاهرة هنا هي DTOs دنيا من العقد canonical؛ لا تعرض أرقام هوية أو هاتف أو lab_id.</p></div>
          <div className="relative w-full sm:w-80"><label className="sr-only" htmlFor="clinical-search">بحث ضمن مساحة العمل</label><Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-sky-600" /><Input id="clinical-search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="بحث بالاسم أو الطلب…" className="h-10 ps-9" /></div>
        </CardHeader>
        <CardContent className="p-5">
          <div className="mb-5 flex flex-wrap gap-2" role="tablist" aria-label="العمليات السريرية">
            <TabButton selected={tab === "patients"} onClick={() => setTab("patients")} icon={Users}>المرضى</TabButton>
            <TabButton selected={tab === "orders"} onClick={() => setTab("orders")} icon={ClipboardList}>طلبات الفحوصات</TabButton>
          </div>
          {blockedMessage ? <EmptyState icon={ShieldAlert} title="القراءة غير متاحة لهذه الجلسة" description={blockedMessage} /> : tab === "patients" ? <DataTable columns={patientColumns} data={patients.data ?? []} loading={patients.isLoading} /> : <DataTable columns={orderColumns} data={orders.data ?? []} loading={orders.isLoading} />}
        </CardContent>
      </Card>

      <Card className="border-amber-200 bg-amber-50/60 dark:border-amber-900/50 dark:bg-amber-950/20"><CardContent className="p-5 text-sm leading-7 text-amber-900 dark:text-amber-200"><strong>حدود آمنة:</strong> هذه الدفعة قراءة فقط. نتائج المختبر التفصيلية تبقى محجوبة عن الواجهة حتى يكتمل عقد `results.read` وDTO minimal وسجل تدقيق مناسب؛ لا يوجد fallback إلى REST legacy. <Link className="font-semibold underline" to="/lab-operations">فتح تشغيل المختبر المعزول</Link></CardContent></Card>
    </div>
  );
}

function Metric({ icon: Icon, label, value }: { icon: typeof Users; label: string; value: number }) { return <Card><CardContent className="flex items-center justify-between p-4"><div><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 text-2xl font-bold">{value}</p></div><Icon className="h-5 w-5 text-sky-600" /></CardContent></Card>; }
function TabButton({ selected, onClick, icon: Icon, children }: { selected: boolean; onClick: () => void; icon: typeof Users; children: string }) { return <button type="button" role="tab" aria-selected={selected} onClick={onClick} className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition ${selected ? "bg-sky-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-white/10 dark:text-slate-200"}`}><Icon className="h-4 w-4" />{children}</button>; }
