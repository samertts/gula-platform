import { useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  CalendarClock,
  ClipboardList,
  Clock3,
  FileText,
  HeartPulse,
  Info,
  LockKeyhole,
  MessageCircle,
  ShieldCheck,
  Stethoscope,
  UserRound,
  Users,
  type LucideIcon,
} from "lucide-react";
import { apiClient, type WorkspaceSummary } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { PageHeader } from "@/components/shared/PageComponents";
import { workspaceScopedReads, type ClinicalOrderRead, type ClinicalPatientRead } from "@/api/workspaceScopedReads";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

type ClinicTab = "overview" | "appointments" | "queue" | "patients" | "encounter" | "orders" | "care-plan" | "inbox";
type DemoAppointmentStatus = "مؤكد" | "وصل" | "بانتظار الطبيب" | "مع الطبيب" | "مكتمل" | "ملغى" | "لم يحضر";

type DemoAppointment = {
  id: string;
  patient: string;
  service: string;
  time: string;
  type: "استشارة جديدة" | "متابعة" | "طب عن بعد";
  status: DemoAppointmentStatus;
  priority: "عادي" | "عاجل";
};

const DEMO_APPOINTMENTS: DemoAppointment[] = [
  { id: "appt-demo-1", patient: "سارة عبد الرحمن", service: "طب الأسرة", time: "08:30", type: "استشارة جديدة", status: "بانتظار الطبيب", priority: "عادي" },
  { id: "appt-demo-2", patient: "حسن نوري", service: "متابعة مزمنة", time: "09:00", type: "متابعة", status: "وصل", priority: "عاجل" },
  { id: "appt-demo-3", patient: "مريم فاضل", service: "استشارة عن بعد", time: "09:30", type: "طب عن بعد", status: "مؤكد", priority: "عادي" },
  { id: "appt-demo-4", patient: "علي كريم حسن", service: "طب الأسرة", time: "10:00", type: "متابعة", status: "مكتمل", priority: "عادي" },
];

const DEMO_ENCOUNTER = {
  patient: "حسن نوري",
  identity: "مواطن اصطناعي · هوية العرض مكتملة",
  complaint: "متابعة ضغط الدم خلال زيارة روتينية",
  history: "بيانات تاريخية اصطناعية مرتبطة بسياق الزيارة فقط.",
  vitals: "ضغط 138/86 · نبض 78 · SpO₂ 98%",
  alerts: "حساسية اصطناعية: لا توجد ضمن السيناريو",
};

const TABS: Array<{ id: ClinicTab; label: string; icon: LucideIcon }> = [
  { id: "overview", label: "نظرة العيادة", icon: Stethoscope },
  { id: "appointments", label: "المواعيد", icon: CalendarClock },
  { id: "queue", label: "الاستقبال والانتظار", icon: Clock3 },
  { id: "patients", label: "المرضى ضمن النطاق", icon: Users },
  { id: "encounter", label: "مساحة الزيارة", icon: FileText },
  { id: "orders", label: "الطلبات والنتائج", icon: ClipboardList },
  { id: "care-plan", label: "خطة الرعاية", icon: HeartPulse },
  { id: "inbox", label: "صندوق التنبيهات", icon: AlertTriangle },
];

function isActiveWorkspace(workspace: WorkspaceSummary) {
  return ["active", "verified", "approved"].includes(workspace.status.toLowerCase());
}

export default function ClinicOperationsWorkspacePage() {
  const { demoMode } = useAuth();
  return demoMode ? <DemoClinicWorkspace /> : <LiveClinicWorkspace />;
}

function DemoClinicWorkspace() {
  const [activeTab, setActiveTab] = useState<ClinicTab>("overview");
  return <ClinicShell demoMode activeTab={activeTab} onTab={setActiveTab} metrics={[["اليوم", "18", CalendarClock], ["بانتظار الطبيب", "3", Clock3], ["زيارات نشطة", "2", Activity], ["تنبيهات حرجة", "1", AlertTriangle]]}>
    {activeTab === "overview" && <DemoOverview onTab={setActiveTab} />}
    {activeTab === "appointments" && <DemoAppointments />}
    {activeTab === "queue" && <DemoQueue />}
    {activeTab === "patients" && <DemoPatients />}
    {activeTab === "encounter" && <DemoEncounter />}
    {activeTab === "orders" && <DemoOrders />}
    {activeTab === "care-plan" && <DemoCarePlan />}
    {activeTab === "inbox" && <DemoInbox />}
    <DemoBoundary />
  </ClinicShell>;
}

function LiveClinicWorkspace() {
  const [activeTab, setActiveTab] = useState<ClinicTab>("overview");
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string | null>(null);
  const [switchingWorkspaceId, setSwitchingWorkspaceId] = useState<string | null>(null);
  const [switchError, setSwitchError] = useState("");
  const workspacesQuery = useQuery({ queryKey: ["clinic-workspaces", "me"], queryFn: () => apiClient.listWorkspaces(), retry: false, staleTime: 30_000 });
  const clinicWorkspaces = (workspacesQuery.data?.workspaces ?? []).filter((workspace) => !workspace.is_personal && Boolean(workspace.facility_id));
  const selectedWorkspace = clinicWorkspaces.find((workspace) => workspace.id === selectedWorkspaceId);
  const contextReady = Boolean(selectedWorkspaceId && selectedWorkspace && isActiveWorkspace(selectedWorkspace));
  const patientsQuery = useQuery({ queryKey: ["clinic-patients", selectedWorkspaceId], queryFn: () => workspaceScopedReads.listPatients({ limit: 50 }), enabled: contextReady, retry: false, staleTime: 15_000 });
  const ordersQuery = useQuery({ queryKey: ["clinic-orders", selectedWorkspaceId], queryFn: () => workspaceScopedReads.listOrders({ limit: 50 }), enabled: contextReady, retry: false, staleTime: 15_000 });
  const activateWorkspace = async (workspace: WorkspaceSummary) => {
    if (!isActiveWorkspace(workspace) || workspace.id === selectedWorkspaceId) return;
    setSwitchingWorkspaceId(workspace.id);
    setSwitchError("");
    try {
      await apiClient.switchWorkspace(workspace.id);
      setSelectedWorkspaceId(workspace.id);
    } catch (error) {
      setSwitchError(error instanceof Error ? error.message : "تعذر تفعيل سياق العيادة.");
    } finally {
      setSwitchingWorkspaceId(null);
    }
  };
  const clinicalError = patientsQuery.error || ordersQuery.error;

  return <ClinicShell demoMode={false} activeTab={activeTab} onTab={setActiveTab} metrics={[["المرضى", patientsQuery.data ? String(patientsQuery.data.length) : "—", Users], ["الطلبات", ordersQuery.data ? String(ordersQuery.data.length) : "—", ClipboardList], ["المواعيد", "—", CalendarClock], ["زيارات نشطة", "—", Activity]]}>
    <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70"><CardHeader><CardTitle className="flex items-center gap-2 text-base"><ShieldCheck className="h-5 w-5 text-teal-600" />سياق العيادة المؤسسي</CardTitle><p className="mt-1 text-xs text-muted-foreground">اختيار مساحة العمل لا يمنح الصلاحية وحده؛ الخادم يعيد فحص المؤسسة والعضوية والترخيص والسياق.</p></CardHeader><CardContent className="space-y-3">{workspacesQuery.isLoading ? <LoadingMessage text="جارٍ تحميل مساحات العيادة…" /> : clinicWorkspaces.length === 0 ? <GatedPanel title="لا توجد مساحة عيادة مؤكدة" description="تحتاج القراءة الحية إلى Professional Verification وMembership وFacility Context من الخادم." /> : clinicWorkspaces.map((workspace) => <WorkspaceCard key={workspace.id} workspace={workspace} selected={workspace.id === selectedWorkspaceId} switching={switchingWorkspaceId === workspace.id} onSelect={() => void activateWorkspace(workspace)} />)}{switchError && <p className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/20 dark:text-rose-200" role="alert">{switchError}</p>}{workspacesQuery.error && <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200" role="alert">تعذر قراءة مساحات العيادة من الخادم.</p>}</CardContent></Card>
    {activeTab === "overview" && <LiveOverview contextReady={contextReady} loading={patientsQuery.isLoading || ordersQuery.isLoading} error={clinicalError} patients={patientsQuery.data} orders={ordersQuery.data} onTab={setActiveTab} />}
    {activeTab === "patients" && <LivePatients contextReady={contextReady} loading={patientsQuery.isLoading} error={patientsQuery.error} patients={patientsQuery.data} />}
    {activeTab === "orders" && <LiveOrders contextReady={contextReady} loading={ordersQuery.isLoading} error={ordersQuery.error} orders={ordersQuery.data} />}
    {activeTab === "appointments" && <GatedPanel title="المواعيد الحية غير موصولة بهذه الموجة" description="عقد appointment يجب أن يفرض نطاق المنشأة وحالة الموعد وIf-Match وسجل الإلغاء وإعادة الجدولة؛ لا نستخدم hospital appointments العام كبديل." />}
    {activeTab === "queue" && <GatedPanel title="قائمة الاستقبال والانتظار محجوبة" description="لا يتم تغيير check-in أو queue أو no-show من الواجهة قبل عقد خادمي مؤسسي." />}
    {activeTab === "encounter" && <GatedPanel title="Encounter والكتابة السريرية محجوبة" description="لا فتح أو تعديل أو إغلاق زيارة حية قبل عقد يفرض patient context وclinical authorization وversioning والتدقيق." />}
    {activeTab === "care-plan" && <GatedPanel title="خطة الرعاية محجوبة" description="الوصفات والإحالات والخطة والمتابعة تحتاج state machine وعقود كتابة مستقلة؛ لا يقررها المساعد." />}
    {activeTab === "inbox" && <GatedPanel title="صندوق التنبيهات السريرية محجوب" description="النتائج الحرجة ليست Notification عادية؛ يلزم تسليم وتأكيد وتصعيد وسجل تدقيق خادمي." />}
    {clinicalError && <div className="rounded-2xl border border-amber-200 bg-amber-50/70 p-5 text-sm leading-7 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200" role="status"><LockKeyhole className="ml-2 inline h-4 w-4" />أوقفنا القراءة السريرية عند فشل عقد؛ لم نستخدم Demo أو fallback legacy.</div>}
    <LiveBoundary />
  </ClinicShell>;
}

function ClinicShell({ demoMode, activeTab, onTab, metrics, children }: { demoMode: boolean; activeTab: ClinicTab; onTab: (tab: ClinicTab) => void; metrics: Array<[string, string, LucideIcon]>; children: ReactNode }) { return <div className="mx-auto max-w-7xl space-y-6" dir="rtl"><PageHeader title="العيادة الطبية" description="مساحة العيادة في GULA: من اكتشاف الخدمة والحجز إلى الوصول والزيارة وخطة الرعاية، مع فصل الحجز عن السجل السريري." /><Card className="overflow-hidden border-teal-200 bg-gradient-to-l from-teal-50 via-white to-sky-50 dark:border-teal-900/50 dark:from-teal-950/30 dark:via-background dark:to-sky-950/30"><CardContent className="p-6"><div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between"><div className="max-w-3xl space-y-3"><div className="flex items-center gap-2 text-teal-700 dark:text-teal-300"><Stethoscope className="h-5 w-5" /><span className="text-sm font-semibold">Clinic & Encounter Operations</span></div><h2 className="text-2xl font-bold tracking-tight">من يحتاجني الآن؟</h2><p className="text-sm leading-7 text-muted-foreground">الموعد ليس زيارة، والموافقة ليست تفويضاً. هذه الصفحة تعرض المسار وتُبقي القرارات السريرية والعمليات الحساسة لدى الخادم.</p><div className="flex flex-wrap gap-2"><Badge variant={demoMode ? "success" : "outline"}><ShieldCheck className="ml-1 h-3.5 w-3.5" />{demoMode ? "عرض اصطناعي معزول" : "سياق خادمي مطلوب"}</Badge><Badge variant="outline"><UserRound className="ml-1 h-3.5 w-3.5" />Appointment ≠ Encounter</Badge><Badge variant="outline"><MessageCircle className="ml-1 h-3.5 w-3.5" />Guide, not decision-maker</Badge></div></div>{demoMode && <div className="grid min-w-[290px] grid-cols-2 gap-3"><Metric label="بانتظار الطبيب" value="3" icon={Clock3} /><Metric label="زيارات نشطة" value="2" icon={Activity} /><Metric label="نتائج متاحة" value="5" icon={ClipboardList} /><Metric label="متابعة" value="4" icon={HeartPulse} /></div>}</div></CardContent></Card><MetricGrid metrics={metrics} /><ClinicTabs activeTab={activeTab} onChange={onTab} />{children}</div>; }
function ClinicTabs({ activeTab, onChange }: { activeTab: ClinicTab; onChange: (tab: ClinicTab) => void }) { return <Card><CardContent className="p-0"><div className="flex flex-wrap border-b">{TABS.map(({ id, label, icon: Icon }) => <button key={id} type="button" onClick={() => onChange(id)} aria-selected={activeTab === id} className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 ${activeTab === id ? "border-b-2 border-teal-600 text-teal-700 dark:text-teal-300" : "text-muted-foreground hover:text-foreground"}`}><Icon className="h-4 w-4" />{label}</button>)}</div></CardContent></Card>; }
function MetricGrid({ metrics }: { metrics: Array<[string, string, LucideIcon]> }) { return <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="مؤشرات العيادة">{metrics.map(([label, value, Icon]) => <Card key={label} className="overflow-hidden rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70"><CardContent className="relative p-5"><div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-l from-teal-500 to-sky-400" /><div className="flex items-start justify-between gap-3"><span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200"><Icon className="h-5 w-5" /></span><Badge variant="outline">{value === "—" ? "محجوب" : "حالة"}</Badge></div><p className="mt-5 text-sm text-muted-foreground">{label}</p><p className="mt-1 text-3xl font-bold tracking-tight text-[#0F172A] dark:text-white">{value}</p></CardContent></Card>)}</section>; }
function Metric({ label, value, icon: Icon }: { label: string; value: string; icon: LucideIcon }) { return <div className="rounded-xl bg-background/80 p-4 shadow-sm"><div className="flex items-center justify-between gap-2"><p className="text-xs text-muted-foreground">{label}</p><Icon className="h-4 w-4 text-teal-600" /></div><p className="mt-1 text-2xl font-bold">{value}</p></div>; }

function DemoOverview({ onTab }: { onTab: (tab: ClinicTab) => void }) { return <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(300px,0.8fr)]"><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Stethoscope className="h-5 w-5 text-teal-600" />لوحة الطبيب التجريبية</CardTitle></CardHeader><CardContent className="space-y-3"><DemoPriorityCard appointment={DEMO_APPOINTMENTS[1]!} onClick={() => onTab("encounter")} /><DemoPriorityCard appointment={DEMO_APPOINTMENTS[0]!} onClick={() => onTab("queue")} /><DemoPriorityCard appointment={DEMO_APPOINTMENTS[2]!} onClick={() => onTab("appointments")} /></CardContent></Card><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><ShieldCheck className="h-5 w-5 text-teal-600" />علي رضا داخل العيادة</CardTitle></CardHeader><CardContent className="space-y-3"><p className="text-sm leading-7 text-muted-foreground">يرشد إلى الحقول الناقصة والتنقل ووظائف النظام، ويلخص فقط ما يملكه الطبيب صلاحية رؤيته.</p><p className="rounded-xl border border-amber-200 bg-amber-50/70 p-3 text-xs leading-6 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200">لا يوقع، لا يغير التشخيص، لا يصدر وصفة، لا يفتح صلاحية، ولا يتجاوز Consent أو Authorization.</p><button type="button" onClick={() => onTab("care-plan")} className="flex w-full items-center justify-between rounded-xl border p-3 text-right text-sm font-medium text-teal-700 hover:border-teal-300 hover:bg-teal-50/40 dark:text-teal-300 dark:hover:bg-teal-950/20">عرض خطة الرعاية المحكومة<ArrowLeft className="h-4 w-4" /></button></CardContent></Card></div>; }
function DemoPriorityCard({ appointment, onClick }: { appointment: DemoAppointment; onClick: () => void }) { return <button type="button" onClick={onClick} className="flex w-full items-center gap-3 rounded-xl border p-4 text-right transition hover:border-teal-300 hover:bg-teal-50/40 dark:hover:bg-teal-950/20"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300"><UserRound className="h-5 w-5" /></span><span className="flex-1"><span className="block font-semibold">{appointment.patient}</span><span className="mt-1 block text-xs text-muted-foreground">{appointment.time} · {appointment.service} · {appointment.status}</span></span><Badge variant={appointment.priority === "عاجل" ? "destructive" : "outline"}>{appointment.priority}</Badge><ArrowLeft className="h-4 w-4 text-muted-foreground" /></button>; }
function DemoAppointments() { return <ListCard title="مواعيد العيادة الاصطناعية" description="حالات الموعد للعرض فقط؛ لا تأكيد أو إلغاء أو إعادة جدولة حقيقية.">{DEMO_APPOINTMENTS.map((appointment) => <div key={appointment.id} className="flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">{appointment.time} · {appointment.patient}</p><p className="mt-1 text-xs text-muted-foreground">{appointment.service} · {appointment.type}</p></div><div className="flex items-center gap-2"><Badge variant={appointment.priority === "عاجل" ? "destructive" : "outline"}>{appointment.priority}</Badge><Badge variant={appointment.status === "مكتمل" ? "success" : "outline"}>{appointment.status}</Badge></div></div>)}</ListCard>; }
function DemoQueue() { return <ListCard title="الاستقبال والانتظار الاصطناعي" description="لا ينفذ Demo check-in أو triage أو no-show."><QueueRow label="وصل" value="حسن نوري" tone="warning" /><QueueRow label="بانتظار الطبيب" value="سارة عبد الرحمن" tone="info" /><QueueRow label="مع الطبيب" value="علي كريم حسن" tone="success" /><QueueRow label="لم يحضر" value="موعد اصطناعي" tone="muted" /></ListCard>; }
function DemoPatients() { return <ListCard title="مرضى ضمن نطاق الزيارة الاصطناعي" description="لا يوجد بحث حر خارج السياق ولا Patient Merge ولا بيانات وطنية حقيقية."><QueueRow label="سياق علاجي" value="حسن نوري · متابعة مزمنة" tone="info" /><QueueRow label="سياق علاجي" value="سارة عبد الرحمن · استشارة جديدة" tone="info" /><QueueRow label="سياق علاجي" value="مريم فاضل · طب عن بعد" tone="info" /></ListCard>; }
function DemoEncounter() { return <Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><FileText className="h-5 w-5 text-teal-600" />Encounter تجريبي — {DEMO_ENCOUNTER.patient}</CardTitle><p className="mt-1 text-xs text-muted-foreground">Appointment ليس Encounter. هذه شاشة عرض بلا حفظ أو توقيع أو إغلاق.</p></CardHeader><CardContent className="space-y-5"><div className="grid gap-3 md:grid-cols-2"><InfoBox label="الهوية والسياق" value={DEMO_ENCOUNTER.identity} /><InfoBox label="التنبيهات والحساسيات" value={DEMO_ENCOUNTER.alerts} /><InfoBox label="الشكوى الرئيسية" value={DEMO_ENCOUNTER.complaint} /><InfoBox label="العلامات الحيوية" value={DEMO_ENCOUNTER.vitals} /></div><div className="rounded-xl border p-4"><p className="font-semibold">التاريخ والفحص والتقييم</p><p className="mt-2 text-sm leading-7 text-muted-foreground">{DEMO_ENCOUNTER.history}</p></div><div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5"><BlockedAction label="طلب مختبر" /><BlockedAction label="طلب أشعة" /><BlockedAction label="وصفة" /><BlockedAction label="إحالة" /><BlockedAction label="إغلاق الزيارة" /></div></CardContent></Card>; }
function DemoOrders() { return <ListCard title="الطلبات والنتائج الاصطناعية" description="النتائج لا تُعتمد تلقائياً ولا تتحول إلى تشخيص أو وصفة."><QueueRow label="مختبر" value="CBC · متاح للعرض" tone="success" /><QueueRow label="أشعة" value="Chest X-Ray · قيد القراءة" tone="warning" /><QueueRow label="نتيجة حرجة" value="تظهر في Clinical Alert Center وليس Notification عادية" tone="critical" /></ListCard>; }
function DemoCarePlan() { return <ListCard title="خطة الرعاية الاصطناعية" description="كل العناصر محكومة ومقترحة للشرح، ولا يوجد أمر سريري أو متابعة حقيقية."><QueueRow label="دواء" value="اقتراح اصطناعي يحتاج قرار الطبيب" tone="info" /><QueueRow label="متابعة" value="بعد 30 يوماً · سبب المتابعة ظاهر" tone="info" /><QueueRow label="تثقيف" value="تعليمات عامة غير تشخيصية" tone="info" /></ListCard>; }
function DemoInbox() { return <ListCard title="صندوق التنبيهات السريري الاصطناعي" description="لا يرسل Demo أي إشعار ولا يسجل acknowledgment أو escalation."><QueueRow label="عاجل" value="نتيجة تحتاج مراجعة بشرية" tone="critical" /><QueueRow label="معلومة" value="موعد متابعة قادم" tone="info" /></ListCard>; }

function LiveOverview({ contextReady, loading, error, patients, orders, onTab }: { contextReady: boolean; loading: boolean; error: unknown; patients?: ClinicalPatientRead[]; orders?: ClinicalOrderRead[]; onTab: (tab: ClinicTab) => void }) { return <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(300px,0.8fr)]"><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Stethoscope className="h-5 w-5 text-teal-600" />ملخص العيادة الحي</CardTitle><p className="mt-1 text-xs text-muted-foreground">قراءات canonical محدودة بعد تفعيل السياق؛ لا توجد كتابة Encounter أو Appointment.</p></CardHeader><CardContent>{!contextReady ? <GatedPanel title="فعّل سياق العيادة أولاً" description="لا يتم تحميل المرضى والطلبات قبل workspace خادمي صالح." /> : loading ? <LoadingMessage text="جارٍ تحميل القراءة السريرية…" /> : error ? <GatedPanel title="أوقفنا القراءة السريرية" description="فشل عقد واحد؛ لم نستخدم Demo أو fallback legacy." /> : <div className="grid gap-3 sm:grid-cols-2"><InfoBox label="مرضى ضمن النطاق" value={String(patients?.length ?? 0)} /><InfoBox label="طلبات ضمن النطاق" value={String(orders?.length ?? 0)} /></div>}</CardContent></Card><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><LockKeyhole className="h-5 w-5 text-amber-600" />مسارات محكومة</CardTitle></CardHeader><CardContent className="space-y-3"><GatedLine label="المواعيد وقائمة الانتظار" onClick={() => onTab("appointments")} /><GatedLine label="Encounter والتوثيق" onClick={() => onTab("encounter")} /><GatedLine label="خطة الرعاية والوصفة والإحالة" onClick={() => onTab("care-plan")} /></CardContent></Card></div>; }
function LivePatients({ contextReady, loading, error, patients }: { contextReady: boolean; loading: boolean; error: unknown; patients?: ClinicalPatientRead[] }) { return <ListCard title="المرضى ضمن النطاق السريري" description="تأتي القراءة من canonical clinical gateway وتُرفض الاستجابة إذا احتوت حقولاً حساسة غير مسموحة.">{!contextReady ? <GatedPanel title="فعّل سياق العيادة أولاً" description="Patient Access يتطلب Clinical Context وAuthorization." /> : loading ? <LoadingMessage text="جارٍ تحميل المرضى…" /> : error ? <GatedPanel title="تعذر قراءة المرضى" description="لم يتم استخدام Demo كبديل." /> : patients?.length ? patients.map((patient) => <div key={patient.id} className="flex items-center gap-3 rounded-xl border p-4"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300"><UserRound className="h-5 w-5" /></span><div><p className="font-semibold">{patient.display_name}</p><p className="mt-1 text-xs text-muted-foreground">مريض ضمن السياق · لا يعرض الهاتف أو الرقم الوطني</p></div></div>) : <EmptyMessage text="لا يوجد مريض ضمن السياق الحالي." />}</ListCard>; }
function LiveOrders({ contextReady, loading, error, orders }: { contextReady: boolean; loading: boolean; error: unknown; orders?: ClinicalOrderRead[] }) { return <ListCard title="الطلبات السريرية ضمن النطاق" description="هذه قراءة للطلبات فقط؛ لا إدخال نتيجة ولا وصفة ولا تغيير حالة من هذه الصفحة.">{!contextReady ? <GatedPanel title="فعّل سياق العيادة أولاً" description="Order Access يتطلب Clinical Context وAuthorization." /> : loading ? <LoadingMessage text="جارٍ تحميل الطلبات…" /> : error ? <GatedPanel title="تعذر قراءة الطلبات" description="لم يتم استخدام Demo كبديل." /> : orders?.length ? orders.map((order) => <div key={order.id} className="flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">{order.patient_display_name ?? "مريض ضمن النطاق"}</p><p className="mt-1 text-xs text-muted-foreground">{order.test_count} عناصر · {order.practitioner_display_name ?? "ممارس ضمن السياق"}</p></div><Badge variant="outline">{order.status}</Badge></div>) : <EmptyMessage text="لا يوجد طلب ضمن السياق الحالي." />}</ListCard>; }

function ClinicBoundary({ children, tone = "amber" }: { children: ReactNode; tone?: "amber" | "teal" }) { return <Card className={tone === "amber" ? "border-amber-200 bg-amber-50/60 dark:border-amber-900/50 dark:bg-amber-950/20" : "border-teal-200 bg-teal-50/60 dark:border-teal-900/50 dark:bg-teal-950/20"}><CardContent className="flex items-start gap-3 p-5 text-sm leading-7"><Info className={`mt-1 h-5 w-5 shrink-0 ${tone === "amber" ? "text-amber-700 dark:text-amber-400" : "text-teal-700 dark:text-teal-400"}`} />{children}</CardContent></Card>; }
function DemoBoundary() { return <ClinicBoundary><p><strong>حدود Demo:</strong> كل المواعيد والمرضى والزيارات والطلبات اصطناعية للعرض. لا يوجد إنشاء Encounter أو وصفة أو إحالة أو check-in أو إرسال تنبيه أو اتصال ببيانات حقيقية.</p></ClinicBoundary>; }
function LiveBoundary() { return <ClinicBoundary><p><strong>حدود Live الحالية:</strong> القراءة تقتصر على المرضى والطلبات من canonical clinical gateway بعد تفعيل السياق. المواعيد والزيارات والكتابة السريرية والوصفات والإحالات والتأمين والتنبيهات تبقى محجوبة حتى عقودها.</p></ClinicBoundary>; }
function ListCard({ title, description, children }: { title: string; description: string; children: ReactNode }) { return <Card><CardHeader><CardTitle>{title}</CardTitle><p className="mt-1 text-xs text-muted-foreground">{description}</p></CardHeader><CardContent className="space-y-3">{children}</CardContent></Card>; }
function WorkspaceCard({ workspace, selected, switching, onSelect }: { workspace: WorkspaceSummary; selected: boolean; switching: boolean; onSelect: () => void }) { const active = isActiveWorkspace(workspace); return <div className={`rounded-xl border p-4 transition ${selected ? "border-teal-400 bg-teal-50/60 dark:border-teal-700 dark:bg-teal-950/20" : "border-slate-200/80 dark:border-white/10"}`}><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><p className="text-sm font-bold">{workspace.name_ar ?? workspace.name}</p><p className="mt-1 text-xs text-muted-foreground">{workspace.facility_id ?? "منشأة غير معروضة"} · {workspace.department_id ?? "قسم غير معروض"}</p></div><div className="flex items-center gap-2"><Badge variant={active ? "success" : "outline"}>{workspace.status}</Badge><Button type="button" size="sm" variant={selected ? "secondary" : "outline"} disabled={!active || selected || switching} onClick={onSelect}>{switching ? "جارٍ التفعيل…" : selected ? "السياق الحالي" : "تفعيل سياق العيادة"}</Button></div></div></div>; }
function GatedPanel({ title, description }: { title: string; description: string }) { return <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-5 text-sm leading-7 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200"><LockKeyhole className="ml-2 inline h-4 w-4" /><strong>{title}</strong><p className="mt-2 text-xs leading-6 opacity-80">{description}</p></div>; }
function GatedLine({ label, onClick }: { label: string; onClick: () => void }) { return <button type="button" onClick={onClick} className="flex w-full items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50/60 p-3 text-right text-sm text-amber-950 transition hover:border-amber-300 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200"><span>{label}</span><LockKeyhole className="h-4 w-4" /></button>; }
function BlockedAction({ label }: { label: string }) { return <Button type="button" variant="outline" disabled className="w-full"><LockKeyhole className="ml-1 h-3.5 w-3.5" />{label}</Button>; }
function QueueRow({ label, value, tone }: { label: string; value: string; tone: "critical" | "warning" | "success" | "info" | "muted" }) { const classes = { critical: "border-red-200 bg-red-50/70 dark:border-red-900/50 dark:bg-red-950/20", warning: "border-amber-200 bg-amber-50/70 dark:border-amber-900/50 dark:bg-amber-950/20", success: "border-emerald-200 bg-emerald-50/70 dark:border-emerald-900/50 dark:bg-emerald-950/20", info: "border-sky-200 bg-sky-50/70 dark:border-sky-900/50 dark:bg-sky-950/20", muted: "border-slate-200 bg-slate-50/70 dark:border-white/10 dark:bg-white/5" }; return <div className={`flex items-center justify-between gap-3 rounded-xl border p-4 ${classes[tone]}`}><span className="text-sm font-semibold">{label}</span><span className="text-sm text-muted-foreground">{value}</span></div>; }
function InfoBox({ label, value }: { label: string; value: string }) { return <div className="rounded-xl border bg-muted/30 p-4"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 text-sm font-semibold leading-6">{value}</p></div>; }
function LoadingMessage({ text }: { text: string }) { return <div className="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">{text}</div>; }
function EmptyMessage({ text }: { text: string }) { return <div className="rounded-xl border border-dashed p-8 text-center text-sm text-muted-foreground">{text}</div>; }

export { DemoClinicWorkspace };
