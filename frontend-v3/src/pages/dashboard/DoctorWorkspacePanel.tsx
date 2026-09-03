import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  Activity,
  ArrowUpLeft,
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  FileCheck2,
  FlaskConical,
  HeartPulse,
  LockKeyhole,
  RefreshCw,
  ShieldCheck,
  Stethoscope,
  Users,
  Workflow,
  type LucideIcon,
} from "lucide-react";
import { apiClient, type WorkspaceSummary } from "@/api/client";
import {
  WorkspaceReadBlockedError,
  type ClinicalOrderRead,
  type ClinicalPatientRead,
  workspaceScopedReads,
} from "@/api/workspaceScopedReads";
import { useAuth } from "@/contexts/AuthContext";
import { ClinicalStatePanel } from "@/components/clinical";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

const DEMO_WORKSPACE: WorkspaceSummary = {
  id: "demo-physician-workspace",
  uuid: "demo-physician-workspace-uuid",
  workspace_type: "professional",
  name: "GULA Synthetic Clinic",
  name_ar: "عيادة GULA الاصطناعية",
  status: "active",
  organization_id: "demo-organization",
  facility_id: "demo-facility",
  department_id: "demo-family-medicine",
  professional_type: "physician",
  is_personal: false,
};

const DEMO_PATIENTS: ClinicalPatientRead[] = [
  { id: "demo-patient-101", display_name: "سارة عبد الرحمن · تجريبي", birth_date: "1992-04-16", gender: "أنثى", created_at: "2026-08-12T09:30:00Z" },
  { id: "demo-patient-102", display_name: "علي كريم حسن · تجريبي", birth_date: "1987-11-03", gender: "ذكر", created_at: "2026-08-13T10:15:00Z" },
  { id: "demo-patient-104", display_name: "حسن نوري · تجريبي", birth_date: "1974-02-09", gender: "ذكر", created_at: "2026-08-10T11:00:00Z" },
];

const DEMO_ORDERS: ClinicalOrderRead[] = [
  { id: "demo-order-401", patient_display_name: "سارة عبد الرحمن · تجريبي", practitioner_display_name: "طبيب GULA التجريبي", status: "قيد المراجعة", test_count: 3, created_at: "2026-08-27T08:30:00Z" },
  { id: "demo-order-402", patient_display_name: "علي كريم حسن · تجريبي", practitioner_display_name: "طبيب GULA التجريبي", status: "مُرسل للمختبر", test_count: 2, created_at: "2026-08-27T09:10:00Z" },
  { id: "demo-order-403", patient_display_name: "حسن نوري · تجريبي", practitioner_display_name: "طبيب GULA التجريبي", status: "نتيجة جاهزة", test_count: 4, created_at: "2026-08-27T10:05:00Z" },
];

const DEMO_SCHEDULE = [
  { time: "09:30", patient: "سارة عبد الرحمن · تجريبي", type: "متابعة طب الأسرة", state: "مؤكد" },
  { time: "10:15", patient: "علي كريم حسن · تجريبي", type: "استشارة عامة", state: "بانتظار التأكيد" },
  { time: "11:00", patient: "حسن نوري · تجريبي", type: "متابعة قلبية", state: "مؤكد" },
];

const DEMO_TASKS = [
  { title: "مراجعة نتيجة اصطناعية", detail: "نتيجة ضمن مسار القراءة فقط", tone: "text-indigo-600" },
  { title: "استكمال ملاحظة زيارة", detail: "مسودة تدريبية غير قابلة للإرسال", tone: "text-amber-600" },
  { title: "متابعة إحالة تجريبية", detail: "لا يتم إنشاء إحالة فعلية", tone: "text-teal-600" },
];

const QUICK_LINKS = [
  { label: "دليل المرضى", detail: "ملخصات ضمن النطاق المصرح", path: "/patient-management", icon: Users },
  { label: "الطلبات", detail: "طلب المختبر دون إدخال نتيجة", path: "/orders", icon: ClipboardList },
  { label: "النتائج", detail: "عرض مقيد حسب العقد", path: "/results", icon: FlaskConical },
  { label: "جاهزية الزيارة", detail: "نموذج Encounter غير تشغيلي", path: "/patient-visit/readiness", icon: CalendarDays },
] as const;

type Metric = { label: string; value: string; detail: string; icon: LucideIcon; tone: string };

type WorkflowItem = {
  label: string;
  detail: string;
  status: "متاح للقراءة" | "تجريبي فقط" | "يتطلب عقداً خادمياً";
  icon: LucideIcon;
};

function isActive(workspace: WorkspaceSummary) {
  return workspace.status.toLowerCase() === "active";
}

function errorMessage(error: unknown) {
  if (error instanceof WorkspaceReadBlockedError) return error.message;
  return "تعذر تحميل القراءة ضمن السياق الحالي. لم يتم استخدام مسار بديل أو بيانات مخزنة غير موثقة.";
}

function formatDate(value?: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("ar-IQ", { dateStyle: "medium" }).format(date);
}

function StatusBadge({ status }: { status: WorkflowItem["status"] }) {
  const variant = status === "متاح للقراءة" ? "success" : status === "تجريبي فقط" ? "warning" : "outline";
  return <Badge variant={variant}>{status}</Badge>;
}

export function DoctorWorkspacePanel() {
  const { demoMode, user } = useAuth();
  const queryClient = useQueryClient();
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string | null>(null);
  const [switchingWorkspaceId, setSwitchingWorkspaceId] = useState<string | null>(null);
  const [switchError, setSwitchError] = useState<string | null>(null);

  const workspacesQuery = useQuery({
    queryKey: ["doctor-workspaces", "me"],
    queryFn: () => apiClient.listWorkspaces(),
    enabled: !demoMode,
    retry: false,
    staleTime: 30_000,
  });

  const professionalWorkspaces = useMemo(
    () => (workspacesQuery.data?.workspaces ?? []).filter((workspace) => workspace.workspace_type === "professional" && workspace.professional_type?.toLowerCase() === "physician"),
    [workspacesQuery.data?.workspaces],
  );

  const selectedLiveWorkspace = professionalWorkspaces.find((workspace) => workspace.id === selectedWorkspaceId);
  const currentWorkspace = demoMode ? DEMO_WORKSPACE : selectedLiveWorkspace;

  const patientsQuery = useQuery({
    queryKey: ["doctor-clinical-patients", selectedLiveWorkspace?.id ?? "none"],
    queryFn: () => workspaceScopedReads.listPatients({ limit: 10 }),
    enabled: !demoMode && Boolean(selectedLiveWorkspace),
    retry: false,
  });

  const ordersQuery = useQuery({
    queryKey: ["doctor-clinical-orders", selectedLiveWorkspace?.id ?? "none"],
    queryFn: () => workspaceScopedReads.listOrders({ limit: 10 }),
    enabled: !demoMode && Boolean(selectedLiveWorkspace),
    retry: false,
  });

  const patients = demoMode ? DEMO_PATIENTS : patientsQuery.data ?? [];
  const orders = demoMode ? DEMO_ORDERS : ordersQuery.data ?? [];
  const isLiveReadReady = demoMode || Boolean(selectedLiveWorkspace);
  const liveReadBlocked = !demoMode && (patientsQuery.error || ordersQuery.error);

  const metrics: Metric[] = demoMode
    ? [
        { label: "مرضى تحت المتابعة", value: "24", detail: "بيانات اصطناعية", icon: Users, tone: "teal" },
        { label: "مواعيد اليوم", value: "11", detail: "تدفق تجريبي", icon: CalendarDays, tone: "sky" },
        { label: "طلبات قيد المتابعة", value: "5", detail: "قراءة فقط", icon: ClipboardList, tone: "indigo" },
        { label: "تنبيهات حرجة", value: "2", detail: "غير تشغيلية", icon: ShieldCheck, tone: "rose" },
      ]
    : [
        { label: "مرضى مصرح بهم", value: patientsQuery.isLoading ? "…" : String(patients.length), detail: "من clinical gateway", icon: Users, tone: "teal" },
        { label: "طلبات مصرح بها", value: ordersQuery.isLoading ? "…" : String(orders.length), detail: "من clinical gateway", icon: ClipboardList, tone: "sky" },
        { label: "المواعيد", value: "—", detail: "العقد غير مفعّل", icon: CalendarDays, tone: "indigo" },
        { label: "التنبيهات الحرجة", value: "—", detail: "العقد غير مفعّل", icon: ShieldCheck, tone: "rose" },
      ];

  const workflow: WorkflowItem[] = [
    { label: "المرضى", detail: "قائمة مختصرة داخل نطاق المؤسسة", status: demoMode ? "تجريبي فقط" : "متاح للقراءة", icon: Users },
    { label: "الموعد → الزيارة", detail: "يفصل النظام بين Appointment وEncounter", status: "يتطلب عقداً خادمياً", icon: CalendarDays },
    { label: "الطلبات", detail: "طلب المختبر ظاهر دون إدخال نتيجة", status: demoMode ? "تجريبي فقط" : "متاح للقراءة", icon: FlaskConical },
    { label: "النتائج والوصفات", detail: "لا توقيع أو اعتماد سريري من هذه الشاشة", status: "يتطلب عقداً خادمياً", icon: FileCheck2 },
    { label: "الإحالات والمتابعة", detail: "تحتاج workflow وTask موثقين", status: "يتطلب عقداً خادمياً", icon: Workflow },
    { label: "علي رضا", detail: "مساعد مرشد داخل السياق وليس صاحب قرار", status: "تجريبي فقط", icon: Stethoscope },
  ];

  async function switchWorkspace(workspace: WorkspaceSummary) {
    if (!isActive(workspace)) return;
    setSwitchingWorkspaceId(workspace.id);
    setSwitchError(null);
    try {
      const result = await apiClient.switchWorkspace(workspace.id);
      setSelectedWorkspaceId(result.workspace.id);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["doctor-clinical-patients"] }),
        queryClient.invalidateQueries({ queryKey: ["doctor-clinical-orders"] }),
      ]);
    } catch {
      setSwitchError("رفض الخادم تبديل مساحة العمل أو تعذر إثبات سياق المؤسسة. لم تُمنح أي صلاحية محلية.");
    } finally {
      setSwitchingWorkspaceId(null);
    }
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 pb-2" dir="rtl">
      <section className="relative overflow-hidden rounded-[1.75rem] border border-slate-200/80 bg-[#0F172A] p-5 text-white shadow-[0_24px_70px_-35px_rgba(15,23,42,0.75)] dark:border-white/10 sm:p-7">
        <div className="absolute -left-12 -top-24 h-64 w-64 rounded-full bg-[#0D9488]/25 blur-3xl" />
        <div className="absolute -bottom-32 right-8 h-72 w-72 rounded-full bg-sky-500/20 blur-3xl" />
        <div className="relative grid gap-7 lg:grid-cols-[1fr_auto] lg:items-end">
          <div className="max-w-3xl">
            <div className="mb-4 flex flex-wrap items-center gap-2 text-xs font-semibold">
              <span className="inline-flex items-center gap-2 rounded-full border border-teal-200/20 bg-teal-200/10 px-3 py-1.5 text-teal-100"><span className="h-2 w-2 rounded-full bg-teal-300 shadow-[0_0_0_4px_rgba(45,212,191,0.12)]" />مساحة الطبيب</span>
              {demoMode && <span className="inline-flex items-center gap-2 rounded-full border border-amber-300/20 bg-amber-300/10 px-3 py-1.5 text-amber-100"><ShieldCheck className="h-3.5 w-3.5" />عرض اصطناعي معزول</span>}
            </div>
            <p className="text-sm text-teal-200">مرحباً{user?.name ? `، ${user.name}` : " بالطبيب"}</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">مركز العمل السريري للطبيب</h1>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-300">هوية واحدة، ومساحة عمل مرتبطة بالمؤسسة، وقراءة سريرية لا تُفتح إلا بعد إثبات العضوية والسياق والتفويض من الخادم.</p>
            {demoMode && <div className="mt-5 inline-flex max-w-2xl flex-wrap items-center gap-2 rounded-2xl border border-amber-200/20 bg-amber-200/10 px-3.5 py-2.5 text-xs text-amber-100"><LockKeyhole className="h-3.5 w-3.5" /><strong>لا توجد بيانات حقيقية</strong><span className="text-amber-100/70">— كل المرضى والمواعيد والطلبات مولدة للتدريب والشرح.</span></div>}
          </div>
          <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.07] p-4 text-sm text-slate-200 backdrop-blur-sm"><span className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-400/15 text-teal-200"><HeartPulse className="h-6 w-6" /></span><div><p className="font-bold">{currentWorkspace?.name_ar ?? "لم تُحدد مساحة عمل"}</p><p className="mt-1 text-xs text-slate-400">{currentWorkspace ? "سياق مؤسسي محدد" : "اختر مساحة مهنية للمتابعة"}</p></div></div>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="مؤشرات مساحة الطبيب">
        {metrics.map(({ label, value, detail, icon: Icon, tone }) => (
          <Card key={label} className="overflow-hidden rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70">
            <CardContent className="relative p-5"><div className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-l ${tone === "rose" ? "from-rose-500 to-orange-400" : tone === "indigo" ? "from-indigo-500 to-sky-400" : tone === "sky" ? "from-sky-500 to-cyan-400" : "from-teal-500 to-emerald-400"}`} /><div className="flex items-start justify-between gap-3"><span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200"><Icon className="h-5 w-5" /></span><span className="rounded-full bg-slate-100 px-2.5 py-1 text-[10px] font-bold text-slate-500 dark:bg-white/10 dark:text-slate-300">{demoMode ? "تجريبي" : "خادمي"}</span></div><p className="mt-5 text-sm text-muted-foreground">{label}</p><p className="mt-1 text-3xl font-bold tracking-tight text-[#0F172A] dark:text-white">{value}</p><p className="mt-2 text-[11px] text-muted-foreground">{detail}</p></CardContent>
          </Card>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70">
          <CardHeader className="flex flex-row items-center justify-between space-y-0"><div><CardTitle className="flex items-center gap-2 text-base"><Stethoscope className="h-5 w-5 text-[#0D9488]" />سياق العمل والعضويات</CardTitle><p className="mt-1 text-xs text-muted-foreground">لا يمنح الاختيار دوراً جديداً؛ هو يطلب تفعيل سياق أعاده الخادم مسبقاً.</p></div><Badge variant={demoMode ? "warning" : "outline"}>{demoMode ? "عرض" : "قراءة الخادم"}</Badge></CardHeader>
          <CardContent className="space-y-3">
            {demoMode ? <WorkspaceCard workspace={DEMO_WORKSPACE} selected onSelect={() => undefined} switching={false} /> : workspacesQuery.isLoading ? <div className="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">جارٍ تحميل مساحات العمل المؤهلة…</div> : professionalWorkspaces.length === 0 ? <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-5 text-sm leading-7 text-amber-900 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200"><LockKeyhole className="ml-2 inline h-4 w-4" />لا توجد مساحة طبيب مؤهلة في استجابة الخادم. يلزم Professional Verification وMembership وFacility Context قبل ظهور المسار السريري.</div> : professionalWorkspaces.map((workspace) => <WorkspaceCard key={workspace.id} workspace={workspace} selected={workspace.id === selectedWorkspaceId} onSelect={() => void switchWorkspace(workspace)} switching={switchingWorkspaceId === workspace.id} />)}
            {switchError && <p className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/20 dark:text-rose-200" role="alert">{switchError}</p>}
            {!demoMode && workspacesQuery.error && <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200" role="alert">{errorMessage(workspacesQuery.error)}</p>}
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70">
          <CardHeader><CardTitle className="flex items-center gap-2 text-base"><ShieldCheck className="h-5 w-5 text-emerald-600" />سلسلة الثقة الحالية</CardTitle></CardHeader>
          <CardContent className="space-y-3"><TrustRow label="هوية الحساب" value="مرتبطة بالشخص" /><TrustRow label="التحقق المهني" value={demoMode ? "اصطناعي للعرض" : currentWorkspace ? "أعادها الخادم" : "غير مثبت"} /><TrustRow label="عضوية المؤسسة" value={demoMode ? "اصطناعية" : currentWorkspace ? "ضمن السياق" : "غير مثبتة"} /><TrustRow label="قراءة المرضى والطلبات" value={demoMode ? "معزولة" : selectedLiveWorkspace ? "بوابة مقيدة" : "معلقة"} /></CardContent>
        </Card>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70">
          <CardHeader className="flex flex-row items-center justify-between space-y-0"><div><CardTitle className="flex items-center gap-2 text-base"><CalendarDays className="h-5 w-5 text-sky-600" />جدول الطبيب</CardTitle><p className="mt-1 text-xs text-muted-foreground">Appointment منفصل عن Encounter ولا توجد كتابة تشغيلية من هذه اللوحة.</p></div><span className="rounded-full bg-slate-100 px-2.5 py-1 text-[10px] font-bold text-slate-600 dark:bg-white/10 dark:text-slate-300">{demoMode ? "تجريبي" : "محجوب بأمان"}</span></CardHeader>
          <CardContent>{demoMode ? <div className="space-y-2">{DEMO_SCHEDULE.map((item) => <div key={item.time} className="flex items-center justify-between gap-3 rounded-xl border border-slate-200/80 p-3 dark:border-white/10"><div className="flex items-center gap-3"><span className="flex h-9 w-16 items-center justify-center rounded-lg bg-sky-50 text-sm font-bold text-sky-700 dark:bg-sky-950/30 dark:text-sky-200">{item.time}</span><div><p className="text-sm font-semibold">{item.patient}</p><p className="mt-1 text-xs text-muted-foreground">{item.type}</p></div></div><Badge variant={item.state === "مؤكد" ? "success" : "warning"}>{item.state}</Badge></div>)}</div> : <GatedPanel title="عقد المواعيد غير مفعّل" description="لن تُعرض مواعيد أو مرضى حقيقيون حتى يتوفر endpoint ذاتي مقيد بالمؤسسة، والعضوية، والتدقيق، والترقيم الصفحي." />}</CardContent>
        </Card>

        <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70">
          <CardHeader className="flex flex-row items-center justify-between space-y-0"><div><CardTitle className="flex items-center gap-2 text-base"><ClipboardList className="h-5 w-5 text-indigo-600" />My Work</CardTitle><p className="mt-1 text-xs text-muted-foreground">المهام الحساسة لا تُغلق أو تُوقّع من الواجهة وحدها.</p></div><Badge variant="outline">قراءة فقط</Badge></CardHeader>
          <CardContent>{demoMode ? <div className="space-y-2">{DEMO_TASKS.map((task) => <div key={task.title} className="flex items-start gap-3 rounded-xl p-3 hover:bg-slate-50 dark:hover:bg-white/[0.04]"><span className="mt-0.5 flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 dark:bg-white/10"><Activity className={`h-4 w-4 ${task.tone}`} /></span><div><p className="text-sm font-semibold">{task.title}</p><p className="mt-1 text-xs text-muted-foreground">{task.detail}</p></div></div>)}</div> : <GatedPanel title="محرك المهام السريري غير موصول" description="يلزم عقد Task/Workflow خادمي يفرض purpose وversion وidempotency وaudit قبل عرض مهام حقيقية." />}</CardContent>
        </Card>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <ClinicalReadCard title="المرضى ضمن النطاق" icon={Users} loading={patientsQuery.isLoading} error={patientsQuery.error} empty={!isLiveReadReady} items={patients.map((patient) => <div key={patient.id} className="rounded-xl border border-slate-200/80 p-3 dark:border-white/10"><div className="flex items-start justify-between gap-3"><div><p className="text-sm font-semibold">{patient.display_name}</p><p className="mt-1 text-xs text-muted-foreground">{patient.gender ?? "بيانات ديموغرافية محدودة"} · تاريخ الإنشاء {formatDate(patient.created_at)}</p></div><Badge variant="outline">ملخص محدود</Badge></div></div>)} emptyMessage={demoMode ? "لا توجد بيانات اصطناعية" : "اختر مساحة طبيب من الخادم أولاً."} />
        <ClinicalReadCard title="طلبات الطبيب" icon={FlaskConical} loading={ordersQuery.isLoading} error={ordersQuery.error} empty={!isLiveReadReady} items={orders.map((order) => <div key={order.id} className="rounded-xl border border-slate-200/80 p-3 dark:border-white/10"><div className="flex items-start justify-between gap-3"><div><p className="text-sm font-semibold">{order.patient_display_name ?? "مريض ضمن النطاق"}</p><p className="mt-1 text-xs text-muted-foreground">{order.status} · {order.test_count} فحوصات · {formatDate(order.created_at)}</p></div><Badge variant="outline">طلب فقط</Badge></div></div>)} emptyMessage={demoMode ? "لا توجد طلبات اصطناعية" : "اختر مساحة طبيب من الخادم أولاً."} />
      </section>

      {liveReadBlocked && <div className="rounded-2xl border border-amber-200 bg-amber-50/70 p-5 text-sm leading-7 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200" role="status"><LockKeyhole className="ml-2 inline h-4 w-4" />{errorMessage(patientsQuery.error ?? ordersQuery.error)}</div>}

      <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70"><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Workflow className="h-5 w-5 text-[#0D9488]" />الوصول السريع</CardTitle><p className="mt-1 text-xs text-muted-foreground">تنتقل الروابط إلى المساحات المحكومة الموجودة؛ لا يعني وجود الرابط توفر الكتابة أو الوصول السريري.</p></CardHeader><CardContent className="grid gap-3 sm:grid-cols-2">{QUICK_LINKS.map(({ label, detail, path, icon: Icon }) => <Link key={path} to={path} className="group flex items-center gap-3 rounded-xl border border-slate-200/80 p-3.5 transition hover:-translate-y-0.5 hover:border-teal-300 hover:bg-teal-50/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 dark:border-white/10 dark:hover:border-teal-800 dark:hover:bg-teal-950/20"><span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200"><Icon className="h-4 w-4" /></span><span className="min-w-0 flex-1"><span className="block text-sm font-bold">{label}</span><span className="mt-1 block truncate text-xs text-muted-foreground">{detail}</span></span><ArrowUpLeft className="h-4 w-4 text-muted-foreground transition group-hover:-translate-y-0.5 group-hover:text-teal-600" /></Link>)}</CardContent></Card>
        <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70"><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Workflow className="h-5 w-5 text-[#0D9488]" />خريطة الرحلة السريرية</CardTitle><p className="mt-1 text-xs text-muted-foreground">المتاح يعكس العقود الحالية فقط؛ والباقي يظهر كفجوة مقصودة لا كميزة وهمية.</p></CardHeader><CardContent className="grid gap-3 sm:grid-cols-2">{workflow.map(({ label, detail, status, icon: Icon }) => <div key={label} className="rounded-xl border border-slate-200/80 p-3.5 dark:border-white/10"><div className="flex items-start justify-between gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200"><Icon className="h-4 w-4" /></span><StatusBadge status={status} /></div><p className="mt-3 text-sm font-bold">{label}</p><p className="mt-1 text-xs leading-6 text-muted-foreground">{detail}</p></div>)}</CardContent></Card>
        <Card className="rounded-2xl border-emerald-200/80 bg-gradient-to-br from-emerald-50 via-white to-sky-50 shadow-sm dark:border-emerald-900/50 dark:from-emerald-950/20 dark:via-slate-900/70 dark:to-sky-950/20"><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Stethoscope className="h-5 w-5 text-emerald-700 dark:text-emerald-300" />علي رضا — مرشد الطبيب</CardTitle></CardHeader><CardContent className="space-y-4"><p className="text-sm leading-7 text-slate-700 dark:text-slate-200">يمكن للمساعد شرح المسارات وتنظيم المعلومات داخل السياق، لكنه لا يقرر صلاحية الوصول، ولا يكتب نتيجة، ولا يوقّع وصفة، ولا يستبدل الطبيب.</p><div className="rounded-xl border border-emerald-200/80 bg-white/70 p-4 text-xs leading-6 text-emerald-950 dark:border-emerald-900/50 dark:bg-white/5 dark:text-emerald-100"><CheckCircle2 className="ml-1 inline h-4 w-4" />أي استخدام سريري حقيقي يحتاج Authorization وConsent وAudit من الخادم.</div><Link to="/ai" className="inline-flex items-center gap-2 text-sm font-bold text-emerald-800 hover:underline dark:text-emerald-200">فتح مساحة المساعد <ArrowUpLeft className="h-4 w-4" /></Link></CardContent></Card>
      </section>

      <div className="flex flex-col gap-3 rounded-2xl border border-amber-200 bg-amber-50/70 p-5 text-sm leading-7 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200 sm:flex-row sm:items-start"><ShieldCheck className="mt-1 h-5 w-5 shrink-0" /><p><strong>حدود التنفيذ:</strong> هذه الواجهة لا تنشئ عضوية أو دوراً مهنياً، ولا تعرض الملف الكامل، ولا تنفذ Encounter أو Prescription أو Referral أو Break-Glass. في الوضع الحي، المرضى والطلبات يمران فقط عبر clinical gateway المقيد؛ وعند غياب سلسلة الثقة تُرفض القراءة بدلاً من استخدام fallback قديم.</p></div>
    </div>
  );
}

function WorkspaceCard({ workspace, selected, onSelect, switching }: { workspace: WorkspaceSummary; selected: boolean; onSelect: () => void; switching: boolean }) {
  const active = isActive(workspace);
  return <div className={`rounded-xl border p-4 transition ${selected ? "border-teal-400 bg-teal-50/60 dark:border-teal-700 dark:bg-teal-950/20" : "border-slate-200/80 dark:border-white/10"}`}><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div className="flex items-start gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200"><Stethoscope className="h-5 w-5" /></span><div><p className="text-sm font-bold">{workspace.name_ar ?? workspace.name}</p><p className="mt-1 text-xs text-muted-foreground">{workspace.organization_id ?? "مؤسسة غير معروضة"} · {workspace.department_id ?? "قسم غير معروض"}</p></div></div><div className="flex items-center gap-2"><Badge variant={active ? "success" : "outline"}>{workspace.status}</Badge><Button type="button" size="sm" variant={selected ? "secondary" : "outline"} disabled={!active || selected || switching} onClick={onSelect}>{switching ? <RefreshCw className="h-4 w-4 animate-spin" /> : selected ? "السياق الحالي" : "تفعيل السياق"}</Button></div></div><div className="mt-3 flex flex-wrap gap-2 text-[11px] text-muted-foreground"><span className="rounded-full bg-slate-100 px-2 py-1 dark:bg-white/10">{workspace.professional_type ?? "نوع مهني غير معروض"}</span><span className="rounded-full bg-slate-100 px-2 py-1 dark:bg-white/10">{workspace.facility_id ?? "منشأة غير معروضة"}</span></div></div>;
}

function TrustRow({ label, value }: { label: string; value: string }) {
  return <div className="flex items-center justify-between gap-3 rounded-xl border border-slate-200/80 p-3 text-sm dark:border-white/10"><span className="text-muted-foreground">{label}</span><span className="inline-flex items-center gap-1.5 font-bold text-emerald-700 dark:text-emerald-300"><CheckCircle2 className="h-3.5 w-3.5" />{value}</span></div>;
}

function GatedPanel({ title, description }: { title: string; description: string }) {
  return <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-5 text-sm leading-7 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200"><LockKeyhole className="ml-2 inline h-4 w-4" /><strong>{title}</strong><p className="mt-2 text-xs leading-6 opacity-80">{description}</p></div>;
}

function ClinicalReadCard({ title, icon: Icon, loading, error, empty, emptyMessage, items }: { title: string; icon: LucideIcon; loading: boolean; error: unknown; empty: boolean; emptyMessage: string; items: React.ReactNode[] }) {
  const state = loading ? "loading" : error ? "error" : empty ? "forbidden" : items.length ? "loaded" : "empty";
  return <Card className="gula-interactive-surface"><CardHeader className="flex flex-row items-center justify-between space-y-0"><CardTitle className="flex items-center gap-2 text-base"><Icon className="h-5 w-5 text-[#0D9488]" />{title}</CardTitle><Badge variant={error || empty ? "warning" : "outline"}>{error || empty ? "محجوب" : "حد أدنى"}</Badge></CardHeader><CardContent className="space-y-2">{state === "loading" ? <ClinicalStatePanel state="loading" title="جارٍ التحقق من سياق القراءة" description="ننتظر استجابة الخادم قبل عرض أي بيانات سريرية." /> : state === "error" ? <ClinicalStatePanel state="error" title="القراءة موقوفة بأمان" description={errorMessage(error)} /> : state === "forbidden" ? <ClinicalStatePanel state="forbidden" title="سياق القراءة مطلوب" description={emptyMessage} /> : state === "empty" ? <ClinicalStatePanel state="empty" title="لا توجد سجلات" description="لا توجد سجلات ضمن النطاق الحالي." /> : items}</CardContent></Card>;
}

export default DoctorWorkspacePanel;
