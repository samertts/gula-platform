import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { DataTable } from "@/components/ui/DataTable";
import { Badge, Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { EmptyState, ErrorDisplay, PageLoadingSkeleton } from "@/components/shared/PageComponents";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import {
  Activity,
  ArrowLeft,
  Bell,
  BookOpen,
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  FileHeart,
  FileText,
  FolderOpen,
  HeartPulse,
  LockKeyhole,
  Pill,
  ShieldCheck,
  UserRound,
} from "lucide-react";

const tabs = [
  { id: "profile", label: "الملف الشخصي", icon: UserRound, description: "بيانات حسابك وهويتك" },
  { id: "health-summary", label: "ملخصي الصحي", icon: HeartPulse, description: "صورة موجزة عن سجلك" },
  { id: "appointments", label: "مواعيدي", icon: CalendarDays, description: "المواعيد والحالات" },
  { id: "medications", label: "أدويتي", icon: Pill, description: "الأدوية المسجلة" },
  { id: "medication-dispenses", label: "العلاجات المصروفة", icon: ClipboardList, description: "سجل الصرف" },
  { id: "lab-results", label: "نتائج المختبر", icon: FolderOpen, description: "النتائج والتقارير" },
] as const;

type TabId = (typeof tabs)[number]["id"];
type Row = Record<string, unknown>;
type QueryResult = { data?: unknown; isLoading: boolean; isError: boolean; refetch: () => unknown };

const column = createColumnHelper<Row>();

function formatDate(value: unknown): string {
  if (!value) return "—";
  const date = new Date(String(value));
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleDateString("ar-IQ");
}

function toRows(value: unknown, preferredKeys: string[] = []): Row[] {
  if (Array.isArray(value)) return value.filter((item): item is Row => Boolean(item) && typeof item === "object");
  if (!value || typeof value !== "object") return [];
  const record = value as Record<string, unknown>;
  for (const key of [...preferredKeys, "items", "data", "records", "results"]) {
    if (Array.isArray(record[key])) return toRows(record[key]);
  }
  return [record];
}

function readNumber(value: unknown, keys: string[], fallback: number | null = null): number | null {
  if (!value || typeof value !== "object") return fallback;
  const record = value as Record<string, unknown>;
  for (const key of keys) {
    const candidate = record[key];
    if (typeof candidate === "number" && Number.isFinite(candidate)) return candidate;
    if (typeof candidate === "string" && candidate.trim() && Number.isFinite(Number(candidate))) return Number(candidate);
  }
  return fallback;
}

function readString(row: Row, keys: string[]): string {
  for (const key of keys) {
    const value = row[key];
    if (typeof value === "string" && value.trim()) return value;
    if (typeof value === "number") return String(value);
  }
  return "—";
}

function statusVariant(value: unknown): "success" | "warning" | "destructive" | "default" {
  const normalized = String(value ?? "").toLowerCase();
  if (["active", "completed", "approved", "confirmed", "ready", "released"].includes(normalized)) return "success";
  if (["pending", "scheduled", "draft", "processing", "in_progress"].includes(normalized)) return "warning";
  if (["rejected", "cancelled", "canceled", "expired", "failed"].includes(normalized)) return "destructive";
  return "default";
}

function makeColumns(tab: TabId): ColumnDef<Row, unknown>[] {
  if (tab === "medication-dispenses") {
    return [
      column.accessor((row) => readString(row, ["medication_name_ar", "medication_name", "name"]), { id: "medication", header: "العلاج" }),
      column.accessor((row) => readString(row, ["quantity"]), { id: "quantity", header: "الكمية" }),
      column.accessor((row) => readString(row, ["quantity_unit", "unit"]), { id: "unit", header: "الوحدة" }),
      column.accessor((row) => readString(row, ["lot_number", "batch"]), { id: "batch", header: "الدفعة" }),
      column.accessor((row) => formatDate(row.expiry_date), { id: "expiry", header: "الصلاحية" }),
      column.accessor((row) => String(row.status ?? "—"), { id: "status", header: "الحالة", cell: ({ getValue }) => <Badge variant={statusVariant(getValue())}>{String(getValue())}</Badge> }),
      column.accessor((row) => formatDate(row.dispensed_at), { id: "dispensedAt", header: "تاريخ الصرف" }),
    ] as unknown as ColumnDef<Row, unknown>[];
  }

  return [
    column.accessor((row) => readString(row, ["id", "uuid", "result_id", "appointment_id"]), { id: "id", header: "المعرف" }),
    column.accessor((row) => readString(row, ["name", "title", "test_name", "doctor_name", "service_name"]), { id: "name", header: "التفاصيل" }),
    column.accessor((row) => String(row.status ?? row.state ?? "—"), { id: "status", header: "الحالة", cell: ({ getValue }) => <Badge variant={statusVariant(getValue())}>{String(getValue())}</Badge> }),
    column.accessor((row) => formatDate(row.created_at ?? row.updated_at ?? row.appointment_at ?? row.measured_at), { id: "date", header: "التاريخ" }),
  ] as unknown as ColumnDef<Row, unknown>[];
}

function MetricCard({ label, value, icon: Icon, tone }: { label: string; value: number | null; icon: typeof Activity; tone: string }) {
  return (
    <Card className="overflow-hidden border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70">
      <CardContent className="relative p-5">
        <div className={`absolute inset-x-0 top-0 h-1 ${tone}`} />
        <div className="flex items-center justify-between gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200">
            <Icon className="h-5 w-5" aria-hidden="true" />
          </span>
          <span className="text-[10px] font-bold text-muted-foreground">قراءة آمنة</span>
        </div>
        <p className="mt-4 text-sm text-muted-foreground">{label}</p>
        <p className="mt-1 text-3xl font-bold tracking-tight text-slate-950 dark:text-white">{value ?? "—"}</p>
      </CardContent>
    </Card>
  );
}

export default function CitizenWorkspacePage() {
  const { demoMode, user } = useAuth();
  const [activeTab, setActiveTab] = useState<TabId>("profile");
  const dashboard = useQuery({ queryKey: ["citizenWorkspace", "dashboard"], queryFn: () => api.get("/citizen-platform/me/dashboard").then((response) => response.data) });
  const profile = useQuery({ queryKey: ["citizenWorkspace", "profile"], queryFn: () => api.get("/citizen-platform/me/profile").then((response) => response.data) });
  const healthSummary = useQuery({ queryKey: ["citizenWorkspace", "health-summary"], queryFn: () => api.get("/citizen-platform/me/health-summary").then((response) => response.data) });
  const appointments = useQuery({ queryKey: ["citizenWorkspace", "appointments"], queryFn: () => api.get("/citizen-platform/me/appointments").then((response) => response.data) });
  const medications = useQuery({ queryKey: ["citizenWorkspace", "medications"], queryFn: () => api.get("/citizen-platform/me/medications").then((response) => response.data) });
  const medicationDispenses = useQuery({ queryKey: ["citizenWorkspace", "medication-dispenses"], queryFn: () => api.get("/citizen-platform/me/medication-dispenses").then((response) => response.data) });
  const labResults = useQuery({ queryKey: ["citizenWorkspace", "lab-results"], queryFn: () => api.get("/citizen-platform/me/lab-results").then((response) => response.data) });

  const queries: Record<TabId, QueryResult> = {
    profile,
    "health-summary": healthSummary,
    appointments,
    medications,
    "medication-dispenses": medicationDispenses,
    "lab-results": labResults,
  };

  const dataRows = useMemo<Record<TabId, Row[]>>(() => ({
    profile: toRows(profile.data),
    "health-summary": toRows(healthSummary.data),
    appointments: toRows(appointments.data, ["appointments"]),
    medications: toRows(medications.data, ["medications"]),
    "medication-dispenses": toRows(medicationDispenses.data, ["dispenses"]),
    "lab-results": toRows(labResults.data, ["results", "lab_results"]),
  }), [profile.data, healthSummary.data, appointments.data, medications.data, medicationDispenses.data, labResults.data]);

  const dashboardRows = toRows(dashboard.data);
  const dashboardRecord = dashboard.data && typeof dashboard.data === "object" && !Array.isArray(dashboard.data) ? dashboard.data : undefined;
  const metrics = [
    { label: "المواعيد القادمة", value: readNumber(dashboardRecord, ["upcoming_appointments", "appointments_count", "appointments"], dataRows.appointments.length || null), icon: CalendarDays, tone: "bg-gradient-to-l from-teal-500 to-cyan-400" },
    { label: "نتائج المختبر", value: readNumber(dashboardRecord, ["lab_results_count", "results_count", "lab_results"], dataRows["lab-results"].length || null), icon: FileHeart, tone: "bg-gradient-to-l from-indigo-500 to-sky-400" },
    { label: "الأدوية المسجلة", value: readNumber(dashboardRecord, ["medications_count", "medications"], dataRows.medications.length || null), icon: Pill, tone: "bg-gradient-to-l from-amber-500 to-orange-400" },
  ];
  const query = queries[activeTab];
  const activeRows = dataRows[activeTab];
  const activeTabMeta = tabs.find((tab) => tab.id === activeTab) ?? tabs[0];

  if (dashboard.isLoading && !dashboard.data) return <PageLoadingSkeleton />;

  return (
    <div className="mx-auto max-w-7xl space-y-6 pb-4">
      <section className="relative overflow-hidden rounded-[1.75rem] border border-slate-200/80 bg-[#0F172A] p-5 text-white shadow-[0_24px_70px_-35px_rgba(15,23,42,0.75)] dark:border-white/10 sm:p-7">
        <div className="absolute -left-16 -top-24 h-64 w-64 rounded-full bg-teal-400/20 blur-3xl" />
        <div className="absolute -bottom-36 right-8 h-72 w-72 rounded-full bg-sky-500/20 blur-3xl" />
        <div className="relative grid gap-6 lg:grid-cols-[1fr_auto] lg:items-end">
          <div className="max-w-3xl">
            <div className="mb-4 flex flex-wrap items-center gap-2 text-xs font-semibold">
              <span className="inline-flex items-center gap-2 rounded-full border border-teal-200/20 bg-teal-200/10 px-3 py-1.5 text-teal-100">
                <span className="h-2 w-2 rounded-full bg-teal-300 shadow-[0_0_0_4px_rgba(45,212,191,0.12)]" /> مساحة المواطن
              </span>
              {demoMode && <span className="inline-flex items-center gap-2 rounded-full border border-amber-300/20 bg-amber-300/10 px-3 py-1.5 text-amber-100"><ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" /> عرض تجريبي معزول</span>}
            </div>
            <p className="text-sm text-teal-200">مرحباً{user?.name ? `، ${user.name}` : ""}</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">كل ما يخص رحلتك الصحية في مكان واحد</h1>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-300">استعرض ملفك ونتائجك ومواعيدك وأدويتك من خلال مساحة واحدة، مع إبقاء كل قراءة مرتبطة بحسابك ونطاقك المصرح به.</p>
            {demoMode && <div className="mt-5 inline-flex max-w-2xl items-center gap-2 rounded-2xl border border-amber-200/20 bg-amber-200/10 px-3.5 py-2.5 text-xs text-amber-100"><LockKeyhole className="h-3.5 w-3.5" aria-hidden="true" /><strong>بيانات اصطناعية فقط</strong><span className="text-amber-100/70">لا تمثل مرضى حقيقيين ولا تُنشئ أثراً تشغيلياً.</span></div>}
          </div>
          <Link to="/notifications" className="group inline-flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.07] p-4 text-sm text-slate-200 backdrop-blur-sm transition hover:bg-white/[0.12] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-300">
            <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-400/15 text-teal-200"><Bell className="h-6 w-6" aria-hidden="true" /></span>
            <span><span className="block font-bold">مركز الإشعارات</span><span className="mt-1 block text-xs text-slate-400">التنبيهات المعتمدة فقط</span></span>
            <ArrowLeft className="h-4 w-4 text-slate-400 transition group-hover:-translate-x-1" aria-hidden="true" />
          </Link>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-3" aria-label="ملخص المساحة الصحية">
        {metrics.map((metric) => <MetricCard key={metric.label} {...metric} />)}
      </section>

      <section className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
        <Card className="border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70">
          <CardHeader><CardTitle className="flex items-center gap-2 text-base"><Activity className="h-5 w-5 text-teal-600" aria-hidden="true" /> اختصارات مفيدة</CardTitle><p className="mt-1 text-xs text-muted-foreground">تجربة موحدة مستوحاة من تطبيقات المرضى، دون تجاوز عقد GULA.</p></CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            {[
              { label: "استعرض المواعيد", description: "تابع الحالة والتاريخ", tab: "appointments" as TabId, icon: CalendarDays, tone: "bg-teal-50 text-teal-700 dark:bg-teal-950/40 dark:text-teal-200" },
              { label: "شاهد النتائج", description: "قراءة السجل المصرح به", tab: "lab-results" as TabId, icon: FolderOpen, tone: "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-200" },
              { label: "راجع أدويتك", description: "القائمة وسجل الصرف", tab: "medications" as TabId, icon: Pill, tone: "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-200" },
            ].map(({ label, description, tab, icon: Icon, tone }) => (
              <button key={tab} type="button" onClick={() => setActiveTab(tab)} className="group flex items-center gap-3 rounded-2xl border border-slate-200/80 p-3.5 text-right transition hover:-translate-y-0.5 hover:border-teal-300 hover:bg-teal-50/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 dark:border-white/10 dark:hover:border-teal-800 dark:hover:bg-teal-950/20">
                <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${tone}`}><Icon className="h-[18px] w-[18px]" aria-hidden="true" /></span>
                <span className="min-w-0 flex-1"><span className="block text-sm font-bold">{label}</span><span className="mt-1 block text-xs text-muted-foreground">{description}</span></span>
                <ArrowLeft className="h-4 w-4 text-muted-foreground transition group-hover:-translate-x-1 group-hover:text-teal-600" aria-hidden="true" />
              </button>
            ))}
          </CardContent>
        </Card>

        <Card className="border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70">
          <CardHeader className="flex flex-row items-center justify-between space-y-0"><div><CardTitle className="flex items-center gap-2 text-base"><ShieldCheck className="h-5 w-5 text-emerald-600" aria-hidden="true" /> حماية المساحة</CardTitle><p className="mt-1 text-xs text-muted-foreground">كل شاشة تستعمل عقد القراءة المصرح بها فقط.</p></div><span className="rounded-full bg-emerald-50 px-2.5 py-1 text-[10px] font-bold text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-200">قراءة فقط</span></CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center gap-3 rounded-2xl bg-emerald-50 p-4 dark:bg-emerald-950/25"><CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-600" aria-hidden="true" /><div><p className="text-sm font-bold text-emerald-900 dark:text-emerald-200">هوية ونطاق محميان</p><p className="mt-1 text-xs text-emerald-800/70 dark:text-emerald-200/70">لا تُعرض بيانات مواطن آخر أو مؤسسة أخرى.</p></div></div>
            <div className="flex items-center gap-3 rounded-2xl bg-slate-50 p-4 dark:bg-white/[0.04]"><FileText className="h-5 w-5 shrink-0 text-slate-500" aria-hidden="true" /><div><p className="text-sm font-bold">القرارات السريرية خارج هذه المساحة</p><p className="mt-1 text-xs text-muted-foreground">المحتوى إرشادي ولا يمثل تشخيصاً أو وصفة علاجية.</p></div></div>
          </CardContent>
        </Card>
      </section>

      <Card className="border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70">
        <CardHeader className="pb-3"><div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between"><div><CardTitle className="flex items-center gap-2 text-base"><BookOpen className="h-5 w-5 text-indigo-600" aria-hidden="true" /> مساحتك الصحية</CardTitle><p className="mt-1 text-xs text-muted-foreground">{activeTabMeta.description} · لا يتم تنفيذ أي تعديل من هذه الشاشة.</p></div><span className="inline-flex w-fit items-center gap-2 rounded-full bg-slate-100 px-3 py-1.5 text-[10px] font-bold text-slate-600 dark:bg-white/10 dark:text-slate-300"><LockKeyhole className="h-3.5 w-3.5" aria-hidden="true" /> وصول شخصي</span></div></CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto border-y border-slate-200/80 dark:border-white/10" role="tablist" aria-label="أقسام مساحة المواطن">
            <div className="flex min-w-max gap-1 p-2">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const selected = activeTab === tab.id;
                return <button key={tab.id} type="button" role="tab" aria-selected={selected} aria-controls={`citizen-panel-${tab.id}`} onClick={() => setActiveTab(tab.id)} className={`inline-flex items-center gap-2 rounded-xl px-3.5 py-2.5 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 ${selected ? "bg-teal-50 text-teal-700 ring-1 ring-teal-100 dark:bg-teal-950/40 dark:text-teal-200 dark:ring-teal-900/60" : "text-muted-foreground hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-white/10 dark:hover:text-white"}`}><Icon className="h-4 w-4" aria-hidden="true" />{tab.label}</button>;
              })}
            </div>
          </div>
          <div id={`citizen-panel-${activeTab}`} role="tabpanel" aria-label={activeTabMeta.label} className="p-4 sm:p-5">
            {query.isLoading ? <div className="py-12"><PageLoadingSkeleton /></div> : query.isError ? <ErrorDisplay error="تعذر تحميل هذا القسم من عقد GULA المصرح به." onRetry={() => { void query.refetch(); }} /> : activeRows.length === 0 ? <EmptyState icon={activeTabMeta.icon} title="لا توجد بيانات معروضة" description={demoMode ? "هذا القسم جاهز للعرض، لكن لا توجد سجلات اصطناعية لهذا الحساب حالياً." : "لا توجد سجلات متاحة ضمن نطاق حسابك المصرح به."} /> : <DataTable columns={makeColumns(activeTab)} data={activeRows} loading={false} />}
          </div>
        </CardContent>
      </Card>

      {dashboardRows.length > 0 && <p className="sr-only">تم تحميل ملخص المواطن بنجاح.</p>}
    </div>
  );
}
