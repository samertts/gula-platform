import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  Activity,
  Building2,
  CheckCircle2,
  ChevronLeft,
  ClipboardCheck,
  FileCheck2,
  FlaskConical,
  LockKeyhole,
  Network,
  ShieldCheck,
  Users,
  Wrench,
  type LucideIcon,
} from "lucide-react";
import { apiClient, type MembershipSummary, type WorkspaceSummary } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { Badge } from "@/components/ui/Badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

type OrganizationTab = "overview" | "facilities" | "memberships" | "governance";

type DemoFacility = {
  id: string;
  name: string;
  city: string;
  status: string;
  departments: string[];
};

type LiveFacility = {
  id: string;
  label: string;
  departments: string[];
  workspaceCount: number;
};

type DemoMembership = {
  facility: string;
  department: string;
  role: string;
  status: string;
  scope: string;
};

type Capability = {
  label: string;
  detail: string;
  status: "عرض تجريبي" | "عقد خادمي مطلوب";
  icon: LucideIcon;
};

const DEMO_FACILITIES: DemoFacility[] = [
  { id: "demo-facility-babylon", name: "فرع بابل الطبي", city: "بابل", status: "تشغيلي للعرض", departments: ["الاستقبال", "العيادة", "المختبر"] },
  { id: "demo-facility-baghdad", name: "فرع بغداد الطبي", city: "بغداد", status: "مخطط للعرض", departments: ["العيادة", "الأشعة", "الجودة"] },
  { id: "demo-facility-karbala", name: "فرع كربلاء الطبي", city: "كربلاء", status: "مخطط للعرض", departments: ["الطوارئ", "الصيدلية"] },
];

const DEMO_MEMBERSHIPS: DemoMembership[] = [
  { facility: "فرع بابل الطبي", department: "العيادة", role: "المدير الطبي — تجريبي", status: "نشطة للعرض", scope: "منشأة واحدة" },
  { facility: "فرع بابل الطبي", department: "المختبر", role: "مسؤول جودة — تجريبي", status: "نشطة للعرض", scope: "قسم واحد" },
  { facility: "فرع بغداد الطبي", department: "الإدارة", role: "مراجع مؤسسي — تجريبي", status: "معلّقة للعرض", scope: "قراءة فقط" },
];

const DEMO_CAPABILITIES: Capability[] = [
  { label: "الفروع والأقسام", detail: "تمثيل المؤسسة والـFacility والـDepartment دون إنشاء فعلي", status: "عرض تجريبي", icon: Building2 },
  { label: "العضويات والأدوار", detail: "Role منفصل عن الاختصاص والصلاحية النهائية", status: "عرض تجريبي", icon: Users },
  { label: "الخدمات والترخيص", detail: "الخدمة لا تُفعّل خارج نطاق الترخيص والسياسة", status: "عقد خادمي مطلوب", icon: FileCheck2 },
  { label: "الأجهزة والتكامل", detail: "لا اتصال مباشر بقاعدة البيانات؛ يلزم gateway مؤسسي", status: "عقد خادمي مطلوب", icon: Wrench },
  { label: "الجودة والتدقيق", detail: "الحوادث والشكاوى والتقارير تحتاج نطاقاً وتدقيقاً", status: "عقد خادمي مطلوب", icon: ClipboardCheck },
  { label: "المالية والتأمين", detail: "Financial domain منفصل عن Clinical domain", status: "عقد خادمي مطلوب", icon: Network },
];

const TABS: Array<{ id: OrganizationTab; label: string; icon: LucideIcon }> = [
  { id: "overview", label: "نظرة عامة", icon: Activity },
  { id: "facilities", label: "الفروع والأقسام", icon: Building2 },
  { id: "memberships", label: "العضويات والأدوار", icon: Users },
  { id: "governance", label: "الحوكمة والاعتماد", icon: ShieldCheck },
];

function statusVariant(status: string): "success" | "warning" | "outline" | "default" {
  const normalized = status.toLowerCase();
  if (normalized.includes("active") || normalized.includes("مفعّلة") || normalized.includes("نشطة") || normalized.includes("تشغيلي")) return "success";
  if (normalized.includes("review") || normalized.includes("مراجعة") || normalized.includes("معلّقة") || normalized.includes("مخطط")) return "warning";
  if (normalized.includes("suspend") || normalized.includes("موقوف")) return "default";
  return "outline";
}

function safeStatus(value?: string | null) {
  return value?.trim() || "غير معروض";
}

function liveOrganizations(memberships: MembershipSummary[], workspaces: WorkspaceSummary[]) {
  const ids = new Set<string>();
  memberships.forEach((membership) => ids.add(membership.organization_id));
  workspaces.forEach((workspace) => {
    if (workspace.organization_id) ids.add(workspace.organization_id);
  });
  return [...ids].sort();
}

function liveFacilities(workspaces: WorkspaceSummary[], organizationId?: string): LiveFacility[] {
  const facilities = new Map<string, LiveFacility>();
  workspaces.filter((workspace) => workspace.organization_id === organizationId && workspace.facility_id).forEach((workspace) => {
    const id = workspace.facility_id!;
    const current = facilities.get(id) ?? { id, label: workspace.name_ar ?? workspace.name, departments: [], workspaceCount: 0 };
    if (workspace.department_id && !current.departments.includes(workspace.department_id)) current.departments.push(workspace.department_id);
    current.workspaceCount += 1;
    facilities.set(id, current);
  });
  return [...facilities.values()];
}

export function OrganizationWorkspacePage() {
  const { demoMode, user } = useAuth();
  const [activeTab, setActiveTab] = useState<OrganizationTab>("overview");
  const [selectedOrganizationId, setSelectedOrganizationId] = useState<string | null>(null);

  const workspacesQuery = useQuery({
    queryKey: ["organization-workspaces", "me"],
    queryFn: () => apiClient.listWorkspaces(),
    enabled: !demoMode,
    retry: false,
    staleTime: 30_000,
  });
  const membershipsQuery = useQuery({
    queryKey: ["organization-memberships", "me"],
    queryFn: () => apiClient.listMyMemberships(),
    enabled: !demoMode,
    retry: false,
    staleTime: 30_000,
  });

  const memberships = membershipsQuery.data?.memberships ?? [];
  const workspaces = workspacesQuery.data?.workspaces ?? [];
  const organizationIds = useMemo(() => liveOrganizations(memberships, workspaces), [memberships, workspaces]);
  const selectedOrganization = demoMode ? "demo-gula-health" : selectedOrganizationId ?? organizationIds[0];
  const facilities: Array<DemoFacility | LiveFacility> = demoMode ? DEMO_FACILITIES : liveFacilities(workspaces, selectedOrganization);
  const organizationMemberships = memberships.filter((membership) => membership.organization_id === selectedOrganization);
  const loading = !demoMode && (workspacesQuery.isLoading || membershipsQuery.isLoading);
  const error = !demoMode && (workspacesQuery.error || membershipsQuery.error);

  return (
    <div className="mx-auto max-w-7xl space-y-6 pb-2" dir="rtl">
      <section className="relative overflow-hidden rounded-[1.75rem] border border-slate-200/80 bg-[#0F172A] p-5 text-white shadow-[0_24px_70px_-35px_rgba(15,23,42,0.75)] dark:border-white/10 sm:p-7">
        <div className="absolute -left-12 -top-24 h-64 w-64 rounded-full bg-[#0D9488]/25 blur-3xl" />
        <div className="absolute -bottom-32 right-8 h-72 w-72 rounded-full bg-sky-500/20 blur-3xl" />
        <div className="relative grid gap-7 lg:grid-cols-[1fr_auto] lg:items-end">
          <div className="max-w-3xl">
            <div className="mb-4 flex flex-wrap items-center gap-2 text-xs font-semibold"><span className="inline-flex items-center gap-2 rounded-full border border-teal-200/20 bg-teal-200/10 px-3 py-1.5 text-teal-100"><span className="h-2 w-2 rounded-full bg-teal-300" />بوابة المؤسسة الصحية</span>{demoMode && <span className="inline-flex items-center gap-2 rounded-full border border-amber-300/20 bg-amber-300/10 px-3 py-1.5 text-amber-100"><ShieldCheck className="h-3.5 w-3.5" />عرض اصطناعي معزول</span>}</div>
            <p className="text-sm text-teal-200">مرحباً{user?.name ? `، ${user.name}` : " بكم"}</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">كيان صحي مستقل، وفروع متعددة، وصلاحيات محكومة</h1>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-300">المؤسسة ليست حساباً كبيراً للموظفين. هي كيان له دورة حياة وترخيص وفروع وعضويات وخدمات، بينما يبقى الاعتماد والوصول والعمليات الحساسة تحت قرار الخادم.</p>
            {demoMode && <div className="mt-5 inline-flex max-w-2xl flex-wrap items-center gap-2 rounded-2xl border border-amber-200/20 bg-amber-200/10 px-3.5 py-2.5 text-xs text-amber-100"><LockKeyhole className="h-3.5 w-3.5" /><strong>لا توجد مؤسسة حقيقية</strong><span className="text-amber-100/70">— كل الفروع والعضويات مؤلفة للشرح والتدريب.</span></div>}
          </div>
          <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.07] p-4 text-sm text-slate-200 backdrop-blur-sm"><span className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-400/15 text-teal-200"><Building2 className="h-6 w-6" /></span><div><p className="font-bold">{demoMode ? "مؤسسة GULA التجريبية" : selectedOrganization ? `مؤسسة ${selectedOrganization}` : "لم يُحدد سياق مؤسسي"}</p><p className="mt-1 text-xs text-slate-400">{demoMode ? "نموذج قراءة فقط" : "مُستخلص من العضويات والمساحات"}</p></div></div>
        </div>
      </section>

      {!demoMode && organizationIds.length > 1 && <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70"><CardHeader><CardTitle className="text-base">مؤسساتك المرتبطة</CardTitle><p className="mt-1 text-xs text-muted-foreground">اختيار المؤسسة يغيّر نطاق العرض فقط؛ لا ينشئ عضوية أو صلاحية جديدة.</p></CardHeader><CardContent className="flex flex-wrap gap-2">{organizationIds.map((organizationId) => <button key={organizationId} type="button" onClick={() => setSelectedOrganizationId(organizationId)} className={`rounded-xl border px-4 py-2 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 ${selectedOrganization === organizationId ? "border-teal-400 bg-teal-50 text-teal-800 dark:border-teal-700 dark:bg-teal-950/30 dark:text-teal-200" : "border-slate-200/80 hover:border-teal-300 dark:border-white/10"}`}>{organizationId}</button>)}</CardContent></Card>}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="مؤشرات المؤسسة الصحية">
        <OrgMetric label="حالة المؤسسة" value={demoMode ? "قيد المراجعة" : loading ? "…" : selectedOrganization ? "مرتبطة" : "غير مثبتة"} detail={demoMode ? "سيناريو اعتماد اصطناعي" : "من عقود الخادم"} icon={ShieldCheck} />
        <OrgMetric label="الفروع" value={demoMode ? String(DEMO_FACILITIES.length) : loading ? "…" : String(facilities.length)} detail={demoMode ? "بيانات للعرض" : "مساحات منشأة معادة"} icon={Building2} />
        <OrgMetric label="العضويات" value={demoMode ? String(DEMO_MEMBERSHIPS.length) : loading ? "…" : String(organizationMemberships.length)} detail={demoMode ? "لا تغيّر الصلاحيات" : "ضمن المؤسسة المحددة"} icon={Users} />
        <OrgMetric label="الخدمات" value="—" detail="تحتاج عقد قدرات وترخيص" icon={FlaskConical} />
      </section>

      <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70"><CardContent className="p-0"><div className="flex flex-wrap border-b">{TABS.map(({ id, label, icon: Icon }) => <button key={id} type="button" onClick={() => setActiveTab(id)} className={`flex items-center gap-2 px-4 py-3 text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 ${activeTab === id ? "border-b-2 border-teal-600 text-teal-700 dark:text-teal-300" : "text-muted-foreground hover:text-foreground"}`} aria-selected={activeTab === id}><Icon className="h-4 w-4" />{label}</button>)}</div></CardContent></Card>

      {loading && <div className="rounded-2xl border border-dashed p-8 text-center text-sm text-muted-foreground" role="status">جارٍ تحميل عضوياتك ومساحاتك المؤسسية من الخادم…</div>}
      {error && <div className="rounded-2xl border border-amber-200 bg-amber-50/70 p-5 text-sm leading-7 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200" role="alert"><LockKeyhole className="ml-2 inline h-4 w-4" />تعذر عرض البيانات المؤسسية في هذا السياق. لم يتم استخدام بيانات تجريبية أو fallback غير مصرح به.</div>}

      {!loading && !error && activeTab === "overview" && <OverviewTab demoMode={demoMode} facilities={facilities} />}
      {!loading && !error && activeTab === "facilities" && <FacilitiesTab demoMode={demoMode} facilities={facilities} />}
      {!loading && !error && activeTab === "memberships" && <MembershipsTab demoMode={demoMode} memberships={demoMode ? DEMO_MEMBERSHIPS : organizationMemberships} />}
      {!loading && !error && activeTab === "governance" && <GovernanceTab demoMode={demoMode} />}

      <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]"><Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70"><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Network className="h-5 w-5 text-[#0D9488]" />حدود المؤسسة في GULA</CardTitle><p className="mt-1 text-xs text-muted-foreground">كل قدرة تحتاج عقداً ونطاقاً وسياسة مستقلة.</p></CardHeader><CardContent className="grid gap-3 sm:grid-cols-2">{DEMO_CAPABILITIES.map(({ label, detail, status, icon: Icon }) => <div key={label} className="rounded-xl border border-slate-200/80 p-3.5 dark:border-white/10"><div className="flex items-start justify-between gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200"><Icon className="h-4 w-4" /></span><Badge variant={status === "عرض تجريبي" ? "warning" : "outline"}>{demoMode ? status : "محجوب"}</Badge></div><p className="mt-3 text-sm font-bold">{label}</p><p className="mt-1 text-xs leading-6 text-muted-foreground">{detail}</p></div>)}</CardContent></Card><Card className="rounded-2xl border-emerald-200/80 bg-gradient-to-br from-emerald-50 via-white to-sky-50 shadow-sm dark:border-emerald-900/50 dark:from-emerald-950/20 dark:via-slate-900/70 dark:to-sky-950/20"><CardHeader><CardTitle className="flex items-center gap-2 text-base"><ShieldCheck className="h-5 w-5 text-emerald-700 dark:text-emerald-300" />قاعدة الأمان</CardTitle></CardHeader><CardContent className="space-y-4"><p className="text-sm leading-7 text-slate-700 dark:text-slate-200">المؤسسة لا تملك المواطن، والمالك لا يصبح طبيباً، والمدير لا يحصل تلقائياً على صلاحيات مالية أو سريرية. كل وصول يحدد عبر المؤسسة والمنشأة والقسم والدور والغرض والسياسة.</p><div className="rounded-xl border border-emerald-200/80 bg-white/70 p-4 text-xs leading-6 text-emerald-950 dark:border-emerald-900/50 dark:bg-white/5 dark:text-emerald-100"><CheckCircle2 className="ml-1 inline h-4 w-4" />لا توجد أزرار إنشاء أو اعتماد أو دعوة في هذه النسخة قبل وجود عقد خادمي مكتمل.</div><Link to="/my-record" className="inline-flex items-center gap-2 text-sm font-bold text-emerald-800 hover:underline dark:text-emerald-200">العودة إلى مركز الهوية والمساحات <ChevronLeft className="h-4 w-4" /></Link></CardContent></Card></section>

      <div className="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50/70 p-5 text-sm leading-7 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200"><ShieldCheck className="mt-1 h-5 w-5 shrink-0" /><p><strong>حدود التنفيذ:</strong> لا تنشئ هذه الصفحة مؤسسة أو فرعاً أو موظفاً، ولا تعتمد ترخيصاً، ولا تمنح دوراً، ولا تعرض قائمة موظفين أو مرضى حقيقيين. في Live تُقرأ العضويات والمساحات فقط، بينما التسجيل والاعتماد والخدمات والأجهزة والمالية والجودة والطوارئ تبقى محجوبة حتى اعتماد عقودها وعزلها وتدقيقها.</p></div>
    </div>
  );
}

function OrgMetric({ label, value, detail, icon: Icon }: { label: string; value: string; detail: string; icon: LucideIcon }) {
  return <Card className="overflow-hidden rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70"><CardContent className="relative p-5"><div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-l from-teal-500 to-sky-400" /><div className="flex items-start justify-between gap-3"><span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200"><Icon className="h-5 w-5" /></span><Badge variant="outline">{detail === "من عقود الخادم" ? "خادمي" : "قراءة"}</Badge></div><p className="mt-5 text-sm text-muted-foreground">{label}</p><p className="mt-1 text-3xl font-bold tracking-tight text-[#0F172A] dark:text-white">{value}</p><p className="mt-2 text-[11px] text-muted-foreground">{detail}</p></CardContent></Card>;
}

function OverviewTab({ demoMode, facilities }: { demoMode: boolean; facilities: Array<DemoFacility | LiveFacility> }) {
  return <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]"><Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70"><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Building2 className="h-5 w-5 text-[#0D9488]" />دورة حياة المؤسسة</CardTitle><p className="mt-1 text-xs text-muted-foreground">إدخال البيانات لا يساوي اعتماد المؤسسة.</p></CardHeader><CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{["Draft", "Submitted", "Under Review", "Verified", "Approved", "Active"].map((step, index) => <div key={step} className={`rounded-xl border p-4 ${index < (demoMode ? 3 : 1) ? "border-emerald-200 bg-emerald-50/50 dark:border-emerald-900/50 dark:bg-emerald-950/20" : "border-slate-200/80 dark:border-white/10"}`}><p className="text-xs font-bold text-muted-foreground">0{index + 1}</p><p className="mt-2 text-sm font-bold">{step}</p><p className="mt-1 text-xs leading-6 text-muted-foreground">{index < (demoMode ? 3 : 1) ? "حالة ممثلة للعرض" : "قرار خادمي مطلوب"}</p></div>)}</CardContent></Card><Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70"><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Activity className="h-5 w-5 text-sky-600" />ملخص الفروع</CardTitle></CardHeader><CardContent className="space-y-3">{facilities.length ? facilities.slice(0, 4).map((facility) => <div key={facility.id} className="flex items-center justify-between gap-3 rounded-xl border border-slate-200/80 p-3 dark:border-white/10"><div><p className="text-sm font-bold">{"name" in facility ? facility.name : facility.label}</p><p className="mt-1 text-xs text-muted-foreground">{"city" in facility ? facility.city : `${facility.departments.length} أقسام معادة`}
</p></div><Badge variant={statusVariant("تشغيلي")}>{"status" in facility ? facility.status : `${facility.workspaceCount} سياقات`}</Badge></div>) : <EmptyState text="لا توجد مرافق ضمن السياق الحالي." />}</CardContent></Card></section>;
}

function FacilitiesTab({ demoMode, facilities }: { demoMode: boolean; facilities: Array<DemoFacility | LiveFacility> }) {
  return <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70"><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Building2 className="h-5 w-5 text-[#0D9488]" />الفروع والأقسام</CardTitle><p className="mt-1 text-xs text-muted-foreground">الفرع ليس مؤسسة جديدة، ولا يعني وجوده منح صلاحيات عابرة للفروع.</p></CardHeader><CardContent className="grid gap-4 md:grid-cols-2">{facilities.length ? facilities.map((facility) => <div key={facility.id} className="rounded-2xl border border-slate-200/80 p-5 dark:border-white/10"><div className="flex items-start justify-between gap-3"><div><p className="font-bold">{"name" in facility ? facility.name : facility.label}</p><p className="mt-1 text-xs text-muted-foreground">{"city" in facility ? facility.city : `Facility ${facility.id}`}</p></div><Badge variant={statusVariant("active")}>{demoMode ? "للعرض" : "من الخادم"}</Badge></div><div className="mt-4 flex flex-wrap gap-2">{("departments" in facility ? facility.departments : []).map((department) => <span key={department} className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-700 dark:bg-white/10 dark:text-slate-200">{department}</span>)}</div><p className="mt-4 text-xs leading-6 text-muted-foreground">{demoMode ? "الأجهزة والخدمات والترخيص غير تشغيلية في Demo." : "المساحات المعادة لا تثبت وحدها اعتماد الخدمة أو صلاحية المستخدم."}</p></div>) : <EmptyState text="لا توجد فروع خادمية ضمن المؤسسة المحددة." />}</CardContent></Card>;
}

function MembershipsTab({ demoMode, memberships }: { demoMode: boolean; memberships: DemoMembership[] | MembershipSummary[] }) {
  const rows = memberships.map((membership, index) => {
    if (demoMode && "facility" in membership) {
      return <div key={`${membership.facility}-${index}`} className="flex flex-col gap-3 rounded-xl border border-slate-200/80 p-4 sm:flex-row sm:items-center sm:justify-between dark:border-white/10"><div><p className="text-sm font-bold">{membership.role}</p><p className="mt-1 text-xs text-muted-foreground">{membership.facility} · {membership.department} · {membership.scope}</p></div><Badge variant={statusVariant(membership.status)}>{membership.status}</Badge></div>;
    }
    if (!("facility" in membership)) {
      return <div key={membership.id} className="flex flex-col gap-3 rounded-xl border border-slate-200/80 p-4 sm:flex-row sm:items-center sm:justify-between dark:border-white/10"><div><p className="text-sm font-bold">عضوية ضمن المؤسسة</p><p className="mt-1 text-xs text-muted-foreground">{safeStatus(membership.relationship_type)} · {safeStatus(membership.facility_id)} · {safeStatus(membership.department_id)} · {safeStatus(membership.scope_type)}</p></div><Badge variant={statusVariant(membership.status)}>{safeStatus(membership.status)}</Badge></div>;
    }
    return null;
  });
  return <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70"><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Users className="h-5 w-5 text-[#0D9488]" />العضويات والأدوار</CardTitle><p className="mt-1 text-xs text-muted-foreground">العضوية علاقة مستقلة؛ لا تنشئ هوية جديدة ولا تجعل الدور مساوياً للاختصاص.</p></CardHeader><CardContent className="space-y-3">{rows.length ? rows : <EmptyState text="لا توجد عضويات ضمن المؤسسة المحددة." />}</CardContent></Card>;
}

function GovernanceTab({ demoMode }: { demoMode: boolean }) {
  const gates = [
    ["اعتماد المؤسسة", demoMode ? "مراجعة اصطناعية" : "غير متاح من العقد الحالي"],
    ["نطاق الترخيص", "يتطلب سجل ترخيص وقدرات خادمية"],
    ["مراجعة الوصول", "يتطلب Access Review مؤسسياً"],
    ["التدقيق", "لا حذف صامتاً للسجل"],
  ];
  return <section className="grid gap-6 xl:grid-cols-[1fr_1fr]"><Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70"><CardHeader><CardTitle className="flex items-center gap-2 text-base"><ShieldCheck className="h-5 w-5 text-emerald-600" />بوابات الاعتماد والامتثال</CardTitle></CardHeader><CardContent className="space-y-3">{gates.map(([label, detail]) => <div key={label} className="flex items-start gap-3 rounded-xl border border-slate-200/80 p-4 dark:border-white/10"><CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" /><div><p className="text-sm font-bold">{label}</p><p className="mt-1 text-xs leading-6 text-muted-foreground">{detail}</p></div></div>)}</CardContent></Card><Card className="rounded-2xl border-amber-200 bg-amber-50/60 shadow-sm dark:border-amber-900/50 dark:bg-amber-950/20"><CardHeader><CardTitle className="flex items-center gap-2 text-base"><LockKeyhole className="h-5 w-5 text-amber-700 dark:text-amber-300" />ما لا تفعله الواجهة</CardTitle></CardHeader><CardContent className="text-sm leading-7 text-amber-950 dark:text-amber-200">لا تعتمد ترخيصاً، ولا تغيّر حالة المؤسسة، ولا تدعو موظفاً، ولا تعيّن دوراً، ولا تضيف خدمة أو جهازاً، ولا تقرأ السجل الطبي لمجرد أن المؤسسة مرتبطة بحساب المستخدم.</CardContent></Card></section>;
}

function EmptyState({ text }: { text: string }) {
  return <div className="rounded-xl border border-dashed p-7 text-center text-sm text-muted-foreground">{text}</div>;
}

export default OrganizationWorkspacePage;
