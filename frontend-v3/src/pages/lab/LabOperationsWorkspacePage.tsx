import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  Beaker,
  ChevronLeft,
  ClipboardCheck,
  Database,
  FileCheck2,
  FlaskConical,
  Gauge,
  History,
  Info,
  LockKeyhole,
  Microscope,
  PackageCheck,
  RefreshCw,
  Search,
  ShieldCheck,
  TestTube2,
  Truck,
  type LucideIcon,
} from "lucide-react";
import { apiClient, type WorkspaceSummary } from "@/api/client";
import { workspaceScopedReads, type ClinicalOrderRead } from "@/api/workspaceScopedReads";
import { useAuth } from "@/contexts/AuthContext";
import { PageHeader } from "@/components/shared/PageComponents";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type LabTab = "overview" | "samples" | "results" | "analyzers" | "quality";
type SampleState = "مستلمة" | "قيد الفحص" | "مكتملة" | "مرفوضة";
type ResultState = "مبدئية" | "متحقق منها" | "حرجة";

type SampleRecord = {
  id: number;
  accession: string;
  patient: string;
  test: string;
  specimen: string;
  state: SampleState;
  priority: "عادي" | "عاجل";
  collectedAt: string;
  location: string;
};

type ResultRecord = {
  id: number;
  accession: string;
  patient: string;
  test: string;
  value: string;
  reference: string;
  state: ResultState;
  instrument: string;
  issuedAt: string;
};

type AnalyzerRecord = {
  id: number;
  name: string;
  category: string;
  protocol: "ASTM" | "HL7" | "CSV";
  state: "متصل" | "متدهور" | "غير متصل";
  testsToday: number;
  lastSync: string;
};

type QualityRecord = {
  id: number;
  analyte: string;
  lot: string;
  level: string;
  measured: string;
  target: string;
  state: "مطابق" | "يحتاج مراجعة";
};

const INITIAL_SAMPLES: SampleRecord[] = [
  { id: 1, accession: "ACC-260814-0018", patient: "سارة عبد الرحمن", test: "HbA1c", specimen: "دم كامل EDTA", state: "قيد الفحص", priority: "عاجل", collectedAt: "08:42", location: "محطة الاستلام 1" },
  { id: 2, accession: "ACC-260814-0021", patient: "علي كريم حسن", test: "CBC", specimen: "دم كامل EDTA", state: "مستلمة", priority: "عادي", collectedAt: "09:05", location: "الثلاجة A-02" },
  { id: 3, accession: "ACC-260814-0025", patient: "مريم فاضل", test: "TSH", specimen: "مصل", state: "مكتملة", priority: "عادي", collectedAt: "09:12", location: "الأرشيف B-04" },
  { id: 4, accession: "ACC-260814-0030", patient: "حسن نوري", test: "Troponin I", specimen: "مصل", state: "مرفوضة", priority: "عاجل", collectedAt: "09:18", location: "منطقة الرفض" },
];

const INITIAL_RESULTS: ResultRecord[] = [
  { id: 1, accession: "ACC-260814-0018", patient: "سارة عبد الرحمن", test: "HbA1c", value: "7.8 %", reference: "4.0–5.6 %", state: "مبدئية", instrument: "Cobas c311", issuedAt: "09:24" },
  { id: 2, accession: "ACC-260814-0025", patient: "مريم فاضل", test: "TSH", value: "2.14 mIU/L", reference: "0.4–4.0", state: "متحقق منها", instrument: "Architect i2000", issuedAt: "09:28" },
  { id: 3, accession: "ACC-260814-0030", patient: "حسن نوري", test: "Troponin I", value: "0.88 ng/mL", reference: "< 0.04", state: "حرجة", instrument: "Alinity ci", issuedAt: "09:31" },
];

const ANALYZERS: AnalyzerRecord[] = [
  { id: 1, name: "Cobas c311", category: "كيمياء سريرية", protocol: "ASTM", state: "متصل", testsToday: 86, lastSync: "منذ دقيقتين" },
  { id: 2, name: "Architect i2000", category: "مناعة", protocol: "HL7", state: "متصل", testsToday: 54, lastSync: "منذ 4 دقائق" },
  { id: 3, name: "Alinity ci", category: "كيمياء ومناعة", protocol: "CSV", state: "متدهور", testsToday: 31, lastSync: "منذ 18 دقيقة" },
  { id: 4, name: "Sysmex XN-1000", category: "أمراض الدم", protocol: "HL7", state: "غير متصل", testsToday: 0, lastSync: "منذ 47 دقيقة" },
];

const QUALITY_RECORDS: QualityRecord[] = [
  { id: 1, analyte: "Glucose", lot: "QC-GLU-26A", level: "Level 1", measured: "98 mg/dL", target: "100 ± 8", state: "مطابق" },
  { id: 2, analyte: "Hemoglobin", lot: "QC-HGB-14B", level: "Level 2", measured: "12.1 g/dL", target: "12.0 ± 0.6", state: "مطابق" },
  { id: 3, analyte: "TSH", lot: "QC-TSH-09C", level: "Level 2", measured: "5.9 mIU/L", target: "4.0 ± 0.5", state: "يحتاج مراجعة" },
];

const TABS: Array<{ id: LabTab; label: string; icon: LucideIcon }> = [
  { id: "overview", label: "نظرة المختبر", icon: Gauge },
  { id: "samples", label: "العينات", icon: TestTube2 },
  { id: "results", label: "النتائج", icon: FileCheck2 },
  { id: "analyzers", label: "المحللات", icon: Microscope },
  { id: "quality", label: "ضبط الجودة", icon: ClipboardCheck },
];

const sampleVariant = (state: SampleState): "success" | "warning" | "destructive" | "outline" => state === "مكتملة" ? "success" : state === "قيد الفحص" ? "warning" : state === "مرفوضة" ? "destructive" : "outline";
const resultVariant = (state: ResultState): "success" | "warning" | "destructive" => state === "متحقق منها" ? "success" : state === "حرجة" ? "destructive" : "warning";
const analyzerVariant = (state: AnalyzerRecord["state"]): "success" | "warning" | "destructive" => state === "متصل" ? "success" : state === "متدهور" ? "warning" : "destructive";

function isActiveWorkspace(workspace: WorkspaceSummary) {
  return ["active", "verified", "approved"].includes(workspace.status.toLowerCase());
}

export function LabOperationsWorkspacePage() {
  const { demoMode } = useAuth();
  return demoMode ? <LabDemoWorkspace /> : <LiveLabWorkspace />;
}

function LabDemoWorkspace() {
  const [activeTab, setActiveTab] = useState<LabTab>("overview");
  const [selectedSampleId, setSelectedSampleId] = useState(INITIAL_SAMPLES[0]?.id ?? 1);
  const [sampleSearch, setSampleSearch] = useState("");
  const [resultSearch, setResultSearch] = useState("");
  const filteredSamples = useMemo(() => filterSamples(INITIAL_SAMPLES, sampleSearch), [sampleSearch]);
  const filteredResults = useMemo(() => filterResults(INITIAL_RESULTS, resultSearch), [resultSearch]);
  const selectedSample = INITIAL_SAMPLES.find((sample) => sample.id === selectedSampleId) ?? INITIAL_SAMPLES[0];
  const criticalCount = INITIAL_RESULTS.filter((result) => result.state === "حرجة").length;
  const pendingResults = INITIAL_RESULTS.filter((result) => result.state === "مبدئية").length;
  const connectedAnalyzers = ANALYZERS.filter((analyzer) => analyzer.state === "متصل").length;

  return <div className="mx-auto max-w-7xl space-y-6" dir="rtl">
    <LabHero demoMode />
    <MetricGrid metrics={[
      ["العينات النشطة", String(INITIAL_SAMPLES.filter((sample) => sample.state !== "مكتملة" && sample.state !== "مرفوضة").length), TestTube2],
      ["نتائج بانتظار التحقق", String(pendingResults), FileCheck2],
      ["تنبيهات حرجة", String(criticalCount), AlertTriangle],
      ["محللات متصلة", `${connectedAnalyzers}/${ANALYZERS.length}`, Microscope],
    ]} />
    <LabTabs activeTab={activeTab} onChange={setActiveTab} />
    {activeTab === "overview" && <DemoOverview onTab={setActiveTab} />}
    {activeTab === "samples" && <SamplesBoard samples={filteredSamples} selectedSample={selectedSample} search={sampleSearch} onSearch={setSampleSearch} onSelect={setSelectedSampleId} />}
    {activeTab === "results" && <ResultsBoard results={filteredResults} search={resultSearch} onSearch={setResultSearch} />}
    {activeTab === "analyzers" && <AnalyzersBoard analyzers={ANALYZERS} />}
    {activeTab === "quality" && <QualityBoard records={QUALITY_RECORDS} />}
    <DemoBoundary />
  </div>;
}

function LiveLabWorkspace() {
  const [activeTab, setActiveTab] = useState<LabTab>("overview");
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string | null>(null);
  const [switchingWorkspaceId, setSwitchingWorkspaceId] = useState<string | null>(null);
  const [switchError, setSwitchError] = useState("");
  const workspacesQuery = useQuery({ queryKey: ["lab-workspaces", "me"], queryFn: () => apiClient.listWorkspaces(), retry: false, staleTime: 30_000 });
  const labWorkspaces = (workspacesQuery.data?.workspaces ?? []).filter((workspace) => !workspace.is_personal && Boolean(workspace.facility_id));
  const selectedWorkspace = labWorkspaces.find((workspace) => workspace.id === selectedWorkspaceId);
  const ordersQuery = useQuery({
    queryKey: ["lab-orders", selectedWorkspaceId],
    queryFn: () => workspaceScopedReads.listOrders({ limit: 50 }),
    enabled: Boolean(selectedWorkspaceId && selectedWorkspace && isActiveWorkspace(selectedWorkspace)),
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
      setSwitchError(error instanceof Error ? error.message : "تعذر تفعيل سياق المختبر.");
    } finally {
      setSwitchingWorkspaceId(null);
    }
  };

  return <div className="mx-auto max-w-7xl space-y-6" dir="rtl">
    <LabHero demoMode={false} />
    <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70"><CardHeader><CardTitle className="flex items-center gap-2 text-base"><ShieldCheck className="h-5 w-5 text-teal-600" />سياق المختبر المؤسسي</CardTitle><p className="mt-1 text-xs text-muted-foreground">لا تبدأ قراءات LIS قبل أن يعيد الخادم مساحة منشأة مؤهلة ويثبت سياق المؤسسة والعضوية.</p></CardHeader><CardContent className="space-y-3">{workspacesQuery.isLoading ? <div className="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">جارٍ تحميل مساحات المختبر…</div> : labWorkspaces.length === 0 ? <GatedPanel title="لا توجد مساحة مختبر مؤكدة" description="تحتاج القراءة الحية إلى Professional Verification وMembership وFacility Context معاد من الخادم." /> : labWorkspaces.map((workspace) => <WorkspaceCard key={workspace.id} workspace={workspace} selected={workspace.id === selectedWorkspaceId} switching={switchingWorkspaceId === workspace.id} onSelect={() => void activateWorkspace(workspace)} />)}{switchError && <p className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/20 dark:text-rose-200" role="alert">{switchError}</p>}{workspacesQuery.error && <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200" role="alert">تعذر قراءة مساحات المختبر من الخادم.</p>}</CardContent></Card>
    <MetricGrid metrics={[
      ["طلبات ضمن السياق", ordersQuery.data ? String(ordersQuery.data.length) : "—", ClipboardCheck],
      ["العينات", "محجوبة", TestTube2],
      ["النتائج", "محجوبة", FileCheck2],
      ["ضبط الجودة", "محجوب", ShieldCheck],
    ]} />
    <LabTabs activeTab={activeTab} onChange={setActiveTab} />
    {activeTab === "overview" && <LiveOverview orders={ordersQuery.data ?? []} loading={ordersQuery.isLoading} error={ordersQuery.error} selectedWorkspace={selectedWorkspace} onTab={setActiveTab} />}
    {activeTab === "samples" && <GatedPanel title="عقد قراءة العينات غير مفعّل" description="لا تستخدم الواجهة legacy samples أو بيانات محلية في Live. يلزم عقد Specimen/Accession مقيد بالمؤسسة والمنشأة مع chain-of-custody وتدقيق." />}
    {activeTab === "results" && <GatedPanel title="عقد قراءة النتائج غير مفعّل" description="النتائج والـDiagnosticReport لا تُعرض قبل عقد خادمي يفرض العلاقة العلاجية، حالة Release، تقليل الإفصاح، والنسخ/التصحيحات." />}
    {activeTab === "analyzers" && <GatedPanel title="عقد المحللات والتكامل غير مفعّل" description="لا يتصل Analyzer بقاعدة البيانات مباشرة. يلزم Integration Gateway وmapping وidempotency وQC وcalibration قبل عرض بيانات حية." />}
    {activeTab === "quality" && <GatedPanel title="عقد الجودة غير مفعّل" description="QC وCalibration وMaintenance وCAPA تحتاج domain خادمياً مستقلاً مع صلاحيات المختبر وسجل تدقيق." />}
    {ordersQuery.error && <div className="rounded-2xl border border-amber-200 bg-amber-50/70 p-5 text-sm leading-7 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200" role="status"><LockKeyhole className="ml-2 inline h-4 w-4" />تم إيقاف قراءة الطلبات بأمان؛ لم يتم استخدام fallback قديم.</div>}
    <LiveBoundary />
  </div>;
}

function LabHero({ demoMode }: { demoMode: boolean }) {
  return <><PageHeader title="إدارة المختبر" description="مساحة GULA لدورة الطلب والعينة والنتيجة والمحلل وضبط الجودة، مع فصل واضح بين العرض التجريبي والعقود السريرية الحية." /><Card className="overflow-hidden border-teal-200 bg-gradient-to-l from-teal-50 via-white to-sky-50 dark:border-teal-900/50 dark:from-teal-950/30 dark:via-background dark:to-sky-950/30"><CardContent className="p-6"><div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between"><div className="max-w-3xl space-y-3"><div className="flex items-center gap-2 text-teal-700 dark:text-teal-300"><FlaskConical className="h-5 w-5" /><span className="text-sm font-semibold">Laboratory Operations Core</span></div><h2 className="text-2xl font-bold tracking-tight">من الاستلام إلى نتيجة موثوقة</h2><p className="text-sm leading-7 text-muted-foreground">تجميع أصلي لسير العمل: accession، سلسلة الحيازة، الفحص، التحقق، القيم الحرجة، تكامل المحللات، وضبط الجودة.</p><div className="flex flex-wrap gap-2"><Badge variant={demoMode ? "success" : "outline"}><ShieldCheck className="ml-1 h-3.5 w-3.5" />{demoMode ? "عرض اصطناعي معزول" : "سياق خادمي مطلوب"}</Badge><Badge variant="outline"><Database className="ml-1 h-3.5 w-3.5" />FHIR-ready</Badge><Badge variant="outline"><Truck className="ml-1 h-3.5 w-3.5" />Chain of custody</Badge></div></div>{demoMode && <div className="grid min-w-[290px] grid-cols-2 gap-3"><Metric label="طلبات اليوم" value="11" icon={ClipboardCheck} /><Metric label="حالات حرجة" value="2" icon={AlertTriangle} /><Metric label="QC Holds" value="1" icon={ShieldCheck} /><Metric label="TAT Breaches" value="6" icon={Gauge} /></div>}</div></CardContent></Card></>;
}

function MetricGrid({ metrics }: { metrics: Array<[string, string, LucideIcon]> }) {
  return <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="مؤشرات المختبر">{metrics.map(([label, value, Icon]) => <Card key={label} className="overflow-hidden rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70"><CardContent className="relative p-5"><div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-l from-teal-500 to-sky-400" /><div className="flex items-start justify-between gap-3"><span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200"><Icon className="h-5 w-5" /></span><Badge variant="outline">{value === "—" ? "محجوب" : "حالة"}</Badge></div><p className="mt-5 text-sm text-muted-foreground">{label}</p><p className="mt-1 text-3xl font-bold tracking-tight text-[#0F172A] dark:text-white">{value}</p></CardContent></Card>)}</section>;
}

function Metric({ label, value, icon: Icon }: { label: string; value: string; icon: LucideIcon }) { return <div className="rounded-xl bg-background/80 p-4 shadow-sm"><div className="flex items-center justify-between gap-2"><p className="text-xs text-muted-foreground">{label}</p><Icon className="h-4 w-4 text-teal-600" /></div><p className="mt-1 text-2xl font-bold">{value}</p></div>; }

function LabTabs({ activeTab, onChange }: { activeTab: LabTab; onChange: (tab: LabTab) => void }) { return <Card><CardContent className="p-0"><div className="flex flex-wrap border-b">{TABS.map(({ id, label, icon: Icon }) => <button key={id} type="button" onClick={() => onChange(id)} aria-selected={activeTab === id} className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 ${activeTab === id ? "border-b-2 border-teal-600 text-teal-700 dark:text-teal-300" : "text-muted-foreground hover:text-foreground"}`}><Icon className="h-4 w-4" />{label}</button>)}</div></CardContent></Card>; }

function DemoOverview({ onTab }: { onTab: (tab: LabTab) => void }) {
  const steps: Array<{ label: string; value: string; icon: LucideIcon; tab: LabTab }> = [
    { label: "استلام وتسجيل العينة", value: "3 عينات ضمن المسار", icon: PackageCheck, tab: "samples" },
    { label: "الفحص والنتائج المبدئية", value: "1 نتيجة بانتظار التحقق", icon: Beaker, tab: "results" },
    { label: "التحقق والتنبيه", value: "1 قيمة حرجة للشرح", icon: AlertTriangle, tab: "results" },
    { label: "اتصال المحللات", value: "2/4 متصل للشرح", icon: RefreshCw, tab: "analyzers" },
  ];
  return <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(300px,0.8fr)]"><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Activity className="h-5 w-5 text-teal-600" />مسار العمل التجريبي</CardTitle></CardHeader><CardContent className="space-y-3">{steps.map((step, index) => { const Icon = step.icon; return <button key={step.label} type="button" onClick={() => onTab(step.tab)} className="flex w-full items-center gap-3 rounded-xl border p-4 text-right transition hover:border-teal-300 hover:bg-teal-50/40 dark:hover:bg-teal-950/20"><span className="flex h-9 w-9 items-center justify-center rounded-full bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300">{index + 1}</span><span className="flex-1"><span className="block font-semibold">{step.label}</span><span className="mt-1 block text-xs text-muted-foreground">{step.value}</span></span><Icon className="h-4 w-4 text-teal-600" /><ChevronLeft className="h-4 w-4 text-muted-foreground" /></button>; })}</CardContent></Card><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><AlertTriangle className="h-5 w-5 text-amber-600" />يحتاج انتباهاً في السيناريو</CardTitle></CardHeader><CardContent className="space-y-3"><AlertRow title="نتيجة Troponin I حرجة" detail="مثال اصطناعي · تحتاج مراجعة مشرف" tone="critical" /><AlertRow title="محلل Sysmex غير متصل" detail="مثال اصطناعي · آخر مزامنة منذ 47 دقيقة" tone="warning" /><AlertRow title="TSH خارج نطاق QC" detail="مثال اصطناعي · Level 2" tone="warning" /><Link to="/alerts" className="mt-2 inline-flex items-center gap-2 text-sm font-medium text-teal-700 hover:underline dark:text-teal-300">فتح التنبيهات <ArrowLeft className="h-4 w-4" /></Link></CardContent></Card></div>;
}

function LiveOverview({ orders, loading, error, selectedWorkspace, onTab }: { orders: ClinicalOrderRead[]; loading: boolean; error: unknown; selectedWorkspace?: WorkspaceSummary; onTab: (tab: LabTab) => void }) {
  return <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(300px,0.8fr)]"><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><ClipboardCheck className="h-5 w-5 text-teal-600" />طلبات ضمن السياق</CardTitle><p className="mt-1 text-xs text-muted-foreground">{selectedWorkspace ? "قراءة محدودة من clinical gateway؛ لا تعرض النتائج ولا تنشئ عينة." : "فعّل سياق مختبر من الخادم أولاً."}</p></CardHeader><CardContent>{loading ? <div className="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">جارٍ التحقق من سياق الطلبات…</div> : error ? <GatedPanel title="قراءة الطلبات موقوفة بأمان" description="رفضت البوابة القراءة أو تعذر الاتصال؛ لم يتم استخدام fallback legacy." /> : orders.length ? <div className="space-y-2">{orders.slice(0, 8).map((order) => <div key={order.id} className="flex items-center justify-between gap-3 rounded-xl border border-slate-200/80 p-3 dark:border-white/10"><div><p className="text-sm font-semibold">طلب ضمن النطاق</p><p className="mt-1 text-xs text-muted-foreground">{order.status} · {order.test_count} فحوصات · {formatDate(order.created_at)}</p></div><Badge variant="outline">لا نتائج</Badge></div>)}</div> : <div className="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">لا توجد طلبات ضمن السياق الحالي.</div>}</CardContent></Card><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><LockKeyhole className="h-5 w-5 text-amber-600" />العقود التالية</CardTitle></CardHeader><CardContent className="space-y-3"><GatedLine label="Specimen / Accession" onClick={() => onTab("samples")} /><GatedLine label="Observation / DiagnosticReport" onClick={() => onTab("results")} /><GatedLine label="Analyzer Gateway / Mapping" onClick={() => onTab("analyzers")} /><GatedLine label="QC / Calibration / CAPA" onClick={() => onTab("quality")} /></CardContent></Card></div>;
}

function GatedLine({ label, onClick }: { label: string; onClick: () => void }) { return <button type="button" onClick={onClick} className="flex w-full items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50/60 p-3 text-right text-sm text-amber-950 transition hover:border-amber-300 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200"><span>{label}</span><LockKeyhole className="h-4 w-4" /></button>; }

function SamplesBoard({ samples, selectedSample, search, onSearch, onSelect }: { samples: SampleRecord[]; selectedSample?: SampleRecord; search: string; onSearch: (value: string) => void; onSelect: (id: number) => void }) { return <div className="grid gap-4 xl:grid-cols-[minmax(0,1.35fr)_minmax(300px,0.75fr)]"><Card><CardHeader><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><CardTitle className="text-base">العينات والوصولات</CardTitle><p className="mt-1 text-xs text-muted-foreground">عرض اصطناعي لسلسلة accession والعينة والموقع والأولوية.</p></div><div className="relative w-full sm:w-80"><Search className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" /><Input value={search} onChange={(event) => onSearch(event.target.value)} placeholder="ابحث بالوصول أو المريض..." className="pr-9" /></div></div></CardHeader><CardContent className="space-y-2">{samples.map((sample) => <button key={sample.id} type="button" onClick={() => onSelect(sample.id)} className={`w-full rounded-xl border p-4 text-right transition hover:border-teal-300 ${selectedSample?.id === sample.id ? "border-teal-400 bg-teal-50/60 dark:border-teal-700 dark:bg-teal-950/25" : "border-border"}`}><div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">{sample.accession} · {sample.patient}</p><p className="mt-1 text-xs text-muted-foreground">{sample.test} · {sample.specimen} · {sample.location}</p></div><div className="flex items-center gap-2"><Badge variant={sample.priority === "عاجل" ? "warning" : "outline"}>{sample.priority}</Badge><Badge variant={sampleVariant(sample.state)}>{sample.state}</Badge></div></div><div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground"><span>جمع {sample.collectedAt}</span><span>محطة الحيازة: {sample.location}</span></div></button>)}{samples.length === 0 && <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">لا توجد عينة مطابقة.</div>}</CardContent></Card><SampleDetail sample={selectedSample} /></div>; }

function SampleDetail({ sample }: { sample?: SampleRecord }) { if (!sample) return <Card><CardContent className="p-8 text-center text-sm text-muted-foreground">اختر عينة لعرض سلسلة الحيازة.</CardContent></Card>; return <Card><CardHeader><CardTitle className="text-base">سلسلة حيازة العينة</CardTitle><p className="mt-1 text-sm text-muted-foreground">{sample.accession}</p></CardHeader><CardContent className="space-y-4"><div><p className="text-lg font-bold">{sample.patient}</p><p className="mt-1 text-sm text-muted-foreground">{sample.test} · {sample.specimen}</p></div><div className="space-y-3">{[{ label: "تم التسجيل", detail: "استلام الطلب وتوليد accession", icon: ClipboardCheck }, { label: "تم الجمع", detail: `الساعة ${sample.collectedAt} · ${sample.location}`, icon: TestTube2 }, { label: "الفحص", detail: sample.state === "قيد الفحص" ? "قيد التنفيذ على المحلل" : "بانتظار الانتقال", icon: Beaker }, { label: "الحالة الحالية", detail: sample.state, icon: History }].map((step, index) => { const Icon = step.icon; return <div key={step.label} className="flex items-start gap-3"><span className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${index < 2 || (index === 2 && sample.state === "قيد الفحص") ? "bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300" : "bg-muted text-muted-foreground"}`}><Icon className="h-4 w-4" /></span><div><p className="text-sm font-semibold">{step.label}</p><p className="mt-0.5 text-xs text-muted-foreground">{step.detail}</p></div></div>; })}</div><p className="text-xs leading-5 text-muted-foreground">هذا سجل اصطناعي للشرح فقط. التنفيذ الفعلي يحتاج actor ووقت الحدث والموقع وسبب الرفض وchain-of-custody خادمية.</p></CardContent></Card>; }

function ResultsBoard({ results, search, onSearch }: { results: ResultRecord[]; search: string; onSearch: (value: string) => void }) { return <Card><CardHeader><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><CardTitle className="text-base">نتائج المختبر</CardTitle><p className="mt-1 text-xs text-muted-foreground">قراءة اصطناعية للقيمة والنطاق المرجعي وحالة التحقق ومصدر الجهاز، دون تعديل أو إصدار.</p></div><div className="relative w-full sm:w-80"><Search className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" /><Input value={search} onChange={(event) => onSearch(event.target.value)} placeholder="ابحث بالوصول أو الفحص..." className="pr-9" /></div></div></CardHeader><CardContent className="space-y-3">{results.map((result) => <div key={result.id} className="rounded-xl border p-4"><div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between"><div><p className="font-semibold">{result.test} · {result.patient}</p><p className="mt-1 text-xs text-muted-foreground">{result.accession} · {result.instrument} · {result.issuedAt}</p></div><Badge variant={resultVariant(result.state)}>{result.state}</Badge></div><div className="mt-4 grid gap-3 sm:grid-cols-3"><ValueBox label="القيمة" value={result.value} /><ValueBox label="النطاق المرجعي" value={result.reference} /><ValueBox label="مصدر النتيجة" value={result.instrument} /></div></div>)}{results.length === 0 && <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">لا توجد نتيجة مطابقة.</div>}</CardContent></Card>; }

function ValueBox({ label, value }: { label: string; value: string }) { return <div className="rounded-lg bg-muted/50 p-3"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 font-semibold">{value}</p></div>; }

function AnalyzersBoard({ analyzers }: { analyzers: AnalyzerRecord[] }) { return <div className="grid gap-4 md:grid-cols-2">{analyzers.map((analyzer) => <Card key={analyzer.id}><CardHeader className="pb-3"><div className="flex items-start justify-between gap-3"><div><CardTitle className="text-base">{analyzer.name}</CardTitle><p className="mt-1 text-sm text-muted-foreground">{analyzer.category}</p></div><Badge variant={analyzerVariant(analyzer.state)}>{analyzer.state}</Badge></div></CardHeader><CardContent className="space-y-4"><div className="grid grid-cols-2 gap-3"><ValueBox label="البروتوكول" value={analyzer.protocol} /><ValueBox label="فحوصات اليوم" value={String(analyzer.testsToday)} /></div><div className="flex items-center gap-2 text-xs text-muted-foreground"><RefreshCw className="h-3.5 w-3.5" />آخر مزامنة: {analyzer.lastSync}</div><p className="text-xs text-muted-foreground">بيانات اصطناعية. التكامل الفعلي يحتاج gateway وmapping وidempotency، ولا يسمح للجهاز بالوصول المباشر إلى قاعدة البيانات.</p></CardContent></Card>)}</div>; }

function QualityBoard({ records }: { records: QualityRecord[] }) { const attention = records.filter((record) => record.state === "يحتاج مراجعة").length; return <div className="space-y-4"><div className="grid gap-3 sm:grid-cols-3"><Card><CardContent className="p-4"><p className="text-xs text-muted-foreground">سجلات QC</p><p className="mt-2 text-2xl font-bold">{records.length}</p></CardContent></Card><Card><CardContent className="p-4"><p className="text-xs text-muted-foreground">مطابقة</p><p className="mt-2 text-2xl font-bold text-teal-700 dark:text-teal-300">{records.length - attention}</p></CardContent></Card><Card><CardContent className="p-4"><p className="text-xs text-muted-foreground">تحتاج مراجعة</p><p className="mt-2 text-2xl font-bold text-amber-700 dark:text-amber-300">{attention}</p></CardContent></Card></div><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><ClipboardCheck className="h-5 w-5 text-teal-600" />ضبط الجودة والتشغيل</CardTitle></CardHeader><CardContent className="space-y-3">{records.map((record) => <div key={record.id} className="flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">{record.analyte} · {record.level}</p><p className="mt-1 text-xs text-muted-foreground">Lot {record.lot} · القيمة {record.measured} · الهدف {record.target}</p></div><Badge variant={record.state === "مطابق" ? "success" : "warning"}>{record.state}</Badge></div>)}</CardContent></Card></div>; }

function WorkspaceCard({ workspace, selected, switching, onSelect }: { workspace: WorkspaceSummary; selected: boolean; switching: boolean; onSelect: () => void }) { const active = isActiveWorkspace(workspace); return <div className={`rounded-xl border p-4 transition ${selected ? "border-teal-400 bg-teal-50/60 dark:border-teal-700 dark:bg-teal-950/20" : "border-slate-200/80 dark:border-white/10"}`}><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div className="flex items-start gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200"><FlaskConical className="h-5 w-5" /></span><div><p className="text-sm font-bold">{workspace.name_ar ?? workspace.name}</p><p className="mt-1 text-xs text-muted-foreground">{workspace.facility_id ?? "منشأة غير معروضة"} · {workspace.department_id ?? "قسم غير معروض"}</p></div></div><div className="flex items-center gap-2"><Badge variant={active ? "success" : "outline"}>{workspace.status}</Badge><Button type="button" size="sm" variant={selected ? "secondary" : "outline"} disabled={!active || selected || switching} onClick={onSelect}>{switching ? <RefreshCw className="h-4 w-4 animate-spin" /> : selected ? "السياق الحالي" : "تفعيل سياق المختبر"}</Button></div></div></div>; }

function GatedPanel({ title, description }: { title: string; description: string }) { return <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-5 text-sm leading-7 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200"><LockKeyhole className="ml-2 inline h-4 w-4" /><strong>{title}</strong><p className="mt-2 text-xs leading-6 opacity-80">{description}</p></div>; }

function DemoBoundary() { return <Card className="border-amber-200 bg-amber-50/60 dark:border-amber-900/50 dark:bg-amber-950/20"><CardContent className="flex items-start gap-3 p-5 text-sm leading-7"><Info className="mt-1 h-5 w-5 shrink-0 text-amber-700 dark:text-amber-400" /><p><strong>حدود Demo:</strong> العينات والنتائج والمحللات وQC اصطناعية للعرض فقط. لا يوجد زر تحقق أو انتقال أو إصدار، ولا يتم إرسال أي نتيجة إلى نظام خارجي.</p></CardContent></Card>; }

function LiveBoundary() { return <Card className="border-amber-200 bg-amber-50/60 dark:border-amber-900/50 dark:bg-amber-950/20"><CardContent className="flex items-start gap-3 p-5 text-sm leading-7"><Info className="mt-1 h-5 w-5 shrink-0 text-amber-700 dark:text-amber-400" /><p><strong>حدود Live الحالية:</strong> قراءة الطلبات فقط عبر clinical gateway بعد اختيار سياق مؤسسي خادمي. لا تُنفذ كتابة عينات أو نتائج أو QC أو تكامل أجهزة أو إشعارات حرجة حتى تكتمل عقود LIS والتدقيق وسير الحالات.</p></CardContent></Card>; }

function AlertRow({ title, detail, tone }: { title: string; detail: string; tone: "critical" | "warning" }) { return <div className={`rounded-xl border p-3 ${tone === "critical" ? "border-red-200 bg-red-50/70 dark:border-red-900/50 dark:bg-red-950/20" : "border-amber-200 bg-amber-50/70 dark:border-amber-900/50 dark:bg-amber-950/20"}`}><div className="flex items-center gap-2"><AlertTriangle className={`h-4 w-4 ${tone === "critical" ? "text-red-600" : "text-amber-600"}`} /><p className="text-sm font-semibold">{title}</p></div><p className="mt-1 text-xs text-muted-foreground">{detail}</p></div>; }

function filterSamples(samples: SampleRecord[], search: string) { const term = search.trim().toLocaleLowerCase("ar"); return term ? samples.filter((sample) => `${sample.accession} ${sample.patient} ${sample.test} ${sample.specimen} ${sample.location}`.toLocaleLowerCase("ar").includes(term)) : samples; }
function filterResults(results: ResultRecord[], search: string) { const term = search.trim().toLocaleLowerCase("ar"); return term ? results.filter((result) => `${result.accession} ${result.patient} ${result.test} ${result.instrument}`.toLocaleLowerCase("ar").includes(term)) : results; }
function formatDate(value?: string | null) { if (!value) return "وقت غير معروض"; const date = new Date(value); return Number.isNaN(date.getTime()) ? value.slice(0, 10) : date.toLocaleDateString("ar-IQ"); }

export default LabOperationsWorkspacePage;
