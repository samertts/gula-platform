import { useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  CalendarClock,
  CheckCircle2,
  ClipboardList,
  Clock3,
  Database,
  FileCheck2,
  History,
  Image,
  Info,
  LockKeyhole,
  ScanLine,
  ShieldCheck,
  Stethoscope,
  UserRoundCheck,
  type LucideIcon,
} from "lucide-react";
import { apiClient, type WorkspaceSummary } from "@/api/client";
import {
  radiologyApi,
  type RadiologyAppointmentRecord,
  type RadiologyExamRecord,
  type RadiologyOrderRecord,
} from "@/api/endpoints";
import { useAuth } from "@/contexts/AuthContext";
import { PageHeader } from "@/components/shared/PageComponents";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

 type RadiologyTab = "overview" | "orders" | "appointments" | "technologist" | "radiologist" | "studies" | "reports" | "critical" | "viewer";
type StudyStatus = "مجدول" | "وصل" | "قيد التنفيذ" | "الصور متاحة" | "قيد القراءة" | "متحقق" | "محرر" | "مؤرشف" | "غير مكتمل";

type DemoStudy = {
  id: string;
  accession: string;
  patient: string;
  modality: string;
  bodyPart: string;
  priority: "روتيني" | "عاجل" | "STAT";
  status: StudyStatus;
  reportStatus: "مسودة" | "مبدئي" | "متحقق" | "محرر";
  appointment: string;
  imageCount: number;
};

type DemoOrder = {
  id: string;
  modality: string;
  procedure: string;
  patient: string;
  priority: "روتيني" | "عاجل" | "STAT";
  status: string;
  indication: string;
};

const DEMO_STUDIES: DemoStudy[] = [
  { id: "study-demo-1", accession: "ACC-260827-014", patient: "سارة عبد الرحمن", modality: "CT", bodyPart: "صدر", priority: "عاجل", status: "الصور متاحة", reportStatus: "مسودة", appointment: "08:30", imageCount: 184 },
  { id: "study-demo-2", accession: "ACC-260827-015", patient: "حسن نوري", modality: "MRI", bodyPart: "دماغ", priority: "STAT", status: "قيد القراءة", reportStatus: "مبدئي", appointment: "09:10", imageCount: 426 },
  { id: "study-demo-3", accession: "ACC-260827-016", patient: "مريم فاضل", modality: "X-Ray", bodyPart: "صدر", priority: "روتيني", status: "متحقق", reportStatus: "متحقق", appointment: "09:25", imageCount: 2 },
  { id: "study-demo-4", accession: "ACC-260827-017", patient: "علي كريم حسن", modality: "Ultrasound", bodyPart: "بطن", priority: "روتيني", status: "غير مكتمل", reportStatus: "مسودة", appointment: "10:05", imageCount: 36 },
];

const DEMO_ORDERS: DemoOrder[] = [
  { id: "IMG-ORD-1001", modality: "CT", procedure: "CT Chest", patient: "سارة عبد الرحمن", priority: "عاجل", status: "Scheduled", indication: "ضيق نفس حاد" },
  { id: "IMG-ORD-1002", modality: "MRI", procedure: "MRI Brain", patient: "حسن نوري", priority: "STAT", status: "In Progress", indication: "تغير وعي مفاجئ" },
  { id: "IMG-ORD-1003", modality: "X-Ray", procedure: "Chest X-Ray", patient: "مريم فاضل", priority: "روتيني", status: "Completed", indication: "متابعة علاجية" },
];

const DEMO_REPORTS = [
  { accession: "ACC-260827-015", modality: "MRI", title: "MRI Brain", status: "مبدئي", finding: "تقرير اصطناعي يحتاج مراجعة اختصاصي الأشعة قبل التحرير." },
  { accession: "ACC-260827-016", modality: "X-Ray", title: "Chest X-Ray", status: "متحقق", finding: "تقرير اصطناعي متحقق ضمن سيناريو العرض." },
];

const TABS: Array<{ id: RadiologyTab; label: string; icon: LucideIcon }> = [
  { id: "overview", label: "نظرة الأشعة", icon: ScanLine },
  { id: "orders", label: "طلبات التصوير", icon: ClipboardList },
  { id: "appointments", label: "المواعيد والوصول", icon: CalendarClock },
  { id: "technologist", label: "قائمة الفني", icon: Activity },
  { id: "radiologist", label: "قائمة الاختصاصي", icon: Stethoscope },
  { id: "studies", label: "الدراسات", icon: Image },
  { id: "reports", label: "التقارير", icon: FileCheck2 },
  { id: "critical", label: "الاكتشافات الحرجة", icon: AlertTriangle },
  { id: "viewer", label: "عارض DICOM", icon: Image },
];

function isActiveWorkspace(workspace: WorkspaceSummary) {
  return ["active", "verified", "approved"].includes(workspace.status.toLowerCase());
}

export default function RadiologyOperationsWorkspacePage() {
  const { demoMode } = useAuth();
  return demoMode ? <RadiologyDemoWorkspace /> : <LiveRadiologyWorkspace />;
}

function RadiologyDemoWorkspace() {
  const [activeTab, setActiveTab] = useState<RadiologyTab>("overview");
  return <RadiologyShell demoMode activeTab={activeTab} onTab={setActiveTab} metrics={[
    ["دراسات اليوم", "146", ScanLine],
    ["بانتظار القراءة", "17", Clock3],
    ["عاجل / STAT", "6", AlertTriangle],
    ["تقارير تحتاج اعتماداً", "11", FileCheck2],
  ]}>
    {activeTab === "overview" && <DemoOverview onTab={setActiveTab} />}
    {activeTab === "orders" && <DemoOrders />}
    {activeTab === "appointments" && <DemoAppointments />}
    {activeTab === "technologist" && <DemoWorklist title="قائمة عمل فني الأشعة" studies={DEMO_STUDIES.filter((study) => study.status === "مجدول" || study.status === "وصل" || study.status === "قيد التنفيذ" || study.status === "غير مكتمل")} />}
    {activeTab === "radiologist" && <DemoWorklist title="قائمة عمل اختصاصي الأشعة" studies={DEMO_STUDIES.filter((study) => study.status === "الصور متاحة" || study.status === "قيد القراءة")} />}
    {activeTab === "studies" && <DemoStudies />}
    {activeTab === "reports" && <DemoReports />}
    {activeTab === "critical" && <GatedPanel title="مسار الاكتشافات الحرجة محاكاة فقط" description="Demo يشرح الإشعار والتأكيد والتصعيد، لكنه لا يرسل تنبيهاً ولا يسجل acknowledgment حقيقياً." />}
    {activeTab === "viewer" && <GatedPanel title="عارض DICOM غير متصل في Demo" description="لا توجد صور أو روابط PACS حقيقية. عارض الصور يحتاج retrieval مفوضاً ورابطاً قصير العمر وسجلاً للتنزيل والطباعة." />}
    <DemoBoundary />
  </RadiologyShell>;
}

function LiveRadiologyWorkspace() {
  const [activeTab, setActiveTab] = useState<RadiologyTab>("overview");
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string | null>(null);
  const [switchingWorkspaceId, setSwitchingWorkspaceId] = useState<string | null>(null);
  const [switchError, setSwitchError] = useState("");
  const workspacesQuery = useQuery({ queryKey: ["radiology-workspaces", "me"], queryFn: () => apiClient.listWorkspaces(), retry: false, staleTime: 30_000 });
  const radiologyWorkspaces = (workspacesQuery.data?.workspaces ?? []).filter((workspace) => !workspace.is_personal && Boolean(workspace.facility_id));
  const selectedWorkspace = radiologyWorkspaces.find((workspace) => workspace.id === selectedWorkspaceId);
  const contextReady = Boolean(selectedWorkspaceId && selectedWorkspace && isActiveWorkspace(selectedWorkspace));
  const ordersQuery = useQuery({ queryKey: ["radiology-orders", selectedWorkspaceId], queryFn: () => radiologyApi.orders({ limit: 50 }), enabled: contextReady, retry: false, staleTime: 15_000 });
  const appointmentsQuery = useQuery({ queryKey: ["radiology-appointments", selectedWorkspaceId], queryFn: () => radiologyApi.appointments({ limit: 50 }), enabled: contextReady, retry: false, staleTime: 15_000 });
  const examsQuery = useQuery({ queryKey: ["radiology-exams", selectedWorkspaceId], queryFn: () => radiologyApi.exams({ limit: 50 }), enabled: contextReady, retry: false, staleTime: 15_000 });
  const radiologistQuery = useQuery({ queryKey: ["radiology-radiologist-worklist", selectedWorkspaceId], queryFn: () => radiologyApi.radiologistWorklist(), enabled: contextReady, retry: false, staleTime: 15_000 });
  const technologistQuery = useQuery({ queryKey: ["radiology-technologist-worklist", selectedWorkspaceId], queryFn: () => radiologyApi.technologistWorklist(), enabled: contextReady, retry: false, staleTime: 15_000 });
  const activateWorkspace = async (workspace: WorkspaceSummary) => {
    if (!isActiveWorkspace(workspace) || workspace.id === selectedWorkspaceId) return;
    setSwitchingWorkspaceId(workspace.id);
    setSwitchError("");
    try {
      await apiClient.switchWorkspace(workspace.id);
      setSelectedWorkspaceId(workspace.id);
    } catch (error) {
      setSwitchError(error instanceof Error ? error.message : "تعذر تفعيل سياق الأشعة.");
    } finally {
      setSwitchingWorkspaceId(null);
    }
  };
  const liveError = ordersQuery.error || appointmentsQuery.error || examsQuery.error || radiologistQuery.error || technologistQuery.error;
  const liveLoading = ordersQuery.isLoading || appointmentsQuery.isLoading || examsQuery.isLoading || radiologistQuery.isLoading || technologistQuery.isLoading;

  return <RadiologyShell demoMode={false} activeTab={activeTab} onTab={setActiveTab} metrics={liveMetrics(ordersQuery.data?.total, examsQuery.data?.total, radiologistQuery.data?.total, technologistQuery.data?.total)}>
    <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70"><CardHeader><CardTitle className="flex items-center gap-2 text-base"><ShieldCheck className="h-5 w-5 text-indigo-600" />سياق الأشعة المؤسسي</CardTitle><p className="mt-1 text-xs text-muted-foreground">يجب أن يثبت الخادم المنشأة والعضوية والقدرة التشغيلية قبل قراءة أي قائمة عمل.</p></CardHeader><CardContent className="space-y-3">{workspacesQuery.isLoading ? <div className="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">جارٍ تحميل مساحات الأشعة…</div> : radiologyWorkspaces.length === 0 ? <GatedPanel title="لا توجد مساحة أشعة مؤكدة" description="تحتاج القراءة الحية إلى Professional Verification وMembership وFacility Context يعاد من الخادم." /> : radiologyWorkspaces.map((workspace) => <WorkspaceCard key={workspace.id} workspace={workspace} selected={workspace.id === selectedWorkspaceId} switching={switchingWorkspaceId === workspace.id} onSelect={() => void activateWorkspace(workspace)} />)}{switchError && <p className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/20 dark:text-rose-200" role="alert">{switchError}</p>}{workspacesQuery.error && <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200" role="alert">تعذر قراءة مساحات الأشعة من الخادم.</p>}</CardContent></Card>
    {activeTab === "overview" && <LiveOverview contextReady={contextReady} loading={liveLoading} error={liveError} orders={ordersQuery.data?.items} exams={examsQuery.data?.items} appointments={appointmentsQuery.data?.items} onTab={setActiveTab} />}
    {activeTab === "orders" && <LiveOrders contextReady={contextReady} loading={ordersQuery.isLoading} error={ordersQuery.error} orders={ordersQuery.data?.items} />}
    {activeTab === "appointments" && <LiveAppointments contextReady={contextReady} loading={appointmentsQuery.isLoading} error={appointmentsQuery.error} appointments={appointmentsQuery.data?.items} />}
    {activeTab === "technologist" && <LiveExams title="قائمة عمل فني الأشعة الحية" contextReady={contextReady} loading={technologistQuery.isLoading} error={technologistQuery.error} exams={technologistQuery.data?.items} />}
    {activeTab === "radiologist" && <LiveExams title="قائمة عمل اختصاصي الأشعة الحية" contextReady={contextReady} loading={radiologistQuery.isLoading} error={radiologistQuery.error} exams={radiologistQuery.data?.items} />}
    {activeTab === "studies" && <LiveExams title="الدراسات الحية" contextReady={contextReady} loading={examsQuery.isLoading} error={examsQuery.error} exams={examsQuery.data?.items} />}
    {activeTab === "reports" && <GatedPanel title="التقارير غير موصولة في هذه الموجة" description="يلزم عقد report lifecycle يفرض draft/preliminary/verified/signed/released وIf-Match وIdempotency-Key وProfessional Identity قبل العرض أو التعديل." />}
    {activeTab === "critical" && <GatedPanel title="الاكتشافات الحرجة غير موصولة" description="يلزم عقد notification/acknowledgment/escalation خادمي قبل إظهار حالة حرجة أو إرسال إشعار للفريق السريري." />}
    {activeTab === "viewer" && <GatedPanel title="عارض DICOM غير موصول" description="لا تستخدم الواجهة روابط صور عامة. يلزم authorized retrieval ورابط قصير العمر وسجل view/download/print وتحقق من PACS/VNA." />}
    {liveError && <div className="rounded-2xl border border-amber-200 bg-amber-50/70 p-5 text-sm leading-7 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200" role="status"><LockKeyhole className="ml-2 inline h-4 w-4" />أوقفنا القراءة الحية عند فشل عقد واحد؛ لم يتم استخدام Demo أو fallback legacy.</div>}
    <LiveBoundary />
  </RadiologyShell>;
}

function RadiologyShell({ demoMode, activeTab, onTab, metrics, children }: { demoMode: boolean; activeTab: RadiologyTab; onTab: (tab: RadiologyTab) => void; metrics: Array<[string, string, LucideIcon]>; children: ReactNode }) { return <div className="mx-auto max-w-7xl space-y-6" dir="rtl"><PageHeader title="الأشعة والتصوير الطبي" description="مساحة GULA للطلبات والمواعيد والدراسات وقوائم العمل، مع فصل metadata عن الصور وحجب التكاملات الحساسة حتى تكتمل عقودها." /><Card className="overflow-hidden border-indigo-200 bg-gradient-to-l from-indigo-50 via-white to-cyan-50 dark:border-indigo-900/50 dark:from-indigo-950/30 dark:via-background dark:to-cyan-950/30"><CardContent className="p-6"><div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between"><div className="max-w-3xl space-y-3"><div className="flex items-center gap-2 text-indigo-700 dark:text-indigo-300"><ScanLine className="h-5 w-5" /><span className="text-sm font-semibold">Radiology & Medical Imaging Operations</span></div><h2 className="text-2xl font-bold tracking-tight">من الطلب إلى تقرير قابل للتدقيق</h2><p className="text-sm leading-7 text-muted-foreground">ربط آمن بين الطلب والموعد والدراسة والتقرير، مع عدم وضع صور DICOM داخل قاعدة GULA أو كشفها عبر روابط عامة.</p><div className="flex flex-wrap gap-2"><Badge variant={demoMode ? "success" : "outline"}><ShieldCheck className="ml-1 h-3.5 w-3.5" />{demoMode ? "عرض اصطناعي معزول" : "سياق خادمي مطلوب"}</Badge><Badge variant="outline"><Database className="ml-1 h-3.5 w-3.5" />DICOM/PACS boundary</Badge><Badge variant="outline"><History className="ml-1 h-3.5 w-3.5" />Audit boundary</Badge></div></div>{demoMode && <div className="grid min-w-[290px] grid-cols-2 gap-3"><Metric label="دراسات مكتملة" value="129" icon={CheckCircle2} /><Metric label="عاجل" value="4" icon={AlertTriangle} /><Metric label="حرج" value="2" icon={AlertTriangle} /><Metric label="أجهزة متصلة" value="7" icon={Activity} /></div>}</div></CardContent></Card><MetricGrid metrics={metrics} /><RadiologyTabs activeTab={activeTab} onChange={onTab} />{children}</div>; }

function RadiologyTabs({ activeTab, onChange }: { activeTab: RadiologyTab; onChange: (tab: RadiologyTab) => void }) { return <Card><CardContent className="p-0"><div className="flex flex-wrap border-b">{TABS.map(({ id, label, icon: Icon }) => <button key={id} type="button" onClick={() => onChange(id)} aria-selected={activeTab === id} className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 ${activeTab === id ? "border-b-2 border-indigo-600 text-indigo-700 dark:text-indigo-300" : "text-muted-foreground hover:text-foreground"}`}><Icon className="h-4 w-4" />{label}</button>)}</div></CardContent></Card>; }
function MetricGrid({ metrics }: { metrics: Array<[string, string, LucideIcon]> }) { return <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="مؤشرات الأشعة">{metrics.map(([label, value, Icon]) => <Card key={label} className="overflow-hidden rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70"><CardContent className="relative p-5"><div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-l from-indigo-500 to-cyan-400" /><div className="flex items-start justify-between gap-3"><span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200"><Icon className="h-5 w-5" /></span><Badge variant="outline">{value === "—" ? "محجوب" : "حالة"}</Badge></div><p className="mt-5 text-sm text-muted-foreground">{label}</p><p className="mt-1 text-3xl font-bold tracking-tight text-[#0F172A] dark:text-white">{value}</p></CardContent></Card>)}</section>; }
function Metric({ label, value, icon: Icon }: { label: string; value: string; icon: LucideIcon }) { return <div className="rounded-xl bg-background/80 p-4 shadow-sm"><div className="flex items-center justify-between gap-2"><p className="text-xs text-muted-foreground">{label}</p><Icon className="h-4 w-4 text-indigo-600" /></div><p className="mt-1 text-2xl font-bold">{value}</p></div>; }

function DemoOverview({ onTab }: { onTab: (tab: RadiologyTab) => void }) { const steps: Array<{ label: string; detail: string; tab: RadiologyTab; icon: LucideIcon }> = [{ label: "الطلب والتحقق", detail: "Procedure + body site + priority + facility capability", tab: "orders", icon: ClipboardList }, { label: "الوصول والسلامة", detail: "Check-in وIdentity وMRI/contrast checklist", tab: "appointments", icon: UserRoundCheck }, { label: "الدراسة والصور", detail: "Study + Series + DICOM/PACS boundary", tab: "studies", icon: Image }, { label: "التقرير والتحرير", detail: "Draft → Verified → Signed → Released", tab: "reports", icon: FileCheck2 }]; return <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(300px,0.8fr)]"><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><ScanLine className="h-5 w-5 text-indigo-600" />رحلة الأشعة التجريبية</CardTitle></CardHeader><CardContent className="space-y-3">{steps.map((step, index) => { const Icon = step.icon; return <button key={step.label} type="button" onClick={() => onTab(step.tab)} className="flex w-full items-center gap-3 rounded-xl border p-4 text-right transition hover:border-indigo-300 hover:bg-indigo-50/40 dark:hover:bg-indigo-950/20"><span className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300">{index + 1}</span><span className="flex-1"><span className="block font-semibold">{step.label}</span><span className="mt-1 block text-xs text-muted-foreground">{step.detail}</span></span><Icon className="h-4 w-4 text-indigo-600" /><ArrowLeft className="h-4 w-4 text-muted-foreground" /></button>; })}</CardContent></Card><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><AlertTriangle className="h-5 w-5 text-amber-600" />حواجز السلامة</CardTitle></CardHeader><CardContent className="space-y-3"><AlertRow title="MRI Safety Screening" detail="قائمة تحقق اصطناعية؛ ليست clearance حقيقية." tone="warning" /><AlertRow title="Critical Finding" detail="الإشعار والتأكيد والتصعيد محجوبة في Demo." tone="critical" /><AlertRow title="DICOM/PACS" detail="لا توجد صورة أو URL عام أو تنزيل." tone="warning" /><LinkLike label="عرض التقارير الاصطناعية" onClick={() => onTab("reports")} /></CardContent></Card></div>; }
function DemoOrders() { return <Card><CardHeader><CardTitle>طلبات التصوير الاصطناعية</CardTitle><p className="mt-1 text-xs text-muted-foreground">لا ينشئ Demo طلباً ولا يغير حالته.</p></CardHeader><CardContent className="space-y-3">{DEMO_ORDERS.map((order) => <div key={order.id} className="rounded-xl border p-4"><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">{order.procedure} · {order.patient}</p><p className="mt-1 text-xs text-muted-foreground">{order.id} · {order.modality} · {order.indication}</p></div><div className="flex items-center gap-2"><Badge variant={order.priority === "STAT" ? "destructive" : order.priority === "عاجل" ? "warning" : "outline"}>{order.priority}</Badge><Badge variant="outline">{order.status}</Badge></div></div></div>)}</CardContent></Card>; }
function DemoAppointments() { return <Card><CardHeader><CardTitle>المواعيد والوصول الاصطناعي</CardTitle><p className="mt-1 text-xs text-muted-foreground">Check-in وIdentity Verification معروضان للشرح ولا ينفذان انتقالاً.</p></CardHeader><CardContent className="space-y-2">{DEMO_STUDIES.map((study) => <div key={study.id} className="flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">{study.appointment} · {study.modality} {study.bodyPart}</p><p className="mt-1 text-xs text-muted-foreground">{study.patient} · {study.accession}</p></div><div className="flex items-center gap-2"><Badge variant="outline">موعد اصطناعي</Badge><Badge variant="success">قائمة السلامة مطلوبة</Badge></div></div>)}</CardContent></Card>; }
function DemoWorklist({ title, studies }: { title: string; studies: DemoStudy[] }) { return <Card><CardHeader><CardTitle>{title}</CardTitle><p className="mt-1 text-xs text-muted-foreground">كل العناصر اصطناعية؛ لا توجد قراءة أو توزيع أو توقيع فعلي.</p></CardHeader><CardContent>{studies.length ? <div className="space-y-2">{studies.map((study) => <StudyRow key={study.id} study={study} />)}</div> : <EmptyMessage text="لا توجد دراسة ضمن السيناريو." />}</CardContent></Card>; }
function DemoStudies() { return <Card><CardHeader><CardTitle>الدراسات والصور الاصطناعية</CardTitle><p className="mt-1 text-xs text-muted-foreground">المعرفات والعدادات للعرض فقط، ولا تمثل DICOM أو PACS حقيقياً.</p></CardHeader><CardContent className="space-y-2">{DEMO_STUDIES.map((study) => <StudyRow key={study.id} study={study} showImages />)}</CardContent></Card>; }
function DemoReports() { return <Card><CardHeader><CardTitle>تقارير الأشعة الاصطناعية</CardTitle><p className="mt-1 text-xs text-muted-foreground">التقرير لا يتحول إلى Released ولا يوقعه AI أو المستخدم في Demo.</p></CardHeader><CardContent className="space-y-3">{DEMO_REPORTS.map((report) => <div key={report.accession} className="rounded-xl border p-4"><div className="flex items-center justify-between gap-3"><div><p className="font-semibold">{report.title}</p><p className="mt-1 text-xs text-muted-foreground">{report.accession} · {report.modality}</p></div><Badge variant={report.status === "متحقق" ? "success" : "warning"}>{report.status}</Badge></div><p className="mt-3 text-sm leading-6 text-muted-foreground">{report.finding}</p></div>)}</CardContent></Card>; }
function StudyRow({ study, showImages = false }: { study: DemoStudy; showImages?: boolean }) { return <div className="rounded-xl border p-4"><div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between"><div><p className="font-semibold">{study.accession} · {study.patient}</p><p className="mt-1 text-xs text-muted-foreground">{study.modality} · {study.bodyPart} · {study.imageCount} صورة اصطناعية · {study.appointment}</p></div><div className="flex flex-wrap items-center gap-2"><Badge variant={study.priority === "STAT" ? "destructive" : study.priority === "عاجل" ? "warning" : "outline"}>{study.priority}</Badge><Badge variant={study.status === "متحقق" ? "success" : study.status === "غير مكتمل" ? "destructive" : "outline"}>{study.status}</Badge>{showImages && <Badge variant="outline">عارض محجوب</Badge>}</div></div></div>; }

function LiveOverview({ contextReady, loading, error, orders, exams, appointments, onTab }: { contextReady: boolean; loading: boolean; error: unknown; orders?: RadiologyOrderRecord[]; exams?: RadiologyExamRecord[]; appointments?: RadiologyAppointmentRecord[]; onTab: (tab: RadiologyTab) => void }) { return <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(300px,0.8fr)]"><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Activity className="h-5 w-5 text-indigo-600" />ملخص الأشعة الحي</CardTitle><p className="mt-1 text-xs text-muted-foreground">قراءة metadata محدودة بعد تفعيل سياق الخادم؛ الصور والتقارير غير معروضة.</p></CardHeader><CardContent>{!contextReady ? <GatedPanel title="فعّل سياق الأشعة أولاً" description="لا يتم تحميل الطلبات والمواعيد والدراسات قبل workspace خادمي صالح." /> : loading ? <div className="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">جارٍ تحميل عقود الأشعة…</div> : error ? <GatedPanel title="قراءة الأشعة موقوفة بأمان" description="فشل عقد حي واحد؛ لم نستخدم Demo أو fallback legacy." /> : <div className="grid gap-3 sm:grid-cols-3"><ValueBox label="الطلبات" value={String(orders?.length ?? 0)} /><ValueBox label="المواعيد" value={String(appointments?.length ?? 0)} /><ValueBox label="الدراسات" value={String(exams?.length ?? 0)} /></div>}</CardContent></Card><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><LockKeyhole className="h-5 w-5 text-amber-600" />العقود التالية</CardTitle></CardHeader><CardContent className="space-y-3"><GatedLine label="Report lifecycle + e-signature" onClick={() => onTab("reports")} /><GatedLine label="DICOM/PACS authorized viewer" onClick={() => onTab("viewer")} /><GatedLine label="Critical finding notification" onClick={() => onTab("critical")} /></CardContent></Card></div>; }
function LiveOrders({ contextReady, loading, error, orders }: { contextReady: boolean; loading: boolean; error: unknown; orders?: RadiologyOrderRecord[] }) { return <Card><CardHeader><CardTitle>طلبات التصوير الحية</CardTitle><p className="mt-1 text-xs text-muted-foreground">البيانات ضمن نطاق الخادم؛ لا يظهر Patient ID الخام ولا توجد كتابة من هذه الصفحة.</p></CardHeader><CardContent>{!contextReady ? <GatedPanel title="فعّل سياق الأشعة أولاً" description="الطلب السريري لا يفتح خارج Facility Context." /> : loading ? <LoadingMessage /> : error ? <GatedPanel title="تعذر قراءة الطلبات" description="لم يتم استخدام بيانات Demo كبديل." /> : orders?.length ? <div className="space-y-2">{orders.map((order) => <div key={order.id} className="rounded-xl border p-4"><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">{order.modality ?? "تصوير"} · {order.body_part ?? "موضع غير معروض"}</p><p className="mt-1 text-xs text-muted-foreground">مريض ضمن نطاق المنشأة · {order.clinical_indication ?? "دلالة غير معروضة"}</p></div><div className="flex items-center gap-2"><Badge variant={order.priority?.toUpperCase() === "STAT" ? "destructive" : "warning"}>{order.priority ?? "غير معروض"}</Badge><Badge variant="outline">{order.status ?? "غير معروض"}</Badge></div></div></div>)}</div> : <EmptyMessage text="لا توجد طلبات ضمن السياق." />}</CardContent></Card>; }
function LiveAppointments({ contextReady, loading, error, appointments }: { contextReady: boolean; loading: boolean; error: unknown; appointments?: RadiologyAppointmentRecord[] }) { return <Card><CardHeader><CardTitle>المواعيد والوصول الحية</CardTitle><p className="mt-1 text-xs text-muted-foreground">لا يوجد check-in أو arrive أو تعديل موعد في هذه الموجة.</p></CardHeader><CardContent>{!contextReady ? <GatedPanel title="فعّل سياق الأشعة أولاً" description="المواعيد تتبع المنشأة والنطاق السريري." /> : loading ? <LoadingMessage /> : error ? <GatedPanel title="تعذر قراءة المواعيد" description="لم يتم استخدام بيانات Demo كبديل." /> : appointments?.length ? <div className="space-y-2">{appointments.map((appointment) => <div key={appointment.id} className="flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">{appointment.modality ?? "تصوير"} · {appointment.scheduled_date ?? "تاريخ غير معروض"}</p><p className="mt-1 text-xs text-muted-foreground">{appointment.scheduled_time ?? "وقت غير معروض"} · {appointment.room ?? "غرفة غير معروضة"}</p></div><Badge variant="outline">{appointment.status ?? "غير معروض"}</Badge></div>)}</div> : <EmptyMessage text="لا توجد مواعيد ضمن السياق." />}</CardContent></Card>; }
function LiveExams({ title, contextReady, loading, error, exams }: { title: string; contextReady: boolean; loading: boolean; error: unknown; exams?: RadiologyExamRecord[] }) { return <Card><CardHeader><CardTitle>{title}</CardTitle><p className="mt-1 text-xs text-muted-foreground">عرض metadata للدراسة فقط؛ الصور والتقارير والتوزيع والتوقيع محجوبة.</p></CardHeader><CardContent>{!contextReady ? <GatedPanel title="فعّل سياق الأشعة أولاً" description="قائمة العمل فرعية النطاق ولا تُقرأ من دون workspace صالح." /> : loading ? <LoadingMessage /> : error ? <GatedPanel title="تعذر قراءة قائمة العمل" description="لم يتم استخدام بيانات Demo كبديل." /> : exams?.length ? <div className="space-y-2">{exams.map((exam) => <div key={exam.id} className="rounded-xl border p-4"><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">{exam.accession_number ?? "Study ضمن النطاق"} · {exam.modality ?? "تصوير"}</p><p className="mt-1 text-xs text-muted-foreground">{exam.body_part ?? "موضع غير معروض"} · {exam.images_count ?? 0} صورة metadata · {exam.series_count ?? 0} Series</p></div><Badge variant={exam.status?.toLowerCase() === "completed" ? "success" : "outline"}>{exam.status ?? "غير معروض"}</Badge></div></div>)}</div> : <EmptyMessage text="لا توجد دراسات ضمن قائمة العمل." />}</CardContent></Card>; }

function liveMetrics(orders: number | undefined, exams: number | undefined, radiologist: number | undefined, technologist: number | undefined): Array<[string, string, LucideIcon]> { return [["طلبات التصوير", orders === undefined ? "—" : String(orders), ClipboardList], ["الدراسات", exams === undefined ? "—" : String(exams), Image], ["قائمة الاختصاصي", radiologist === undefined ? "—" : String(radiologist), Stethoscope], ["قائمة الفني", technologist === undefined ? "—" : String(technologist), Activity]]; }
function WorkspaceCard({ workspace, selected, switching, onSelect }: { workspace: WorkspaceSummary; selected: boolean; switching: boolean; onSelect: () => void }) { const active = isActiveWorkspace(workspace); return <div className={`rounded-xl border p-4 transition ${selected ? "border-indigo-400 bg-indigo-50/60 dark:border-indigo-700 dark:bg-indigo-950/20" : "border-slate-200/80 dark:border-white/10"}`}><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div className="flex items-start gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200"><ScanLine className="h-5 w-5" /></span><div><p className="text-sm font-bold">{workspace.name_ar ?? workspace.name}</p><p className="mt-1 text-xs text-muted-foreground">{workspace.facility_id ?? "منشأة غير معروضة"} · {workspace.department_id ?? "قسم غير معروض"}</p></div></div><div className="flex items-center gap-2"><Badge variant={active ? "success" : "outline"}>{workspace.status}</Badge><Button type="button" size="sm" variant={selected ? "secondary" : "outline"} disabled={!active || selected || switching} onClick={onSelect}>{switching ? "جارٍ التفعيل…" : selected ? "السياق الحالي" : "تفعيل سياق الأشعة"}</Button></div></div></div>; }
function GatedLine({ label, onClick }: { label: string; onClick: () => void }) { return <button type="button" onClick={onClick} className="flex w-full items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50/60 p-3 text-right text-sm text-amber-950 transition hover:border-amber-300 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200"><span>{label}</span><LockKeyhole className="h-4 w-4" /></button>; }
function GatedPanel({ title, description }: { title: string; description: string }) { return <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-5 text-sm leading-7 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200"><LockKeyhole className="ml-2 inline h-4 w-4" /><strong>{title}</strong><p className="mt-2 text-xs leading-6 opacity-80">{description}</p></div>; }
function DemoBoundary() { return <Card className="border-amber-200 bg-amber-50/60 dark:border-amber-900/50 dark:bg-amber-950/20"><CardContent className="flex items-start gap-3 p-5 text-sm leading-7"><Info className="mt-1 h-5 w-5 shrink-0 text-amber-700 dark:text-amber-400" /><p><strong>حدود Demo:</strong> الطلبات والمواعيد والدراسات والتقارير اصطناعية للعرض فقط. لا توجد صور DICOM أو روابط PACS أو توقيع أو إشعار حرج حقيقي.</p></CardContent></Card>; }
function LiveBoundary() { return <Card className="border-amber-200 bg-amber-50/60 dark:border-amber-900/50 dark:bg-amber-950/20"><CardContent className="flex items-start gap-3 p-5 text-sm leading-7"><Info className="mt-1 h-5 w-5 shrink-0 text-amber-700 dark:text-amber-400" /><p><strong>حدود Live الحالية:</strong> القراءة تقتصر على metadata للطلبات والمواعيد والدراسات وقوائم العمل بعد تفعيل السياق. لا إنشاء فحص أو تقرير أو توقيع أو تحميل صورة أو مشاركة أو critical notification.</p></CardContent></Card>; }
function AlertRow({ title, detail, tone }: { title: string; detail: string; tone: "critical" | "warning" }) { return <div className={`rounded-xl border p-3 ${tone === "critical" ? "border-red-200 bg-red-50/70 dark:border-red-900/50 dark:bg-red-950/20" : "border-amber-200 bg-amber-50/70 dark:border-amber-900/50 dark:bg-amber-950/20"}`}><div className="flex items-center gap-2"><AlertTriangle className={`h-4 w-4 ${tone === "critical" ? "text-red-600" : "text-amber-600"}`} /><p className="text-sm font-semibold">{title}</p></div><p className="mt-1 text-xs text-muted-foreground">{detail}</p></div>; }
function LinkLike({ label, onClick }: { label: string; onClick: () => void }) { return <button type="button" onClick={onClick} className="flex w-full items-center justify-between rounded-xl border p-3 text-right text-sm font-medium text-indigo-700 hover:border-indigo-300 hover:bg-indigo-50/40 dark:text-indigo-300 dark:hover:bg-indigo-950/20">{label}<ArrowLeft className="h-4 w-4" /></button>; }
function LoadingMessage() { return <div className="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">جارٍ تحميل البيانات…</div>; }
function ValueBox({ label, value }: { label: string; value: string }) { return <div className="rounded-lg bg-muted/50 p-3"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 font-semibold">{value}</p></div>; }
function EmptyMessage({ text }: { text: string }) { return <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">{text}</div>; }

export { RadiologyDemoWorkspace };
