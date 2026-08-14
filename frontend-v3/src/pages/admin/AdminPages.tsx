import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { adminApi } from "@/api/endpoints";
import { Card, CardContent, CardHeader, CardTitle, Badge, DataTable, Input } from "@/components/ui";
import { LoadingSpinner, ErrorDisplay } from "@/components/shared/PageComponents";
import { Building2, ClipboardList, FileSearch, Search, ShieldCheck, Users, UserRound } from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";
import type { AuditLog, Lab, User } from "@/types";

function AdminHeader({ icon: Icon, eyebrow, title, description }: { icon: typeof Building2; eyebrow: string; title: string; description: string }) {
  return <header className="flex flex-col gap-4 rounded-[1.5rem] border border-teal-100 bg-white p-5 shadow-[0_18px_44px_-36px_rgba(15,23,42,0.48)] dark:border-teal-900/40 dark:bg-slate-900/70 sm:flex-row sm:items-end sm:justify-between sm:p-6"><div><div className="mb-3 inline-flex items-center gap-2 rounded-full border border-teal-100 bg-teal-50 px-3 py-1.5 text-xs font-bold text-[#0D9488] dark:border-teal-900/60 dark:bg-teal-950/35 dark:text-teal-200"><Icon className="h-3.5 w-3.5" /> {eyebrow}</div><h1 className="text-2xl font-bold tracking-tight text-[#0F172A] dark:text-white sm:text-3xl">{title}</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">{description}</p></div><div className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-700 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-200"><ShieldCheck className="h-4 w-4 text-[#0D9488]" /> عرض إداري محكوم</div></header>;
}

function SearchField({ value, onChange, placeholder }: { value: string; onChange: (value: string) => void; placeholder: string }) {
  return <div className="relative w-full sm:max-w-xs"><Search className="pointer-events-none absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" /><Input placeholder={placeholder} value={value} onChange={(event) => onChange(event.target.value)} className="h-11 rounded-xl ps-9" /></div>;
}

export function AdminLabsPage() {
  const [search, setSearch] = useState("");
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["admin-labs", search], queryFn: () => adminApi.labs({ limit: 50 }) });
  const columns: ColumnDef<Lab>[] = [
    { accessorKey: "name", header: "اسم المختبر" },
    { accessorKey: "city", header: "المدينة" },
    { accessorKey: "phone", header: "الهاتف" },
    { accessorKey: "license_number", header: "رقم الترخيص" },
    { accessorKey: "director_name", header: "المدير" },
    { accessorKey: "is_active", header: "الحالة", cell: ({ row }) => <Badge variant={row.original.is_active ? "success" : "secondary"}>{row.original.is_active ? "نشط" : "غير نشط"}</Badge> },
  ];
  const labs = useMemo(() => (data?.labs ?? []).filter((lab) => `${lab.name} ${lab.city ?? ""} ${lab.license_number ?? ""}`.toLowerCase().includes(search.toLowerCase())), [data?.labs, search]);
  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;
  return <div className="mx-auto max-w-7xl space-y-6"><AdminHeader icon={Building2} eyebrow="إدارة المنشآت" title="إدارة المختبرات" description="مراقبة المختبرات المسجلة ضمن نطاق الإدارة والصلاحيات الحالية." /><Card className="overflow-hidden border-teal-100 dark:border-teal-900/40"><CardHeader className="gap-4 border-b border-teal-100/80 p-5 dark:border-teal-900/40 sm:flex-row sm:items-center sm:justify-between sm:p-6"><div><CardTitle className="flex items-center gap-2 text-base"><Building2 className="h-5 w-5 text-[#0D9488]" /> سجل المختبرات</CardTitle><p className="mt-1 text-xs font-normal text-muted-foreground">{labs.length} سجلًا ظاهرًا — القراءة فقط في هذا المسار.</p></div><SearchField value={search} onChange={setSearch} placeholder="بحث عن مختبر..." /></CardHeader><CardContent className="p-4 sm:p-6"><DataTable columns={columns} data={labs} loading={isLoading} /></CardContent></Card></div>;
}

export function AdminUsersPage() {
  const [search, setSearch] = useState("");
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["admin-users", search], queryFn: () => adminApi.users({ limit: 50 }) });
  const columns: ColumnDef<User>[] = [
    { accessorKey: "name", header: "الاسم" },
    { accessorKey: "email", header: "البريد الإلكتروني" },
    { accessorKey: "role", header: "الدور" },
    { accessorKey: "lab_name", header: "المختبر" },
    { accessorKey: "is_active", header: "الحالة", cell: ({ row }) => <Badge variant={row.original.is_active ? "success" : "secondary"}>{row.original.is_active ? "نشط" : "غير نشط"}</Badge> },
  ];
  const users = useMemo(() => (data?.users ?? []).filter((user) => `${user.name} ${user.email} ${user.role} ${user.lab_name ?? ""}`.toLowerCase().includes(search.toLowerCase())), [data?.users, search]);
  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;
  return <div className="mx-auto max-w-7xl space-y-6"><AdminHeader icon={Users} eyebrow="حوكمة الوصول" title="إدارة المستخدمين" description="عرض المستخدمين والأدوار ونطاق المنشأة دون تعديل مباشر للصلاحيات من الواجهة." /><Card className="overflow-hidden border-sky-100 dark:border-sky-900/40"><CardHeader className="gap-4 border-b border-sky-100/80 p-5 dark:border-sky-900/40 sm:flex-row sm:items-center sm:justify-between sm:p-6"><div><CardTitle className="flex items-center gap-2 text-base"><UserRound className="h-5 w-5 text-sky-600" /> دليل المستخدمين</CardTitle><p className="mt-1 text-xs font-normal text-muted-foreground">{users.length} مستخدمًا ظاهرًا — تعيين الدور يمر عبر IAM ومسار تدقيق معتمد.</p></div><SearchField value={search} onChange={setSearch} placeholder="بحث عن مستخدم..." /></CardHeader><CardContent className="p-4 sm:p-6"><DataTable columns={columns} data={users} loading={isLoading} /></CardContent></Card></div>;
}

export function AdminAuditPage() {
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["admin-audit"], queryFn: () => adminApi.auditLogs({ limit: 50 }) });
  const columns: ColumnDef<AuditLog>[] = [
    { accessorKey: "action", header: "الإجراء" },
    { accessorKey: "resource_type", header: "نوع المورد" },
    { accessorKey: "resource_id", header: "رقم المورد" },
    { accessorKey: "user_role", header: "دور المنفذ" },
    { accessorKey: "created_at", header: "التاريخ" },
  ];
  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;
  const logs = data?.logs ?? [];
  return <div className="mx-auto max-w-7xl space-y-6"><AdminHeader icon={FileSearch} eyebrow="دليل الامتثال" title="سجل التدقيق" description="سجل غير قابل للتغيير للعمليات التي تظهر ضمن الصلاحيات الحالية وسياق المنشأة." /><Card className="overflow-hidden border-violet-100 dark:border-violet-900/40"><CardHeader className="border-b border-violet-100/80 p-5 dark:border-violet-900/40 sm:p-6"><CardTitle className="flex items-center gap-2 text-base"><ClipboardList className="h-5 w-5 text-violet-600" /> السجل غير القابل للتعديل</CardTitle><p className="mt-1 text-xs font-normal text-muted-foreground">{logs.length} حدثًا ظاهرًا — لا يمكن حذف السجل أو تعديله من الواجهة.</p></CardHeader><CardContent className="p-4 sm:p-6"><DataTable columns={columns} data={logs} loading={isLoading} /></CardContent></Card></div>;
}
