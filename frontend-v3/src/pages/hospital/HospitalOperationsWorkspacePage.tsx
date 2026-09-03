import { useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  AlertTriangle,
  Ambulance,
  ArrowLeft,
  BedDouble,
  Building2,
  ClipboardList,
  FileText,
  HeartPulse,
  Info,
  LockKeyhole,
  ShieldCheck,
  Siren,
  Users,
  Wrench,
  type LucideIcon,
} from "lucide-react";
import { apiClient, type WorkspaceSummary } from "@/api/client";
import { workspaceScopedReads, type ClinicalOrderRead, type ClinicalPatientRead } from "@/api/workspaceScopedReads";
import { useAuth } from "@/contexts/AuthContext";
import { PageHeader } from "@/components/shared/PageComponents";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

type HospitalTab = "overview" | "emergency" | "admissions" | "beds" | "patients" | "orders" | "care-team" | "operations" | "discharge" | "audit";
type BedStatus = "متاح" | "محجوز" | "مشغول" | "تنظيف" | "صيانة" | "عزل";

type DemoBed = { label: string; ward: string; status: BedStatus; patient?: string };
type DemoAdmission = { id: string; patient: string; route: string; unit: string; status: "بانتظار السرير" | "مقبول" | "مراقبة" | "خرج"; priority: "عادي" | "عاجل" };

const DEMO_BEDS: DemoBed[] = [
  { label: "A-101", ward: "الجناح A", status: "مشغول", patient: "مريض اصطناعي 01" },
  { label: "A-102", ward: "الجناح A", status: "متاح" },
  { label: "B-204", ward: "الجناح B", status: "تنظيف" },
  { label: "ICU-03", ward: "العناية المركزة", status: "مشغول", patient: "مريض اصطناعي 02" },
  { label: "ICU-04", ward: "العناية المركزة", status: "عزل" },
  { label: "OR-02", ward: "غرفة العمليات", status: "صيانة" },
];

const DEMO_ADMISSIONS: DemoAdmission[] = [
  { id: "adm-demo-1", patient: "مريض اصطناعي 01", route: "إدخال مجدول", unit: "الباطنية", status: "مراقبة", priority: "عادي" },
  { id: "adm-demo-2", patient: "مريض اصطناعي 02", route: "طوارئ", unit: "العناية المركزة", status: "مقبول", priority: "عاجل" },
  { id: "adm-demo-3", patient: "مريض اصطناعي 03", route: "إحالة داخلية", unit: "الجراحة", status: "بانتظار السرير", priority: "عاجل" },
];

const DEMO_EMERGENCY = [
  { patient: "مريض اصطناعي 04", priority: "P1", area: "إنعاش", status: "فرز أولي" },
  { patient: "مريض اصطناعي 05", priority: "P2", area: "مراقبة", status: "بانتظار الطبيب" },
  { patient: "مريض اصطناعي 06", priority: "P3", area: "الطوارئ العامة", status: "مكتمل" },
];

const TABS: Array<{ id: HospitalTab; label: string; icon: LucideIcon }> = [
  { id: "overview", label: "نظرة المستشفى", icon: Building2 },
  { id: "emergency", label: "الطوارئ والفرز", icon: Siren },
  { id: "admissions", label: "الإدخال والإقامة", icon: Ambulance },
  { id: "beds", label: "مركز الأسرة", icon: BedDouble },
  { id: "patients", label: "المرضى ضمن النطاق", icon: Users },
  { id: "orders", label: "الأوامر والرعاية", icon: ClipboardList },
  { id: "care-team", label: "فريق الرعاية", icon: HeartPulse },
  { id: "operations", label: "العمليات والعناية", icon: Activity },
  { id: "discharge", label: "الخروج والمتابعة", icon: FileText },
  { id: "audit", label: "التدقيق والحوكمة", icon: ShieldCheck },
];

function isActiveWorkspace(workspace: WorkspaceSummary) {
  return ["active", "verified", "approved"].includes(workspace.status.toLowerCase());
}

export default function HospitalOperationsWorkspacePage() {
  const { demoMode } = useAuth();
  return demoMode ? <DemoHospitalWorkspace /> : <LiveHospitalWorkspace />;
}

function DemoHospitalWorkspace() {
  const [activeTab, setActiveTab] = useState<HospitalTab>("overview");
  return <HospitalShell demoMode activeTab={activeTab} onTab={setActiveTab} metrics={[["إشغال الأسرة", "78%", BedDouble], ["إدخالات اليوم", "14", Ambulance], ["الطوارئ", "6", Siren], ["أحداث حرجة", "2", AlertTriangle]]}>
    {activeTab === "overview" && <DemoOverview onTab={setActiveTab} />}
    {activeTab === "emergency" && <DemoEmergency />}
    {activeTab === "admissions" && <DemoAdmissions />}
    {activeTab === "beds" && <DemoBeds />}
    {activeTab === "patients" && <DemoPatients />}
    {activeTab === "orders" && <DemoOrders />}
    {activeTab === "care-team" && <DemoCareTeam />}
    {activeTab === "operations" && <DemoOperations />}
    {activeTab === "discharge" && <DemoDischarge />}
    {activeTab === "audit" && <DemoAudit />}
    <DemoBoundary />
  </HospitalShell>;
}

function LiveHospitalWorkspace() {
  const [activeTab, setActiveTab] = useState<HospitalTab>("overview");
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string | null>(null);
  const [switchingWorkspaceId, setSwitchingWorkspaceId] = useState<string | null>(null);
  const [switchError, setSwitchError] = useState("");
  const workspacesQuery = useQuery({ queryKey: ["hospital-workspaces", "me"], queryFn: () => apiClient.listWorkspaces(), retry: false, staleTime: 30_000 });
  const hospitalWorkspaces = (workspacesQuery.data?.workspaces ?? []).filter((workspace) => {
    const type = workspace.workspace_type.toLowerCase();
    return !workspace.is_personal && Boolean(workspace.facility_id) && (type.includes("hospital") || type.includes("facility"));
  });
  const selectedWorkspace = hospitalWorkspaces.find((workspace) => workspace.id === selectedWorkspaceId);
  const contextReady = Boolean(selectedWorkspaceId && selectedWorkspace && isActiveWorkspace(selectedWorkspace));
  const patientsQuery = useQuery({ queryKey: ["hospital-patients", selectedWorkspaceId], queryFn: () => workspaceScopedReads.listPatients({ limit: 50 }), enabled: contextReady, retry: false, staleTime: 15_000 });
  const ordersQuery = useQuery({ queryKey: ["hospital-orders", selectedWorkspaceId], queryFn: () => workspaceScopedReads.listOrders({ limit: 50 }), enabled: contextReady, retry: false, staleTime: 15_000 });
  const activateWorkspace = async (workspace: WorkspaceSummary) => {
    if (!isActiveWorkspace(workspace) || workspace.id === selectedWorkspaceId) return;
    setSwitchingWorkspaceId(workspace.id);
    setSwitchError("");
    try {
      await apiClient.switchWorkspace(workspace.id);
      setSelectedWorkspaceId(workspace.id);
    } catch (error) {
      setSwitchError(error instanceof Error ? error.message : "تعذر تفعيل سياق المستشفى.");
    } finally {
      setSwitchingWorkspaceId(null);
    }
  };
  const clinicalError = patientsQuery.error || ordersQuery.error;
  return <HospitalShell demoMode={false} activeTab={activeTab} onTab={setActiveTab} metrics={[["المرضى", patientsQuery.data ? String(patientsQuery.data.length) : "—", Users], ["الأوامر", ordersQuery.data ? String(ordersQuery.data.length) : "—", ClipboardList], ["الأسرة", "—", BedDouble], ["الإدخالات", "—", Ambulance]]}>
    <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70"><CardHeader><CardTitle className="flex items-center gap-2 text-base"><ShieldCheck className="h-5 w-5 text-indigo-600" />سياق المستشفى المؤسسي</CardTitle><p className="mt-1 text-xs text-muted-foreground">الإدخال والأسرة والطوارئ والأوامر تتطلب منشأة وعضوية ودوراً وسياقاً خادمياً؛ اختيار workspace لا يمنح الصلاحية وحده.</p></CardHeader><CardContent className="space-y-3">{workspacesQuery.isLoading ? <LoadingMessage text="جارٍ تحميل مساحات المستشفى…" /> : hospitalWorkspaces.length === 0 ? <GatedPanel title="لا توجد مساحة مستشفى مؤكدة" description="تحتاج القراءة الحية إلى Organization Membership وProfessional Verification وFacility Context." /> : hospitalWorkspaces.map((workspace) => <WorkspaceCard key={workspace.id} workspace={workspace} selected={workspace.id === selectedWorkspaceId} switching={switchingWorkspaceId === workspace.id} onSelect={() => void activateWorkspace(workspace)} />)}{switchError && <p className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/20 dark:text-rose-200" role="alert">{switchError}</p>}{workspacesQuery.error && <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200" role="alert">تعذر قراءة مساحات المستشفى من الخادم.</p>}</CardContent></Card>
    {activeTab === "overview" && <LiveOverview contextReady={contextReady} loading={patientsQuery.isLoading || ordersQuery.isLoading} error={clinicalError} patients={patientsQuery.data} orders={ordersQuery.data} onTab={setActiveTab} />}
    {activeTab === "patients" && <LivePatients contextReady={contextReady} loading={patientsQuery.isLoading} error={patientsQuery.error} patients={patientsQuery.data} />}
    {activeTab === "orders" && <LiveOrders contextReady={contextReady} loading={ordersQuery.isLoading} error={ordersQuery.error} orders={ordersQuery.data} />}
    {activeTab === "emergency" && <GatedPanel title="عمليات الطوارئ والفرز محجوبة" description="لا يبدأ Emergency Encounter أو Break-Glass أو Triage من الواجهة قبل عقد يفرض السبب والأولوية والحد الأدنى من الوصول والتدقيق." />}
    {activeTab === "admissions" && <GatedPanel title="الإدخال والقبول محجوبان" description="Admission ليس Bed؛ يلزم عقد قبول وتحقق هوية وتخصيص سرير وتدقيق ونطاق منشأة." />}
    {activeTab === "beds" && <GatedPanel title="مركز الأسرة الحي محجوب" description="عقد occupancy العام لا يكفي لعرض أو تخصيص السرير من سياق المؤسسة؛ يلزم facility-scoped bed contract." />}
    {activeTab === "care-team" && <GatedPanel title="فريق الرعاية والإنابة محجوبان" description="لا تُمنح صلاحيات الطبيب أو الممرض من العضوية وحدها؛ يلزم care-team وdelegation وhandover خادمي." />}
    {activeTab === "operations" && <GatedPanel title="العمليات والعناية المركزة محجوبة" description="Surgical وICU وBlood Bank وDevice Gateway مجالات مستقلة تحتاج عقوداً وتدقيقاً وتحققاً متخصصاً." />}
    {activeTab === "discharge" && <GatedPanel title="الخروج والمتابعة محجوبان" description="لا يمكن إنشاء ملخص خروج أو medication reconciliation أو متابعة حية من دون عقد سريري خادمي." />}
    {activeTab === "audit" && <GatedPanel title="تدقيق المستشفى محجوب" description="لا يُعرض سجل نشاط شامل؛ يلزم endpoint purpose-limited مع pagination وminimum disclosure وaudit authorization." />}
    {clinicalError && <div className="rounded-2xl border border-amber-200 bg-amber-50/70 p-5 text-sm leading-7 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200" role="status"><LockKeyhole className="ml-2 inline h-4 w-4" />أوقفنا القراءة عند فشل العقد؛ لم نستخدم Demo أو fallback legacy.</div>}
    <LiveBoundary />
  </HospitalShell>;
}

function HospitalShell({ demoMode, activeTab, onTab, metrics, children }: { demoMode: boolean; activeTab: HospitalTab; onTab: (tab: HospitalTab) => void; metrics: Array<[string, string, LucideIcon]>; children: ReactNode }) { return <div className="mx-auto max-w-7xl space-y-6" dir="rtl"><PageHeader title="عمليات المستشفى" description="Hospital Domain مستقل: الطوارئ والإدخال والأسرة وفريق الرعاية والأوامر والعمليات والعناية والخروج والتدقيق." /><Card className="overflow-hidden border-indigo-200 bg-gradient-to-l from-indigo-50 via-white to-slate-50 dark:border-indigo-900/50 dark:from-indigo-950/30 dark:via-background dark:to-slate-950/30"><CardContent className="p-6"><div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between"><div className="max-w-3xl space-y-3"><div className="flex items-center gap-2 text-indigo-700 dark:text-indigo-300"><Building2 className="h-5 w-5" /><span className="text-sm font-semibold">Hospital Domain · Secure Operations</span></div><h2 className="text-2xl font-bold tracking-tight">المريض أولاً، والسياق قبل الصلاحية</h2><p className="text-sm leading-7 text-muted-foreground">Admission لا يساوي Bed، وOrder لا يساوي Performed، وDispensing لا يساوي Administration. كل انتقال حساس يجب أن يمر عبر خادم GULA.</p><div className="flex flex-wrap gap-2"><Badge variant={demoMode ? "success" : "outline"}><ShieldCheck className="ml-1 h-3.5 w-3.5" />{demoMode ? "عرض اصطناعي معزول" : "سياق خادمي مطلوب"}</Badge><Badge variant="outline"><LockKeyhole className="ml-1 h-3.5 w-3.5" />RBAC + Context</Badge><Badge variant="outline"><Wrench className="ml-1 h-3.5 w-3.5" />Audit required</Badge></div></div>{demoMode && <div className="grid min-w-[270px] grid-cols-2 gap-3"><SmallMetric label="إشغال" value="78%" icon={BedDouble} /><SmallMetric label="طوارئ" value="6" icon={Siren} /><SmallMetric label="ICU" value="90%" icon={HeartPulse} /><SmallMetric label="عمليات" value="3" icon={Activity} /></div>}</div></CardContent></Card><MetricGrid metrics={metrics} /><HospitalTabs activeTab={activeTab} onChange={onTab} />{children}</div>; }
function HospitalTabs({ activeTab, onChange }: { activeTab: HospitalTab; onChange: (tab: HospitalTab) => void }) { return <Card><CardContent className="p-0"><div className="flex flex-wrap border-b">{TABS.map(({ id, label, icon: Icon }) => <button key={id} type="button" onClick={() => onChange(id)} aria-selected={activeTab === id} className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 ${activeTab === id ? "border-b-2 border-indigo-600 text-indigo-700 dark:text-indigo-300" : "text-muted-foreground hover:text-foreground"}`}><Icon className="h-4 w-4" />{label}</button>)}</div></CardContent></Card>; }
function MetricGrid({ metrics }: { metrics: Array<[string, string, LucideIcon]> }) { return <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="مؤشرات المستشفى">{metrics.map(([label, value, Icon]) => <Card key={label} className="overflow-hidden rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70"><CardContent className="relative p-5"><div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-l from-indigo-500 to-slate-400" /><div className="flex items-start justify-between gap-3"><span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200"><Icon className="h-5 w-5" /></span><Badge variant="outline">{value === "—" ? "محجوب" : "حالة"}</Badge></div><p className="mt-5 text-sm text-muted-foreground">{label}</p><p className="mt-1 text-3xl font-bold tracking-tight text-[#0F172A] dark:text-white">{value}</p></CardContent></Card>)}</section>; }
function SmallMetric({ label, value, icon: Icon }: { label: string; value: string; icon: LucideIcon }) { return <div className="rounded-xl bg-background/80 p-3 shadow-sm"><div className="flex items-center justify-between gap-2"><p className="text-xs text-muted-foreground">{label}</p><Icon className="h-4 w-4 text-indigo-600" /></div><p className="mt-1 text-2xl font-bold">{value}</p></div>; }
function DemoOverview({ onTab }: { onTab: (tab: HospitalTab) => void }) { return <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(300px,0.8fr)]"><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Siren className="h-5 w-5 text-rose-600" />ما يحتاج الفريق الآن</CardTitle></CardHeader><CardContent className="space-y-3"><PriorityCard title="طوارئ P1" subtitle="مريض اصطناعي 04 · إنعاش · فرز أولي" tone="critical" onClick={() => onTab("emergency")} /><PriorityCard title="سرير ICU" subtitle="ICU-03 مشغول · ICU-04 عزل · مراجعة إشغال" tone="warning" onClick={() => onTab("beds")} /><PriorityCard title="قبول بانتظار السرير" subtitle="مريض اصطناعي 03 · الجراحة · عاجل" tone="info" onClick={() => onTab("admissions")} /></CardContent></Card><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><ShieldCheck className="h-5 w-5 text-indigo-600" />حوكمة المستشفى</CardTitle></CardHeader><CardContent className="space-y-3"><p className="text-sm leading-7 text-muted-foreground">كل موظف يعمل بحسابه وهويته المهنية. لا مشاركة كلمات مرور، ولا وصول لمجرد الوجود داخل الفريق.</p><p className="rounded-xl border border-amber-200 bg-amber-50/70 p-3 text-xs leading-6 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200">علي رضا يشرح الإجراءات ويذكّر بالمهام؛ لا يشخّص ولا يوقع ولا يمنح صلاحية ولا يعطي Blood Product.</p><button type="button" onClick={() => onTab("audit")} className="flex w-full items-center justify-between rounded-xl border p-3 text-right text-sm font-medium text-indigo-700 hover:border-indigo-300 hover:bg-indigo-50/40 dark:text-indigo-300 dark:hover:bg-indigo-950/20">عرض سجل الحوكمة التجريبي<ArrowLeft className="h-4 w-4" /></button></CardContent></Card></div>; }
function PriorityCard({ title, subtitle, tone, onClick }: { title: string; subtitle: string; tone: "critical" | "warning" | "info"; onClick: () => void }) { const color = tone === "critical" ? "bg-rose-50 text-rose-800 dark:bg-rose-950/20 dark:text-rose-200" : tone === "warning" ? "bg-amber-50 text-amber-800 dark:bg-amber-950/20 dark:text-amber-200" : "bg-sky-50 text-sky-800 dark:bg-sky-950/20 dark:text-sky-200"; return <button type="button" onClick={onClick} className={`flex w-full items-center justify-between gap-3 rounded-xl border p-4 text-right transition hover:border-indigo-300 ${color}`}><span><span className="block font-semibold">{title}</span><span className="mt-1 block text-xs opacity-80">{subtitle}</span></span><ArrowLeft className="h-4 w-4" /></button>; }
function DemoEmergency() { return <ListCard title="الطوارئ والفرز الاصطناعي" description="الأولوية والسبب والفاعل والوقت معروضة للشرح؛ لا يوجد Triage أو Break-Glass حقيقي.">{DEMO_EMERGENCY.map((item) => <QueueRow key={item.patient} label={`${item.priority} · ${item.patient}`} value={`${item.area} · ${item.status}`} tone={item.priority === "P1" ? "critical" : item.priority === "P2" ? "warning" : "info"} />)}</ListCard>; }
function DemoAdmissions() { return <ListCard title="الإدخال والإقامة الاصطناعية" description="Admission مستقل عن Bed؛ لا قبول أو تخصيص أو نقل حقيقي.">{DEMO_ADMISSIONS.map((item) => <div key={item.id} className="flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">{item.patient} · {item.route}</p><p className="mt-1 text-xs text-muted-foreground">{item.unit} · {item.status}</p></div><div className="flex gap-2"><Badge variant={item.priority === "عاجل" ? "destructive" : "outline"}>{item.priority}</Badge><Badge variant={item.status === "خرج" ? "success" : "outline"}>{item.status}</Badge></div></div>)}</ListCard>; }
function DemoBeds() { return <ListCard title="مركز الأسرة الاصطناعي" description="التخصيص والنقل وحالة العزل للعرض فقط؛ لا يظهر رقم مواطن أو موقع حقيقي."><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{DEMO_BEDS.map((bed) => <div key={bed.label} className="rounded-xl border p-4"><div className="flex items-center justify-between gap-2"><p className="font-semibold">{bed.label}</p><Badge variant={bed.status === "متاح" ? "success" : bed.status === "مشغول" ? "destructive" : "outline"}>{bed.status}</Badge></div><p className="mt-2 text-xs text-muted-foreground">{bed.ward}</p>{bed.patient && <p className="mt-2 text-xs text-muted-foreground">{bed.patient}</p>}</div>)}</div></ListCard>; }
function DemoPatients() { return <ListCard title="مرضى المستشفى الاصطناعيون" description="الوصول مرتبط بسياق الرعاية؛ لا بحث فضولي ولا Patient Merge."><QueueRow label="مريض اصطناعي 01" value="الباطنية · إقامة" tone="info" /><QueueRow label="مريض اصطناعي 02" value="ICU · مسؤول سريري محدد" tone="warning" /><QueueRow label="مريض اصطناعي 03" value="الجراحة · بانتظار القبول" tone="info" /></ListCard>; }
function DemoOrders() { return <ListCard title="CPOE والأوامر الاصطناعية" description="Order لا يساوي Performed؛ كل حالة تحتاج سيراً خادمياً."><QueueRow label="دواء" value="Active · تحقق الصيدلية مطلوب" tone="info" /><QueueRow label="مختبر" value="In Progress · نتيجة غير متاحة" tone="warning" /><QueueRow label="أشعة" value="Completed · التقرير محجوب" tone="success" /><QueueRow label="تمريض" value="Held · يحتاج مراجعة" tone="critical" /></ListCard>; }
function DemoCareTeam() { return <ListCard title="فريق الرعاية والتسليم الاصطناعي" description="كل عضو يحمل هويته ودوره؛ الإنابة مؤقتة ومحددة النطاق وليست مشاركة كلمة مرور."><QueueRow label="Attending" value="طبيب اصطناعي · مسؤول سريري" tone="info" /><QueueRow label="Nurse" value="ممرض اصطناعي · جناح A" tone="info" /><QueueRow label="Handover" value="مشاكل نشطة ومخاطر ومهام موثقة" tone="warning" /></ListCard>; }
function DemoOperations() { return <ListCard title="العمليات والعناية المركزة الاصطناعية" description="Surgical وICU وBlood Bank مجالات مستقلة؛ لا تنفيذ أو إعطاء أو نقل دم."><QueueRow label="OR-02" value="عملية مجدولة · موافقة مطلوبة" tone="info" /><QueueRow label="ICU" value="إشغال 90% · اتجاهات زمنية اصطناعية" tone="warning" /><QueueRow label="Blood Bank" value="Crossmatch محجوب · لا إصدار" tone="critical" /></ListCard>; }
function DemoDischarge() { return <ListCard title="الخروج والمتابعة الاصطناعية" description="Medication reconciliation وملخص الخروج للشرح فقط؛ لا إغلاق إقامة حقيقي."><QueueRow label="Medication reconciliation" value="منزلي + مستشفى + جديد + متوقف" tone="info" /><QueueRow label="Discharge summary" value="مسودة غير قابلة للإصدار" tone="warning" /><QueueRow label="Follow-up" value="موعد اصطناعي بعد 14 يوماً" tone="info" /></ListCard>; }
function DemoAudit() { return <ListCard title="سجل التدقيق الاصطناعي" description="سجل للعرض يبين نوع الحدث دون بيانات تعريف حساسة أو وصول حي."><QueueRow label="Bed Changed" value="فاعل اصطناعي · وقت اصطناعي · سبب مسجل" tone="info" /><QueueRow label="Break-Glass" value="سبب مطلوب · وصول محدود · مراجعة لاحقة" tone="critical" /><QueueRow label="Discharge" value="ملخص وخطة متابعة · غير نهائي" tone="warning" /></ListCard>; }
function LiveOverview({ contextReady, loading, error, patients, orders, onTab }: { contextReady: boolean; loading: boolean; error: unknown; patients?: ClinicalPatientRead[]; orders?: ClinicalOrderRead[]; onTab: (tab: HospitalTab) => void }) { return <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(300px,0.8fr)]"><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Building2 className="h-5 w-5 text-indigo-600" />ملخص المستشفى الحي</CardTitle><p className="mt-1 text-xs text-muted-foreground">قراءة محدودة من canonical clinical gateway بعد تفعيل السياق؛ لا إدخال أو سرير أو أمر كتابة.</p></CardHeader><CardContent>{!contextReady ? <GatedPanel title="فعّل سياق المستشفى أولاً" description="لا يتم تحميل المرضى والطلبات قبل workspace خادمي صالح." /> : loading ? <LoadingMessage text="جارٍ تحميل القراءة السريرية…" /> : error ? <GatedPanel title="أوقفنا القراءة السريرية" description="فشل عقد واحد؛ لم نستخدم Demo أو fallback legacy." /> : <div className="grid gap-3 sm:grid-cols-2"><InfoBox label="مرضى ضمن النطاق" value={String(patients?.length ?? 0)} /><InfoBox label="أوامر ضمن النطاق" value={String(orders?.length ?? 0)} /></div>}</CardContent></Card><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><LockKeyhole className="h-5 w-5 text-amber-600" />عمليات تحتاج عقوداً مستقلة</CardTitle></CardHeader><CardContent className="space-y-3"><GatedLine label="الطوارئ والفرز وBreak-Glass" onClick={() => onTab("emergency")} /><GatedLine label="الإدخال والأسرة والنقل" onClick={() => onTab("admissions")} /><GatedLine label="الخروج والتدقيق" onClick={() => onTab("discharge")} /></CardContent></Card></div>; }
function LivePatients({ contextReady, loading, error, patients }: { contextReady: boolean; loading: boolean; error: unknown; patients?: ClinicalPatientRead[] }) { return <ListCard title="المرضى ضمن نطاق المستشفى" description="تأتي القراءة من canonical clinical gateway وتُرفض الاستجابة إذا احتوت حقولاً حساسة غير مسموحة.">{!contextReady ? <GatedPanel title="فعّل سياق المستشفى أولاً" description="Patient Access يتطلب Identity + Role + Organization + Care Context + Purpose." /> : loading ? <LoadingMessage text="جارٍ تحميل المرضى…" /> : error ? <GatedPanel title="تعذر قراءة المرضى" description="لم يتم استخدام Demo كبديل." /> : patients?.length ? patients.map((patient) => <div key={patient.id} className="flex items-center gap-3 rounded-xl border p-4"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300"><Users className="h-5 w-5" /></span><div><p className="font-semibold">{patient.display_name}</p><p className="mt-1 text-xs text-muted-foreground">ضمن سياق الرعاية · لا يعرض الهاتف أو الرقم الوطني</p></div></div>) : <EmptyMessage text="لا يوجد مريض ضمن السياق الحالي." />}</ListCard>; }
function LiveOrders({ contextReady, loading, error, orders }: { contextReady: boolean; loading: boolean; error: unknown; orders?: ClinicalOrderRead[] }) { return <ListCard title="الأوامر ضمن نطاق المستشفى" description="قراءة فقط؛ لا تنفيذ أو إعطاء دواء أو إدخال نتيجة أو تغيير حالة من هذه الصفحة.">{!contextReady ? <GatedPanel title="فعّل سياق المستشفى أولاً" description="Order Access يتطلب Clinical Context وAuthorization." /> : loading ? <LoadingMessage text="جارٍ تحميل الأوامر…" /> : error ? <GatedPanel title="تعذر قراءة الأوامر" description="لم يتم استخدام Demo كبديل." /> : orders?.length ? orders.map((order) => <div key={order.id} className="flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">{order.patient_display_name ?? "مريض ضمن النطاق"}</p><p className="mt-1 text-xs text-muted-foreground">{order.test_count} عناصر · {order.practitioner_display_name ?? "ممارس ضمن السياق"}</p></div><Badge variant="outline">{order.status}</Badge></div>) : <EmptyMessage text="لا يوجد أمر ضمن السياق الحالي." />}</ListCard>; }
function WorkspaceCard({ workspace, selected, switching, onSelect }: { workspace: WorkspaceSummary; selected: boolean; switching: boolean; onSelect: () => void }) { const active = isActiveWorkspace(workspace); return <div className={`rounded-xl border p-4 transition ${selected ? "border-indigo-400 bg-indigo-50/60 dark:border-indigo-700 dark:bg-indigo-950/20" : "border-slate-200/80 dark:border-white/10"}`}><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><p className="text-sm font-bold">{workspace.name_ar ?? workspace.name}</p><p className="mt-1 text-xs text-muted-foreground">{workspace.facility_id ?? "منشأة غير معروضة"} · {workspace.department_id ?? "قسم غير معروض"}</p></div><div className="flex items-center gap-2"><Badge variant={active ? "success" : "outline"}>{workspace.status}</Badge><Button type="button" size="sm" variant={selected ? "secondary" : "outline"} disabled={!active || selected || switching} onClick={onSelect}>{switching ? "جارٍ التفعيل…" : selected ? "السياق الحالي" : "تفعيل سياق المستشفى"}</Button></div></div></div>; }
function ListCard({ title, description, children }: { title: string; description: string; children: ReactNode }) { return <Card><CardHeader><CardTitle>{title}</CardTitle><p className="mt-1 text-xs text-muted-foreground">{description}</p></CardHeader><CardContent className="space-y-3">{children}</CardContent></Card>; }
function QueueRow({ label, value, tone }: { label: string; value: string; tone: "critical" | "warning" | "success" | "info" | "muted" }) { const classes = { critical: "border-red-200 bg-red-50/70 dark:border-red-900/50 dark:bg-red-950/20", warning: "border-amber-200 bg-amber-50/70 dark:border-amber-900/50 dark:bg-amber-950/20", success: "border-emerald-200 bg-emerald-50/70 dark:border-emerald-900/50 dark:bg-emerald-950/20", info: "border-sky-200 bg-sky-50/70 dark:border-sky-900/50 dark:bg-sky-950/20", muted: "border-slate-200 bg-slate-50/70 dark:border-white/10 dark:bg-white/5" }; return <div className={`flex items-center justify-between gap-3 rounded-xl border p-4 ${classes[tone]}`}><span className="text-sm font-semibold">{label}</span><span className="text-sm text-muted-foreground">{value}</span></div>; }
function GatedPanel({ title, description }: { title: string; description: string }) { return <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-5 text-sm leading-7 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200"><LockKeyhole className="ml-2 inline h-4 w-4" /><strong>{title}</strong><p className="mt-2 text-xs leading-6 opacity-80">{description}</p></div>; }
function GatedLine({ label, onClick }: { label: string; onClick: () => void }) { return <button type="button" onClick={onClick} className="flex w-full items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50/60 p-3 text-right text-sm text-amber-950 transition hover:border-amber-300 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200"><span>{label}</span><LockKeyhole className="h-4 w-4" /></button>; }
function DemoBoundary() { return <Boundary><p><strong>حدود Demo:</strong> كل المستشفى اصطناعي للعرض. لا تسجيل مريض أو قبول أو تخصيص سرير أو نقل أو أمر أو إعطاء دواء أو نقل دم أو عملية أو خروج أو تدقيق حي.</p></Boundary>; }
function LiveBoundary() { return <Boundary><p><strong>حدود Live الحالية:</strong> القراءة تقتصر على المرضى والأوامر بعد تفعيل سياق المنشأة. الطوارئ والإدخال والأسرة والتمريض والعمليات والعناية والدم والخروج والتدقيق تبقى محجوبة حتى عقودها.</p></Boundary>; }
function Boundary({ children }: { children: ReactNode }) { return <Card className="border-indigo-200 bg-indigo-50/60 dark:border-indigo-900/50 dark:bg-indigo-950/20"><CardContent className="flex items-start gap-3 p-5 text-sm leading-7"><Info className="mt-1 h-5 w-5 shrink-0 text-indigo-700 dark:text-indigo-400" />{children}</CardContent></Card>; }
function InfoBox({ label, value }: { label: string; value: string }) { return <div className="rounded-xl border bg-muted/30 p-4"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 text-sm font-semibold leading-6">{value}</p></div>; }
function LoadingMessage({ text }: { text: string }) { return <div className="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">{text}</div>; }
function EmptyMessage({ text }: { text: string }) { return <div className="rounded-xl border border-dashed p-8 text-center text-sm text-muted-foreground">{text}</div>; }

export { DemoHospitalWorkspace };
