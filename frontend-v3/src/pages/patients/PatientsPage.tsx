import { useQuery } from "@tanstack/react-query";
import { Badge, Card, CardContent, CardHeader, CardTitle, DataTable, Input } from "@/components/ui";
import { EmptyState } from "@/components/ui/EmptyState";
import { WorkspaceReadBlockedError, workspaceScopedReads } from "@/api/workspaceScopedReads";
import { Search, ShieldAlert, ShieldCheck, Users } from "lucide-react";
import { useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import type { Patient } from "@/types";
import { formatDate, getGenderLabel } from "@/lib/utils";

export function PatientsPage() {
  const [search, setSearch] = useState("");
  const columns: ColumnDef<Patient>[] = [
    { accessorKey: "full_name", header: "الاسم" },
    { accessorKey: "phone", header: "الهاتف" },
    {
      accessorKey: "gender",
      header: "الجنس",
      cell: ({ row }) => <Badge variant="secondary">{getGenderLabel(row.original.gender)}</Badge>,
    },
    {
      accessorKey: "date_of_birth",
      header: "تاريخ الميلاد",
      cell: ({ row }) => formatDate(row.original.birth_date),
    },
    { accessorKey: "national_id", header: "الرقم الوطني" },
    { accessorKey: "lab_id", header: "رقم المختبر" },
  ];

  const query = useQuery({
    queryKey: ["patients", "patients.read", search],
    queryFn: () => workspaceScopedReads.listPatients({ search, limit: 50 }),
    retry: false,
  });
  const blockedMessage = query.error instanceof WorkspaceReadBlockedError ? query.error.message : null;

  return (
    <div
      className="mx-auto max-w-7xl space-y-6"
      data-contract-id="patients.read"
      data-permission="patients:read"
      data-workspace-context="required"
    >
      <section className="flex flex-col gap-4 rounded-[1.5rem] border border-slate-200/80 bg-white p-5 shadow-[0_18px_44px_-36px_rgba(15,23,42,0.48)] dark:border-white/10 dark:bg-slate-900/70 sm:flex-row sm:items-end sm:justify-between sm:p-6">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-teal-100 bg-teal-50 px-3 py-1.5 text-xs font-bold text-[#0D9488] dark:border-teal-900/60 dark:bg-teal-950/35 dark:text-teal-200">
            <Users className="h-3.5 w-3.5" /> سجل المرضى
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-[#0F172A] dark:text-white sm:text-3xl">المرضى المصرّح لهم</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">ابحث ضمن مساحة العمل النشطة فقط. لا يتم تحميل أو عرض أي سجل قبل تحقق الخادم من الصلاحية وسياق المؤسسة.</p>
        </div>
        <div className="inline-flex items-center gap-2 rounded-2xl border border-emerald-100 bg-emerald-50 px-3.5 py-2.5 text-xs text-emerald-800 dark:border-emerald-900/50 dark:bg-emerald-950/25 dark:text-emerald-200">
          <ShieldCheck className="h-4 w-4 shrink-0" /><span><strong>قراءة محكومة</strong><br /><span className="text-emerald-700/75 dark:text-emerald-200/70">نطاق مساحة العمل إلزامي</span></span>
        </div>
      </section>

      <Card className="overflow-hidden">
        <CardHeader className="flex flex-col gap-3 border-b border-slate-100 p-5 dark:border-white/10 sm:flex-row sm:items-center sm:justify-between sm:p-6">
          <div>
            <CardTitle className="flex items-center gap-2 text-base"><Users className="h-5 w-5 text-[#0D9488]" /> قائمة المرضى</CardTitle>
            <p className="mt-1 text-xs text-muted-foreground">تظهر النتائج المطابقة لنطاقك المصرح به فقط.</p>
          </div>
          <span className="w-fit rounded-full bg-slate-100 px-2.5 py-1 text-[10px] font-bold text-slate-600 dark:bg-white/10 dark:text-slate-300">قراءة فقط</span>
        </CardHeader>
        <CardContent className="p-4 pt-4 sm:p-6 sm:pt-5">
          {blockedMessage ? (
            <EmptyState
              icon={ShieldAlert}
              title="قراءة المرضى غير متاحة لهذه الجلسة"
              description={blockedMessage}
            />
          ) : <DataTable
            columns={columns}
            data={query.data ?? []}
            loading={query.isLoading}
            toolbar={
              <div className="relative w-full sm:w-80">
                <label className="sr-only" htmlFor="patient-search">بحث ضمن المرضى المصرح بهم</label>
                <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#0D9488]" />
                <Input
                  id="patient-search"
                  placeholder="بحث ضمن المرضى المصرح بهم…"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  className="h-10 w-full rounded-xl border-slate-200 bg-slate-50 ps-9 shadow-sm focus-visible:border-teal-400 dark:border-white/10 dark:bg-white/[0.04]"
                />
              </div>
            }
          />}
        </CardContent>
      </Card>
    </div>
  );
}
