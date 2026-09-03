import { useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  Ambulance,
  ArrowLeft,
  BellRing,
  Droplets,
  BookOpenCheck,
  ClipboardCheck,
  ClipboardList,
  FileCheck2,
  HeartPulse,
  Info,
  LockKeyhole,
  Microscope,
  Radio,
  ShieldCheck,
  Siren,
  Stethoscope,
  TimerReset,
  Truck,
  Users,
  type LucideIcon,
} from "lucide-react";
import { apiClient, type WorkspaceSummary } from "@/api/client";
import { workspaceScopedReads, type ClinicalOrderRead, type ClinicalPatientRead } from "@/api/workspaceScopedReads";
import { useAuth } from "@/contexts/AuthContext";
import { PageHeader } from "@/components/shared/PageComponents";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

type AcuteCareTab =
  | "overview"
  | "emergency"
  | "ambulance"
  | "prehospital"
  | "patients"
  | "orders"
  | "critical-care"
  | "operating-room"
  | "blood-bank"
  | "pathology"
  | "infection-control"
  | "handover"
  | "audit";

type Tone = "critical" | "warning" | "success" | "info" | "muted";

type DemoQueueItem = {
  label: string;
  value: string;
  tone: Tone;
};

const DEMO_QUEUE: DemoQueueItem[] = [
  { label: "P1 · مريض اصطناعي 04", value: "إنعاش · فريق مستعد", tone: "critical" },
  { label: "P2 · مريض اصطناعي 05", value: "مراقبة · تصوير مطلوب", tone: "warning" },
  { label: "مريض اصطناعي مجهول · TEMP-000123", value: "هوية مؤقتة · لا دمج تلقائي", tone: "info" },
  { label: "P3 · مريض اصطناعي 06", value: "ملاحظة · إعادة تقييم مطلوبة", tone: "success" },
];

const DEMO_AMBULANCES = [
  { id: "AMB-SYN-01", status: "في الطريق", crew: "طاقم اصطناعي A", destination: "مستشفى الرافدين" },
  { id: "AMB-SYN-02", status: "متاحة", crew: "طاقم اصطناعي B", destination: "بانتظار بلاغ" },
  { id: "AMB-SYN-03", status: "في موقع الحادث", crew: "طاقم اصطناعي C", destination: "لم يُحدد" },
];

const TABS: Array<{ id: AcuteCareTab; label: string; icon: LucideIcon }> = [
  { id: "overview", label: "نظرة الرعاية الحادة", icon: Activity },
  { id: "emergency", label: "الطوارئ والفرز", icon: Siren },
  { id: "ambulance", label: "الإسعاف والتوجيه", icon: Ambulance },
  { id: "prehospital", label: "الرعاية قبل المستشفى", icon: Truck },
  { id: "patients", label: "المرضى ضمن النطاق", icon: Users },
  { id: "orders", label: "الأوامر والنتائج", icon: ClipboardList },
  { id: "critical-care", label: "العناية الحرجة", icon: HeartPulse },
  { id: "operating-room", label: "العمليات", icon: Stethoscope },
  { id: "blood-bank", label: "بنك الدم", icon: Droplets },
  { id: "pathology", label: "المرضيات والعينات", icon: Microscope },
  { id: "infection-control", label: "مكافحة العدوى", icon: ShieldCheck },
  { id: "handover", label: "التسليم والتحويل", icon: ClipboardCheck },
  { id: "audit", label: "التدقيق والحوكمة", icon: FileCheck2 },
];

function isActiveWorkspace(workspace: WorkspaceSummary) {
  return ["active", "verified", "approved"].includes(workspace.status.toLowerCase());
}

export default function AcuteCareOperationsWorkspacePage() {
  const { demoMode } = useAuth();
  return demoMode ? <DemoAcuteCareWorkspace /> : <LiveAcuteCareWorkspace />;
}

function DemoAcuteCareWorkspace() {
  const [activeTab, setActiveTab] = useState<AcuteCareTab>("overview");

  return (
    <AcuteCareShell
      demoMode
      activeTab={activeTab}
      onTab={setActiveTab}
      metrics={[
        ["حالات حرجة", "3", Siren],
        ["وحدات الإسعاف", "8", Ambulance],
        ["مراقبة", "7", TimerReset],
        ["تنبيهات", "2", BellRing],
      ]}
    >
      {activeTab === "overview" && <DemoOverview onTab={setActiveTab} />}
      {activeTab === "emergency" && <DemoEmergency />}
      {activeTab === "ambulance" && <DemoAmbulance />}
      {activeTab === "prehospital" && <DemoPrehospital />}
      {activeTab === "patients" && <DemoPatients />}
      {activeTab === "orders" && <DemoOrders />}
      {activeTab === "critical-care" && <DemoCriticalCare />}
      {activeTab === "operating-room" && <DemoOperatingRoom />}
      {activeTab === "blood-bank" && <DemoBloodBank />}
      {activeTab === "pathology" && <DemoPathology />}
      {activeTab === "infection-control" && <DemoInfectionControl />}
      {activeTab === "handover" && <DemoHandover />}
      {activeTab === "audit" && <DemoAudit />}
      <DemoBoundary />
    </AcuteCareShell>
  );
}

function LiveAcuteCareWorkspace() {
  const [activeTab, setActiveTab] = useState<AcuteCareTab>("overview");
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string | null>(null);
  const [switchingWorkspaceId, setSwitchingWorkspaceId] = useState<string | null>(null);
  const [switchError, setSwitchError] = useState("");
  const workspacesQuery = useQuery({
    queryKey: ["acute-care-workspaces", "me"],
    queryFn: () => apiClient.listWorkspaces(),
    retry: false,
    staleTime: 30_000,
  });
  const acuteWorkspaces = (workspacesQuery.data?.workspaces ?? []).filter((workspace) => {
    const type = workspace.workspace_type.toLowerCase();
    return (
      !workspace.is_personal &&
      Boolean(workspace.facility_id) &&
      (type.includes("hospital") || type.includes("facility") || type.includes("emergency") || type.includes("acute") || type.includes("ems"))
    );
  });
  const selectedWorkspace = acuteWorkspaces.find((workspace) => workspace.id === selectedWorkspaceId);
  const contextReady = Boolean(selectedWorkspaceId && selectedWorkspace && isActiveWorkspace(selectedWorkspace));
  const patientsQuery = useQuery({
    queryKey: ["acute-care-patients", selectedWorkspaceId],
    queryFn: () => workspaceScopedReads.listPatients({ limit: 50 }),
    enabled: contextReady,
    retry: false,
    staleTime: 15_000,
  });
  const ordersQuery = useQuery({
    queryKey: ["acute-care-orders", selectedWorkspaceId],
    queryFn: () => workspaceScopedReads.listOrders({ limit: 50 }),
    enabled: contextReady,
    retry: false,
    staleTime: 15_000,
  });
  const activateWorkspace = async (workspace: WorkspaceSummary) => {
    if (!isActiveWorkspace(workspace) || workspace.id === selectedWorkspaceId) return;
    setSwitchingWorkspaceId(workspace.id);
    setSwitchError("");
    try {
      await apiClient.switchWorkspace(workspace.id);
      setSelectedWorkspaceId(workspace.id);
    } catch (error) {
      setSwitchError(error instanceof Error ? error.message : "تعذر تفعيل سياق الرعاية الحادة.");
    } finally {
      setSwitchingWorkspaceId(null);
    }
  };
  const clinicalError = patientsQuery.error || ordersQuery.error;

  return (
    <AcuteCareShell
      demoMode={false}
      activeTab={activeTab}
      onTab={setActiveTab}
      metrics={[
        ["المرضى", patientsQuery.data ? String(patientsQuery.data.length) : "—", Users],
        ["الأوامر", ordersQuery.data ? String(ordersQuery.data.length) : "—", ClipboardList],
        ["الإسعاف", "—", Ambulance],
        ["ICU / OR / دم", "—", HeartPulse],
      ]}
    >
      <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <ShieldCheck className="h-5 w-5 text-indigo-600" />
            سياق الطوارئ والرعاية الحادة
          </CardTitle>
          <p className="mt-1 text-xs text-muted-foreground">
            كل قراءة حية تحتاج منشأة وعضوية ودوراً وسياقاً خادمياً؛ اختيار workspace لا يمنح صلاحية ولا يفعّل Break-Glass.
          </p>
        </CardHeader>
        <CardContent className="space-y-3">
          {workspacesQuery.isLoading ? (
            <LoadingMessage text="جارٍ تحميل مساحات الرعاية الحادة…" />
          ) : acuteWorkspaces.length === 0 ? (
            <GatedPanel title="لا توجد مساحة رعاية حادة مؤكدة" description="تحتاج القراءة الحية إلى Organization Membership وProfessional Verification وFacility Context." />
          ) : (
            acuteWorkspaces.map((workspace) => (
              <WorkspaceCard
                key={workspace.id}
                workspace={workspace}
                selected={workspace.id === selectedWorkspaceId}
                switching={switchingWorkspaceId === workspace.id}
                onSelect={() => void activateWorkspace(workspace)}
              />
            ))
          )}
          {switchError && <p className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/20 dark:text-rose-200" role="alert">{switchError}</p>}
          {workspacesQuery.error && <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200" role="alert">تعذر قراءة مساحات الرعاية الحادة من الخادم.</p>}
        </CardContent>
      </Card>
      {activeTab === "overview" && <LiveOverview contextReady={contextReady} loading={patientsQuery.isLoading || ordersQuery.isLoading} error={clinicalError} patients={patientsQuery.data} orders={ordersQuery.data} onTab={setActiveTab} />}
      {activeTab === "patients" && <LivePatients contextReady={contextReady} loading={patientsQuery.isLoading} error={patientsQuery.error} patients={patientsQuery.data} />}
      {activeTab === "orders" && <LiveOrders contextReady={contextReady} loading={ordersQuery.isLoading} error={ordersQuery.error} orders={ordersQuery.data} />}
      {activeTab === "emergency" && <GatedPanel title="عمليات الطوارئ والفرز محجوبة" description="لا يبدأ Emergency Encounter أو Break-Glass أو Triage من الواجهة قبل عقد يفرض السبب والأولوية والهوية المؤقتة والتدقيق." />}
      {activeTab === "ambulance" && <GatedPanel title="Dispatch والإسعاف محجوبان" description="لا يوجد عقد frontend آمن لتخصيص وحدة أو مشاركة موقع أو إرسال Pre-alert؛ القرار والتتبع يحتاجان صلاحية وسياقاً وسياسة احتفاظ." />}
      {activeTab === "prehospital" && <GatedPanel title="الرعاية قبل المستشفى محجوبة" description="لا تسجيل ePCR أو علامات حيوية أو تدخلات أو نقل من الواجهة قبل عقد مستقل يفرض مصدر القياس والنسخة والتدقيق." />}
      {activeTab === "critical-care" && <GatedPanel title="العناية الحرجة وDevice Gateway محجوبان" description="لا تُقرأ ICU أو ventilator أو telemetry أو flowsheets من broad endpoints؛ يلزم عقد facility-scoped متخصص." />}
      {activeTab === "operating-room" && <GatedPanel title="العمليات الجراحية محجوبة" description="لا جدولة أو موافقة أو checklist أو تنفيذ أو تخدير أو implant من الواجهة قبل Workflow سريري خادمي." />}
      {activeTab === "blood-bank" && <GatedPanel title="بنك الدم محجوب" description="لا crossmatch أو issue أو administration؛ عمليات الدم عالية الخطورة تحتاج تحققاً ثنائي الشخص وسجل تتبع immutable." />}
      {activeTab === "pathology" && <GatedPanel title="المرضيات وتتبع العينات محجوبان" description="لا وصول إلى عينات أو تقارير أو accession أو barcode قبل عقد specimen-scoped مع purpose وaudit." />}
      {activeTab === "infection-control" && <GatedPanel title="مكافحة العدوى محجوبة" description="لا كشف للتعرضات أو المخالطين أو المناطق؛ يلزم purpose-based access ونطاق موقع وسياسة إفصاح أدنى." />}
      {activeTab === "handover" && <GatedPanel title="التسليم والتحويل محجوبان" description="لا قبول ICU أو تحويل أو handover أو discharge؛ يجب أن يقبل الفريق المستلم ويثبت الحالة والمهام والنتائج المعلقة." />}
      {activeTab === "audit" && <GatedPanel title="تدقيق الرعاية الحادة محجوب" description="لا يُعرض سجل نشاط شامل؛ يلزم endpoint purpose-limited مع pagination وminimum disclosure وauthorization." />}
      {clinicalError && <div className="rounded-2xl border border-amber-200 bg-amber-50/70 p-5 text-sm leading-7 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200" role="status"><LockKeyhole className="ml-2 inline h-4 w-4" />أوقفنا القراءة عند فشل العقد؛ لم نستخدم Demo أو fallback قديم.</div>}
      <LiveBoundary />
    </AcuteCareShell>
  );
}

function AcuteCareShell({
  demoMode,
  activeTab,
  onTab,
  metrics,
  children,
}: {
  demoMode: boolean;
  activeTab: AcuteCareTab;
  onTab: (tab: AcuteCareTab) => void;
  metrics: Array<[string, string, LucideIcon]>;
  children: ReactNode;
}) {
  return (
    <div className="mx-auto max-w-7xl space-y-6" dir="rtl">
      <PageHeader title="الطوارئ والإسعاف والرعاية الحادة" description="Acute Care Domain مستقل: الطوارئ والـEMS والرعاية قبل المستشفى والعناية الحرجة والعمليات والدم والمرضيات ومكافحة العدوى." />
      <Card className="overflow-hidden border-rose-200 bg-gradient-to-l from-rose-50 via-white to-indigo-50 dark:border-rose-900/50 dark:from-rose-950/30 dark:via-background dark:to-indigo-950/30">
        <CardContent className="p-6">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
            <div className="max-w-3xl space-y-3">
              <div className="flex items-center gap-2 text-rose-700 dark:text-rose-300"><Siren className="h-5 w-5" /><span className="text-sm font-semibold">Acute Care Command · Secure Operations</span></div>
              <h2 className="text-2xl font-bold tracking-tight">كل ثانية مهمة، والسياق قبل الصلاحية</h2>
              <p className="text-sm leading-7 text-muted-foreground">الفرز يحدد الأولوية ولا يساوي التشخيص، والمريض المجهول يحتاج هوية مؤقتة، وكل انتقال حاد يجب أن يمر عبر خادم GULA لا عبر الواجهة.</p>
              <div className="flex flex-wrap gap-2"><Badge variant={demoMode ? "success" : "outline"}><ShieldCheck className="ml-1 h-3.5 w-3.5" />{demoMode ? "عرض اصطناعي معزول" : "سياق خادمي مطلوب"}</Badge><Badge variant="outline"><LockKeyhole className="ml-1 h-3.5 w-3.5" />RBAC + Context</Badge><Badge variant="outline"><Radio className="ml-1 h-3.5 w-3.5" />Fail closed</Badge></div>
            </div>
            {demoMode && <div className="grid min-w-[270px] grid-cols-2 gap-3"><SmallMetric label="P1 / P2" value="3 / 8" icon={Siren} /><SmallMetric label="الإسعاف" value="8" icon={Ambulance} /><SmallMetric label="ICU" value="90%" icon={HeartPulse} /><SmallMetric label="تنبيهات" value="2" icon={BellRing} /></div>}
          </div>
        </CardContent>
      </Card>
      <MetricGrid metrics={metrics} />
      <AcuteCareTabs activeTab={activeTab} onChange={onTab} />
      {children}
    </div>
  );
}

function AcuteCareTabs({ activeTab, onChange }: { activeTab: AcuteCareTab; onChange: (tab: AcuteCareTab) => void }) {
  return <Card><CardContent className="p-0"><div className="flex flex-wrap border-b">{TABS.map(({ id, label, icon: Icon }) => <button key={id} type="button" onClick={() => onChange(id)} aria-selected={activeTab === id} className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-500 ${activeTab === id ? "border-b-2 border-rose-600 text-rose-700 dark:text-rose-300" : "text-muted-foreground hover:text-foreground"}`}><Icon className="h-4 w-4" />{label}</button>)}</div></CardContent></Card>;
}

function MetricGrid({ metrics }: { metrics: Array<[string, string, LucideIcon]> }) {
  return <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="مؤشرات الرعاية الحادة">{metrics.map(([label, value, Icon]) => <Card key={label} className="overflow-hidden rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70"><CardContent className="relative p-5"><div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-l from-rose-500 to-indigo-500" /><div className="flex items-start justify-between gap-3"><span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200"><Icon className="h-5 w-5" /></span><Badge variant="outline">{value === "—" ? "محجوب" : "حالة"}</Badge></div><p className="mt-5 text-sm text-muted-foreground">{label}</p><p className="mt-1 text-3xl font-bold tracking-tight text-[#0F172A] dark:text-white">{value}</p></CardContent></Card>)}</section>;
}

function SmallMetric({ label, value, icon: Icon }: { label: string; value: string; icon: LucideIcon }) {
  return <div className="rounded-xl bg-background/80 p-3 shadow-sm"><div className="flex items-center justify-between gap-2"><p className="text-xs text-muted-foreground">{label}</p><Icon className="h-4 w-4 text-rose-600" /></div><p className="mt-1 text-2xl font-bold">{value}</p></div>;
}

function DemoOverview({ onTab }: { onTab: (tab: AcuteCareTab) => void }) {
  return <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(300px,0.8fr)]"><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Siren className="h-5 w-5 text-rose-600" />ما يحتاج الفريق الآن</CardTitle></CardHeader><CardContent className="space-y-3"><PriorityCard title="P1 · إنعاش" subtitle="مريض اصطناعي 04 · فريق الإنعاش جاهز" tone="critical" onClick={() => onTab("emergency")} /><PriorityCard title="إسعاف في الطريق" subtitle="AMB-SYN-01 · ETA اصطناعي · Pre-alert للشرح" tone="warning" onClick={() => onTab("ambulance")} /><PriorityCard title="هوية مؤقتة" subtitle="TEMP-000123 · لا دمج أو مطابقة تلقائية" tone="info" onClick={() => onTab("prehospital")} /></CardContent></Card><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><BookOpenCheck className="h-5 w-5 text-indigo-600" />مرشد علي رضا</CardTitle></CardHeader><CardContent className="space-y-3"><p className="text-sm leading-7 text-muted-foreground">يرتب المعلومات ويشرح المسار ويذكّر الفريق بالخطوات الموثقة، دون تشخيص أو قرار فرز أو اعتماد أو تنفيذ.</p><p className="rounded-xl border border-amber-200 bg-amber-50/70 p-3 text-xs leading-6 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200">التنبيه ليس إجراءً سريرياً، وفتح الإشعار لا يساوي acknowledgement سريري أو تصعيداً.</p><button type="button" onClick={() => onTab("audit")} className="flex w-full items-center justify-between rounded-xl border p-3 text-right text-sm font-medium text-indigo-700 hover:border-indigo-300 hover:bg-indigo-50/40 dark:text-indigo-300 dark:hover:bg-indigo-950/20">عرض حوكمة المسار التجريبي<ArrowLeft className="h-4 w-4" /></button></CardContent></Card></div>;
}

function PriorityCard({ title, subtitle, tone, onClick }: { title: string; subtitle: string; tone: Tone; onClick: () => void }) {
  const color = tone === "critical" ? "bg-rose-50 text-rose-800 dark:bg-rose-950/20 dark:text-rose-200" : tone === "warning" ? "bg-amber-50 text-amber-800 dark:bg-amber-950/20 dark:text-amber-200" : "bg-sky-50 text-sky-800 dark:bg-sky-950/20 dark:text-sky-200";
  return <button type="button" onClick={onClick} className={`flex w-full items-center justify-between gap-3 rounded-xl border p-4 text-right transition hover:border-indigo-300 ${color}`}><span><span className="block font-semibold">{title}</span><span className="mt-1 block text-xs opacity-80">{subtitle}</span></span><ArrowLeft className="h-4 w-4" /></button>;
}

function DemoEmergency() {
  return <ListCard title="الطوارئ والفرز الاصطناعي" description="الأولوية والسبب والفاعل والوقت معروضة للشرح؛ لا يوجد Triage أو Break-Glass حقيقي.">{DEMO_QUEUE.map((item) => <QueueRow key={item.label} label={item.label} value={item.value} tone={item.tone} />)}<div className="rounded-xl border border-indigo-200 bg-indigo-50/60 p-4 text-sm leading-7 text-indigo-950 dark:border-indigo-900/50 dark:bg-indigo-950/20 dark:text-indigo-200"><strong>قاعدة السلامة:</strong> العلاج العاجل لا ينتظر الدفع أو التأمين، لكن أي هوية أو انتقال أو إجراء يبقى خاضعاً للسياق والتدقيق.</div></ListCard>;
}

function DemoAmbulance() {
  return <ListCard title="الإسعاف والتوجيه الاصطناعي" description="حالات الوحدات والطاقم والموقع وETA اصطناعية فقط؛ لا GPS أو Dispatch أو اتصال خارجي."><div className="grid gap-3 md:grid-cols-3">{DEMO_AMBULANCES.map((ambulance) => <div key={ambulance.id} className="rounded-xl border p-4"><div className="flex items-center justify-between gap-2"><p className="font-semibold">{ambulance.id}</p><Badge variant={ambulance.status === "متاحة" ? "success" : "warning"}>{ambulance.status}</Badge></div><p className="mt-3 text-xs text-muted-foreground">{ambulance.crew}</p><p className="mt-1 text-xs text-muted-foreground">الوجهة: {ambulance.destination}</p></div>)}</div><QueueRow label="اختيار المستشفى" value="قدرة مناسبة لا الأقرب فقط · محجوب في Live" tone="info" /><QueueRow label="Hospital pre-alert" value="ETA + حالة + موارد مطلوبة · اصطناعي" tone="muted" /></ListCard>;
}

function DemoPrehospital() {
  return <ListCard title="الرعاية قبل المستشفى" description="Pre-hospital Encounter وePCR والهوية المؤقتة معروضة كرحلة؛ لا تحفظ الواجهة أحداثاً سريرية."><QueueRow label="بلاغ اصطناعي" value="حادث · أولوية Bravo · وقت اصطناعي" tone="warning" /><QueueRow label="مريض مجهول" value="TEMP-000123 · هوية مؤقتة" tone="critical" /><QueueRow label="علامات حيوية" value="المصدر والوقت والجهاز مطلوبان" tone="info" /><QueueRow label="التسليم" value="Structured handover · Acceptance مطلوب" tone="success" /><div className="rounded-xl border border-amber-200 bg-amber-50/70 p-4 text-sm leading-7 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200"><strong>لا دمج تلقائي:</strong> ربط الهوية المؤقتة بالمواطن يحتاج أدلة وهوية وصلاحية خاصة وسبباً وتدقيقاً ومراجعة.</div></ListCard>;
}

function DemoPatients() {
  return <ListCard title="مرضى الرعاية الحادة الاصطناعيون" description="الوصول ضمن سياق الرعاية؛ لا بحث فضولي ولا عرض لمعرف وطني أو هاتف ولا Patient Merge."><QueueRow label="مريض اصطناعي 04" value="إنعاش · مسؤول سريري محدد" tone="critical" /><QueueRow label="مريض اصطناعي 05" value="مراقبة · إعادة تقييم" tone="warning" /><QueueRow label="مريض اصطناعي مجهول · TEMP-000123" value="رابط مؤقت · يحتاج Identity Resolution" tone="info" /></ListCard>;
}

function DemoOrders() {
  return <ListCard title="أوامر ونتائج الطوارئ الاصطناعية" description="STAT ليس افتراضياً؛ Order لا يساوي Performed، وفتح التنبيه لا يساوي إجراءً سريرياً."><QueueRow label="مختبر · STAT" value="Specimen مطلوب · Critical check لاحق" tone="warning" /><QueueRow label="أشعة · Urgent" value="Acquisition/report محجوبان" tone="info" /><QueueRow label="دواء · Protocol set" value="تحقق صيدلي ثم إعطاء مهني" tone="critical" /><QueueRow label="تنبيه حرج" value="استلام التنبيه ≠ اتخاذ الإجراء" tone="success" /></ListCard>;
}

function DemoCriticalCare() {
  return <ListCard title="العناية الحرجة الاصطناعية" description="ICU وflowsheets وdevice gateway والتنبيهات الزمنية للشرح فقط؛ لا telemetry خام أو ventilator data حقيقية."><QueueRow label="ICU-03" value="مريض اصطناعي 02 · مراقبة" tone="warning" /><QueueRow label="Flowsheet" value="Vitals · ventilation · infusions · labs" tone="info" /><QueueRow label="Alert fatigue" value="تقليل التكرار والتصعيد وفق سياسة" tone="critical" /><QueueRow label="Device Gateway" value="جهاز → بوابة محلية → تحقق → GULA" tone="success" /></ListCard>;
}

function DemoOperatingRoom() {
  return <ListCard title="غرفة العمليات الاصطناعية" description="مسار القرار والتحقق والـchecklist معروض دون جدولة أو موافقة أو تنفيذ جراحي."><QueueRow label="08:00 · إجراء اصطناعي A" value="Consent · Pre-op · Team ✓" tone="success" /><QueueRow label="10:30 · إجراء اصطناعي B" value="Consent معلقة · لا يسمح بالتقدم" tone="warning" /><QueueRow label="Verification" value="Patient + Procedure + Site + Consent + OR" tone="critical" /><QueueRow label="الفريق" value="Surgeon · Anesthetist · Nurse · Technician" tone="info" /></ListCard>;
}

function DemoBloodBank() {
  return <ListCard title="بنك الدم الاصطناعي" description="المخزون والتتبع وcrossmatch والتفاعل معروضة للشرح؛ لا إصدار أو إعطاء أو نقل دم."><QueueRow label="RBC / Plasma / Platelets" value="مخزون اصطناعي · الصلاحية محكومة" tone="info" /><QueueRow label="Crossmatch" value="Patient + Sample + Product + Verification" tone="warning" /><QueueRow label="Two-person verification" value="مطلوب حسب سياسة المؤسسة" tone="critical" /><QueueRow label="Blood reaction" value="Stop protocol · care · investigation · audit" tone="success" /></ListCard>;
}

function DemoPathology() {
  return <ListCard title="المرضيات وتتبع العينات الاصطناعي" description="دورة العينة والتقرير المؤجل معروضة دون specimen حقيقي أو barcode أو تقرير قابل للإصدار."><QueueRow label="Specimen SYN-001" value="Collected → Labeled → Received" tone="info" /><QueueRow label="Specimen SYN-002" value="Processing → Pending" tone="warning" /><QueueRow label="Pathology report" value="Draft · Verification مطلوبة" tone="critical" /><QueueRow label="Pending result" value="مسؤول سريري بعد الخروج · متابعة مطلوبة" tone="success" /></ListCard>;
}

function DemoInfectionControl() {
  return <ListCard title="مكافحة العدوى الاصطناعية" description="Exposure وisolation وclusters للشرح فقط؛ لا كشف لهوية المرضى أو الموظفين لكل العاملين."><QueueRow label="Exposure SYN-01" value="منطقة اصطناعية · نافذة زمنية محددة" tone="warning" /><QueueRow label="Isolation" value="سياسة محلية · قرار مهني مطلوب" tone="critical" /><QueueRow label="Cluster signal" value="Detection → Investigation → Case definition" tone="info" /><QueueRow label="Purpose-based access" value="أدنى إفصاح · نطاق موقع · تدقيق" tone="success" /></ListCard>;
}

function DemoHandover() {
  return <ListCard title="التسليم والتحويل الاصطناعي" description="لا يكتمل النقل دون قبول الفريق المستلم وتوثيق الهوية والعلامات والمهام والنتائج المعلقة."><QueueRow label="Emergency → ICU" value="ICU acceptance مطلوب قبل النقل" tone="critical" /><QueueRow label="Transfer checklist" value="Identity · Vitals · Medication · Lines · Devices" tone="info" /><QueueRow label="Pending results" value="مسؤولية واضحة بعد التحويل" tone="warning" /><QueueRow label="Handover" value="مخاطر · خطة · مهام · receiving team" tone="success" /></ListCard>;
}

function DemoAudit() {
  return <ListCard title="حوكمة الرعاية الحادة الاصطناعية" description="أحداث توضيحية دون هوية أو سجل نشاط حي؛ كل عملية حساسة في الواقع تحتاج audit append-only قابل للمراجعة."><QueueRow label="Triage reassessment" value="Old + New + Reason + Actor + Timestamp" tone="info" /><QueueRow label="Critical alert" value="Acknowledgment منفصل عن الإجراء" tone="warning" /><QueueRow label="Temporary identity" value="سبب + أدلة + مراجعة قبل الربط" tone="critical" /><QueueRow label="System health" value="منفصل عن Clinical health" tone="success" /></ListCard>;
}

function LiveOverview({ contextReady, loading, error, patients, orders, onTab }: { contextReady: boolean; loading: boolean; error: unknown; patients?: ClinicalPatientRead[]; orders?: ClinicalOrderRead[]; onTab: (tab: AcuteCareTab) => void }) {
  return <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(300px,0.8fr)]"><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Activity className="h-5 w-5 text-indigo-600" />ملخص الرعاية الحادة الحي</CardTitle><p className="mt-1 text-xs text-muted-foreground">قراءة محدودة من canonical clinical gateway بعد تفعيل السياق؛ لا Dispatch أو Triage أو ICU أو Blood Bank أو كتابة.</p></CardHeader><CardContent>{!contextReady ? <GatedPanel title="فعّل سياق الرعاية الحادة أولاً" description="لا يتم تحميل المرضى والطلبات قبل workspace خادمي صالح." /> : loading ? <LoadingMessage text="جارٍ تحميل القراءة السريرية…" /> : error ? <GatedPanel title="أوقفنا القراءة السريرية" description="فشل عقد واحد؛ لم نستخدم Demo أو fallback قديم." /> : <div className="grid gap-3 sm:grid-cols-2"><InfoBox label="مرضى ضمن النطاق" value={String(patients?.length ?? 0)} /><InfoBox label="أوامر ضمن النطاق" value={String(orders?.length ?? 0)} /><InfoBox label="الإسعاف وDispatch" value="محجوب" /><InfoBox label="ICU / OR / دم" value="محجوب" /></div>}</CardContent></Card><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><LockKeyhole className="h-5 w-5 text-amber-600" />حدود المسار الحي</CardTitle></CardHeader><CardContent className="space-y-3"><GatedLine label="الطوارئ والفرز وBreak-Glass" onClick={() => onTab("emergency")} /><GatedLine label="الإسعاف وPre-hospital" onClick={() => onTab("ambulance")} /><GatedLine label="ICU وOR والدم والخروج" onClick={() => onTab("critical-care")} /></CardContent></Card></div>;
}

function LivePatients({ contextReady, loading, error, patients }: { contextReady: boolean; loading: boolean; error: unknown; patients?: ClinicalPatientRead[] }) {
  return <ListCard title="المرضى ضمن نطاق الرعاية الحادة" description="تأتي القراءة من canonical clinical gateway وتُرفض الاستجابة إذا احتوت حقولاً حساسة غير مسموحة.">{!contextReady ? <GatedPanel title="فعّل السياق أولاً" description="Patient Access يتطلب Identity + Role + Organization + Care Context + Purpose." /> : loading ? <LoadingMessage text="جارٍ تحميل المرضى…" /> : error ? <GatedPanel title="تعذر قراءة المرضى" description="لم يتم استخدام Demo كبديل." /> : patients?.length ? patients.map((patient) => <div key={patient.id} className="flex items-center gap-3 rounded-xl border p-4"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300"><Users className="h-5 w-5" /></span><div><p className="font-semibold">{patient.display_name}</p><p className="mt-1 text-xs text-muted-foreground">ضمن سياق الرعاية · لا يعرض الهاتف أو الرقم الوطني</p></div></div>) : <EmptyMessage text="لا يوجد مريض ضمن السياق الحالي." />}</ListCard>;
}

function LiveOrders({ contextReady, loading, error, orders }: { contextReady: boolean; loading: boolean; error: unknown; orders?: ClinicalOrderRead[] }) {
  return <ListCard title="الأوامر ضمن نطاق الرعاية الحادة" description="قراءة فقط؛ لا تنفيذ أو إعطاء دواء أو إدخال نتيجة أو تغيير حالة من هذه الصفحة.">{!contextReady ? <GatedPanel title="فعّل السياق أولاً" description="Order Access يتطلب Clinical Context وAuthorization." /> : loading ? <LoadingMessage text="جارٍ تحميل الأوامر…" /> : error ? <GatedPanel title="تعذر قراءة الأوامر" description="لم يتم استخدام Demo كبديل." /> : orders?.length ? orders.map((order) => <div key={order.id} className="flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">{order.patient_display_name ?? "مريض ضمن النطاق"}</p><p className="mt-1 text-xs text-muted-foreground">{order.test_count} عناصر · {order.practitioner_display_name ?? "ممارس ضمن السياق"}</p></div><Badge variant="outline">{order.status}</Badge></div>) : <EmptyMessage text="لا يوجد أمر ضمن السياق الحالي." />}</ListCard>;
}

function WorkspaceCard({ workspace, selected, switching, onSelect }: { workspace: WorkspaceSummary; selected: boolean; switching: boolean; onSelect: () => void }) {
  const active = isActiveWorkspace(workspace);
  return <div className={`rounded-xl border p-4 transition ${selected ? "border-rose-400 bg-rose-50/60 dark:border-rose-700 dark:bg-rose-950/20" : "border-slate-200/80 dark:border-white/10"}`}><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><p className="text-sm font-bold">{workspace.name_ar ?? workspace.name}</p><p className="mt-1 text-xs text-muted-foreground">{workspace.facility_id ?? "منشأة غير معروضة"} · {workspace.department_id ?? "قسم غير معروض"}</p></div><div className="flex items-center gap-2"><Badge variant={active ? "success" : "outline"}>{workspace.status}</Badge><Button type="button" size="sm" variant={selected ? "secondary" : "outline"} disabled={!active || selected || switching} onClick={onSelect}>{switching ? "جارٍ التفعيل…" : selected ? "السياق الحالي" : "تفعيل السياق"}</Button></div></div></div>;
}

function ListCard({ title, description, children }: { title: string; description: string; children: ReactNode }) {
  return <Card><CardHeader><CardTitle>{title}</CardTitle><p className="mt-1 text-xs text-muted-foreground">{description}</p></CardHeader><CardContent className="space-y-3">{children}</CardContent></Card>;
}

function QueueRow({ label, value, tone }: { label: string; value: string; tone: Tone }) {
  const classes: Record<Tone, string> = { critical: "border-red-200 bg-red-50/70 dark:border-red-900/50 dark:bg-red-950/20", warning: "border-amber-200 bg-amber-50/70 dark:border-amber-900/50 dark:bg-amber-950/20", success: "border-emerald-200 bg-emerald-50/70 dark:border-emerald-900/50 dark:bg-emerald-950/20", info: "border-sky-200 bg-sky-50/70 dark:border-sky-900/50 dark:bg-sky-950/20", muted: "border-slate-200 bg-slate-50/70 dark:border-white/10 dark:bg-white/5" };
  return <div className={`flex items-center justify-between gap-3 rounded-xl border p-4 ${classes[tone]}`}><span className="text-sm font-semibold">{label}</span><span className="text-sm text-muted-foreground">{value}</span></div>;
}

function GatedPanel({ title, description }: { title: string; description: string }) {
  return <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-5 text-sm leading-7 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200"><LockKeyhole className="ml-2 inline h-4 w-4" /><strong>{title}</strong><p className="mt-2 text-xs leading-6 opacity-80">{description}</p></div>;
}

function GatedLine({ label, onClick }: { label: string; onClick: () => void }) {
  return <button type="button" onClick={onClick} className="flex w-full items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50/60 p-3 text-right text-sm text-amber-950 transition hover:border-amber-300 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200"><span>{label}</span><LockKeyhole className="h-4 w-4" /></button>;
}

function DemoBoundary() {
  return <Boundary><p><strong>حدود Demo:</strong> كل البيانات اصطناعية للعرض. لا تسجيل بلاغ أو مريض أو هوية مؤقتة حقيقية، ولا Dispatch أو Triage أو ePCR أو دواء أو ICU أو عملية أو دم أو مرضيات أو مكافحة عدوى أو نقل أو تدقيق حي.</p></Boundary>;
}

function LiveBoundary() {
  return <Boundary><p><strong>حدود Live الحالية:</strong> القراءة تقتصر على المرضى والأوامر بعد تفعيل سياق المنشأة. الطوارئ والإسعاف والرعاية قبل المستشفى والعناية والعمليات والدم والمرضيات والعدوى والتسليم والتدقيق تبقى محجوبة حتى عقودها.</p></Boundary>;
}

function Boundary({ children }: { children: ReactNode }) {
  return <Card className="border-indigo-200 bg-indigo-50/60 dark:border-indigo-900/50 dark:bg-indigo-950/20"><CardContent className="flex items-start gap-3 p-5 text-sm leading-7"><Info className="mt-1 h-5 w-5 shrink-0 text-indigo-700 dark:text-indigo-400" />{children}</CardContent></Card>;
}

function InfoBox({ label, value }: { label: string; value: string }) {
  return <div className="rounded-xl border bg-muted/30 p-4"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 text-sm font-semibold leading-6">{value}</p></div>;
}

function LoadingMessage({ text }: { text: string }) {
  return <div className="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">{text}</div>;
}

function EmptyMessage({ text }: { text: string }) {
  return <div className="rounded-xl border border-dashed p-8 text-center text-sm text-muted-foreground">{text}</div>;
}

export { DemoAcuteCareWorkspace };
