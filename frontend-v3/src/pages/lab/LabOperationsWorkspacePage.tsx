import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  Beaker,
  CheckCircle2,
  ChevronLeft,
  ClipboardCheck,
  Database,
  FileCheck2,
  FlaskConical,
  Gauge,
  History,
  Info,
  Microscope,
  PackageCheck,
  RefreshCw,
  Search,
  ShieldCheck,
  TestTube2,
  Truck,
} from "lucide-react";
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

const tabs: Array<{ id: LabTab; label: string; icon: typeof FlaskConical }> = [
  { id: "overview", label: "نظرة المختبر", icon: Gauge },
  { id: "samples", label: "العينات", icon: TestTube2 },
  { id: "results", label: "النتائج", icon: FileCheck2 },
  { id: "analyzers", label: "المحللات", icon: Microscope },
  { id: "quality", label: "ضبط الجودة", icon: ClipboardCheck },
];

const sampleVariant = (state: SampleState): "success" | "warning" | "destructive" | "outline" => state === "مكتملة" ? "success" : state === "قيد الفحص" ? "warning" : state === "مرفوضة" ? "destructive" : "outline";
const resultVariant = (state: ResultState): "success" | "warning" | "destructive" => state === "متحقق منها" ? "success" : state === "حرجة" ? "destructive" : "warning";
const analyzerVariant = (state: AnalyzerRecord["state"]): "success" | "warning" | "destructive" => state === "متصل" ? "success" : state === "متدهور" ? "warning" : "destructive";

export function LabOperationsWorkspacePage() {
  const [activeTab, setActiveTab] = useState<LabTab>("overview");
  const [samples, setSamples] = useState(INITIAL_SAMPLES);
  const [results, setResults] = useState(INITIAL_RESULTS);
  const [selectedSampleId, setSelectedSampleId] = useState(INITIAL_SAMPLES[0]?.id ?? 1);
  const [sampleSearch, setSampleSearch] = useState("");
  const [resultSearch, setResultSearch] = useState("");
  const [notice, setNotice] = useState("");

  const filteredSamples = useMemo(() => {
    const term = sampleSearch.trim().toLocaleLowerCase("ar");
    if (!term) return samples;
    return samples.filter((sample) => `${sample.accession} ${sample.patient} ${sample.test} ${sample.specimen} ${sample.location}`.toLocaleLowerCase("ar").includes(term));
  }, [sampleSearch, samples]);

  const filteredResults = useMemo(() => {
    const term = resultSearch.trim().toLocaleLowerCase("ar");
    if (!term) return results;
    return results.filter((result) => `${result.accession} ${result.patient} ${result.test} ${result.instrument}`.toLocaleLowerCase("ar").includes(term));
  }, [resultSearch, results]);

  const selectedSample = samples.find((sample) => sample.id === selectedSampleId) ?? samples[0];
  const criticalCount = results.filter((result) => result.state === "حرجة").length;
  const pendingResults = results.filter((result) => result.state === "مبدئية").length;
  const connectedAnalyzers = ANALYZERS.filter((analyzer) => analyzer.state === "متصل").length;

  const simulateVerify = (resultId: number) => {
    setResults((current) => current.map((result) => result.id === resultId ? { ...result, state: "متحقق منها" } : result));
    setNotice("تمت محاكاة التحقق محليًا؛ لم تُرسل النتيجة إلى أي نظام خارجي.");
  };

  const advanceSample = (sampleId: number) => {
    setSamples((current) => current.map((sample) => sample.id === sampleId && sample.state === "مستلمة" ? { ...sample, state: "قيد الفحص" } : sample));
    setNotice("تمت محاكاة انتقال العينة إلى قيد الفحص محليًا.");
  };

  return (
    <div className="mx-auto max-w-7xl space-y-6" dir="rtl">
      <PageHeader title="إدارة المختبر" description="مساحة GULA الأصلية لدورة الطلب والعينة والنتيجة والمحلل وضبط الجودة، مستلهمة من احتياجات OpenELIS وLIMS العامة دون نسخ الكود." />

      <Card className="overflow-hidden border-teal-200 bg-gradient-to-l from-teal-50 via-white to-sky-50 dark:border-teal-900/50 dark:from-teal-950/30 dark:via-background dark:to-sky-950/30">
        <CardContent className="p-6">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div className="max-w-3xl space-y-3"><div className="flex items-center gap-2 text-teal-700 dark:text-teal-300"><FlaskConical className="h-5 w-5" /><span className="text-sm font-semibold">Laboratory Operations Core</span></div><h2 className="text-2xl font-bold tracking-tight">من الاستلام إلى نتيجة موثوقة</h2><p className="text-sm leading-7 text-muted-foreground">تجميع أصلي لسير العمل الذي تحتاجه GULA: accession، سلسلة الحيازة، الفحص، التحقق، التنبيه الحرج، تكامل المحللات، وضبط الجودة. البيانات اصطناعية ولا تُرسل إلى OpenELIS أو أي نظام خارجي.</p><div className="flex flex-wrap gap-2"><Badge variant="success"><ShieldCheck className="ml-1 h-3.5 w-3.5" />عرض معزول</Badge><Badge variant="outline"><Database className="ml-1 h-3.5 w-3.5" />FHIR-ready</Badge><Badge variant="outline"><Truck className="ml-1 h-3.5 w-3.5" />Chain of custody</Badge></div></div>
            <div className="grid min-w-[290px] grid-cols-2 gap-3"><Metric label="العينات النشطة" value={samples.filter((sample) => sample.state !== "مكتملة" && sample.state !== "مرفوضة").length} icon={TestTube2} /><Metric label="نتائج بانتظار التحقق" value={pendingResults} icon={FileCheck2} /><Metric label="تنبيهات حرجة" value={criticalCount} icon={AlertTriangle} /><Metric label="محللات متصلة" value={connectedAnalyzers} icon={Microscope} /></div>
          </div>
        </CardContent>
      </Card>

      <Card><CardContent className="p-0"><div className="flex flex-wrap border-b">{tabs.map((tab) => { const Icon = tab.icon; return <button key={tab.id} type="button" onClick={() => { setActiveTab(tab.id); setNotice(""); }} className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${activeTab === tab.id ? "border-b-2 border-teal-600 text-teal-700 dark:text-teal-300" : "text-muted-foreground hover:text-foreground"}`}><Icon className="h-4 w-4" />{tab.label}</button>; })}</div></CardContent></Card>

      {notice && <div className="rounded-lg border border-teal-200 bg-teal-50 px-4 py-3 text-sm text-teal-800 dark:border-teal-900/60 dark:bg-teal-950/30 dark:text-teal-300" role="status"><CheckCircle2 className="ml-2 inline h-4 w-4" />{notice}</div>}

      {activeTab === "overview" && <Overview samples={samples} results={results} analyzers={ANALYZERS} onTab={setActiveTab} />}
      {activeTab === "samples" && <SamplesBoard samples={filteredSamples} selectedSample={selectedSample} search={sampleSearch} onSearch={setSampleSearch} onSelect={setSelectedSampleId} onAdvance={advanceSample} />}
      {activeTab === "results" && <ResultsBoard results={filteredResults} search={resultSearch} onSearch={setResultSearch} onVerify={simulateVerify} />}
      {activeTab === "analyzers" && <AnalyzersBoard analyzers={ANALYZERS} />}
      {activeTab === "quality" && <QualityBoard records={QUALITY_RECORDS} />}

      <Card className="border-amber-200 bg-amber-50/60 dark:border-amber-900/50 dark:bg-amber-950/20"><CardContent className="flex items-start gap-3 p-5 text-sm leading-7"><Info className="mt-1 h-5 w-5 shrink-0 text-amber-700 dark:text-amber-400" /><p><strong>حدود الدفعة الحالية:</strong> الأزرار التي تحاكي الانتقال أو التحقق تعدّل الحالة داخل الواجهة فقط. الربط الحقيقي يجب أن يمر عبر عقد خادمي وصلاحيات المختبر وسجل تدقيق، وأن يحول البيانات إلى ServiceRequest وSpecimen وObservation وDiagnosticReport وTask.</p></CardContent></Card>
    </div>
  );
}

function Metric({ label, value, icon: Icon }: { label: string; value: number; icon: typeof TestTube2 }) { return <div className="rounded-xl bg-background/80 p-4 shadow-sm"><div className="flex items-center justify-between gap-2"><p className="text-xs text-muted-foreground">{label}</p><Icon className="h-4 w-4 text-teal-600" /></div><p className="mt-1 text-2xl font-bold">{value}</p></div>; }

function Overview({ samples, results, analyzers, onTab }: { samples: SampleRecord[]; results: ResultRecord[]; analyzers: AnalyzerRecord[]; onTab: (tab: LabTab) => void }) {
  return <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(300px,0.8fr)]"><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Activity className="h-5 w-5 text-teal-600" />مسار العمل الحالي</CardTitle></CardHeader><CardContent className="space-y-3">{[
    { label: "استلام وتسجيل العينة", value: `${samples.filter((sample) => sample.state !== "مرفوضة").length} عينات`, icon: PackageCheck, tab: "samples" as LabTab },
    { label: "الفحص والنتائج المبدئية", value: `${results.filter((result) => result.state === "مبدئية").length} نتائج`, icon: Beaker, tab: "results" as LabTab },
    { label: "التحقق والتنبيه", value: `${results.filter((result) => result.state === "حرجة").length} حرجة`, icon: AlertTriangle, tab: "results" as LabTab },
    { label: "اتصال المحللات", value: `${analyzers.filter((analyzer) => analyzer.state === "متصل").length}/${analyzers.length} متصل`, icon: RefreshCw, tab: "analyzers" as LabTab },
  ].map((step, index) => { const Icon = step.icon; return <button key={step.label} type="button" onClick={() => onTab(step.tab)} className="flex w-full items-center gap-3 rounded-xl border p-4 text-right transition hover:border-teal-300 hover:bg-teal-50/40 dark:hover:bg-teal-950/20"><span className="flex h-9 w-9 items-center justify-center rounded-full bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300">{index + 1}</span><span className="flex-1"><span className="block font-semibold">{step.label}</span><span className="mt-1 block text-xs text-muted-foreground">{step.value}</span></span><Icon className="h-4 w-4 text-teal-600" /><ChevronLeft className="h-4 w-4 text-muted-foreground" /></button>; })}</CardContent></Card><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><AlertTriangle className="h-5 w-5 text-amber-600" />يحتاج انتباهًا</CardTitle></CardHeader><CardContent className="space-y-3"><AlertRow title="نتيجة Troponin I حرجة" detail="ACC-260814-0030 · تحتاج مراجعة مشرف" tone="critical" /><AlertRow title="محلل Sysmex غير متصل" detail="آخر مزامنة منذ 47 دقيقة" tone="warning" /><AlertRow title="TSH خارج نطاق QC" detail="QC-TSH-09C · Level 2" tone="warning" /><Link to="/alerts" className="mt-2 inline-flex items-center gap-2 text-sm font-medium text-teal-700 hover:underline dark:text-teal-300">فتح التنبيهات <ArrowLeft className="h-4 w-4" /></Link></CardContent></Card></div>;
}

function AlertRow({ title, detail, tone }: { title: string; detail: string; tone: "critical" | "warning" }) { return <div className={`rounded-xl border p-3 ${tone === "critical" ? "border-red-200 bg-red-50/70 dark:border-red-900/50 dark:bg-red-950/20" : "border-amber-200 bg-amber-50/70 dark:border-amber-900/50 dark:bg-amber-950/20"}`}><div className="flex items-center gap-2"><AlertTriangle className={`h-4 w-4 ${tone === "critical" ? "text-red-600" : "text-amber-600"}`} /><p className="text-sm font-semibold">{title}</p></div><p className="mt-1 text-xs text-muted-foreground">{detail}</p></div>; }

function SamplesBoard({ samples, selectedSample, search, onSearch, onSelect, onAdvance }: { samples: SampleRecord[]; selectedSample?: SampleRecord; search: string; onSearch: (value: string) => void; onSelect: (id: number) => void; onAdvance: (id: number) => void }) {
  return <div className="grid gap-4 xl:grid-cols-[minmax(0,1.35fr)_minmax(300px,0.75fr)]"><Card><CardHeader><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><CardTitle className="text-base">العينات والوصولات</CardTitle><p className="mt-1 text-xs text-muted-foreground">تتبع accession والعينة والموقع والأولوية دون تغيير قاعدة البيانات.</p></div><div className="relative w-full sm:w-80"><Search className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" /><Input value={search} onChange={(event) => onSearch(event.target.value)} placeholder="ابحث بالوصول أو المريض..." className="pr-9" /></div></div></CardHeader><CardContent className="space-y-2">{samples.map((sample) => <button key={sample.id} type="button" onClick={() => onSelect(sample.id)} className={`w-full rounded-xl border p-4 text-right transition hover:border-teal-300 ${selectedSample?.id === sample.id ? "border-teal-400 bg-teal-50/60 dark:border-teal-700 dark:bg-teal-950/25" : "border-border"}`}><div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">{sample.accession} · {sample.patient}</p><p className="mt-1 text-xs text-muted-foreground">{sample.test} · {sample.specimen} · {sample.location}</p></div><div className="flex items-center gap-2"><Badge variant={sample.priority === "عاجل" ? "warning" : "outline"}>{sample.priority}</Badge><Badge variant={sampleVariant(sample.state)}>{sample.state}</Badge></div></div><div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground"><span>استلام {sample.collectedAt}</span><span>محطة الحيازة: {sample.location}</span></div></button>)}{samples.length === 0 && <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">لا توجد عينة مطابقة.</div>}</CardContent></Card><SampleDetail sample={selectedSample} onAdvance={onAdvance} /></div>;
}

function SampleDetail({ sample, onAdvance }: { sample?: SampleRecord; onAdvance: (id: number) => void }) { if (!sample) return <Card><CardContent className="p-8 text-center text-sm text-muted-foreground">اختر عينة لعرض سلسلة الحيازة.</CardContent></Card>; return <Card><CardHeader><CardTitle className="text-base">سلسلة حيازة العينة</CardTitle><p className="mt-1 text-sm text-muted-foreground">{sample.accession}</p></CardHeader><CardContent className="space-y-4"><div><p className="text-lg font-bold">{sample.patient}</p><p className="mt-1 text-sm text-muted-foreground">{sample.test} · {sample.specimen}</p></div><div className="space-y-3">{[{ label: "تم التسجيل", detail: "استلام الطلب وتوليد accession", icon: ClipboardCheck }, { label: "تم الجمع", detail: `الساعة ${sample.collectedAt} · ${sample.location}`, icon: TestTube2 }, { label: "الفحص", detail: sample.state === "قيد الفحص" ? "قيد التنفيذ على المحلل" : "بانتظار الانتقال", icon: Beaker }, { label: "الحالة الحالية", detail: sample.state, icon: History }].map((step, index) => { const Icon = step.icon; return <div key={step.label} className="flex items-start gap-3"><span className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${index < 2 || (index === 2 && sample.state === "قيد الفحص") ? "bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300" : "bg-muted text-muted-foreground"}`}><Icon className="h-4 w-4" /></span><div><p className="text-sm font-semibold">{step.label}</p><p className="mt-0.5 text-xs text-muted-foreground">{step.detail}</p></div></div>; })}</div>{sample.state === "مستلمة" && <Button type="button" variant="outline" onClick={() => onAdvance(sample.id)}><Beaker className="h-4 w-4" />محاكاة بدء الفحص</Button>}<p className="text-xs leading-5 text-muted-foreground">التسجيلات الفعلية يجب أن تتضمن actor ووقت الحدث والموقع وسبب الرفض عند الحاجة.</p></CardContent></Card>; }

function ResultsBoard({ results, search, onSearch, onVerify }: { results: ResultRecord[]; search: string; onSearch: (value: string) => void; onVerify: (id: number) => void }) { return <Card><CardHeader><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><CardTitle className="text-base">نتائج المختبر</CardTitle><p className="mt-1 text-xs text-muted-foreground">القيمة والنطاق المرجعي وحالة التحقق ومصدر الجهاز.</p></div><div className="relative w-full sm:w-80"><Search className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" /><Input value={search} onChange={(event) => onSearch(event.target.value)} placeholder="ابحث بالوصول أو الفحص..." className="pr-9" /></div></div></CardHeader><CardContent className="space-y-3">{results.map((result) => <div key={result.id} className="rounded-xl border p-4"><div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between"><div><p className="font-semibold">{result.test} · {result.patient}</p><p className="mt-1 text-xs text-muted-foreground">{result.accession} · {result.instrument} · {result.issuedAt}</p></div><div className="flex items-center gap-2"><Badge variant={resultVariant(result.state)}>{result.state}</Badge>{result.state === "مبدئية" && <Button type="button" size="sm" onClick={() => onVerify(result.id)}><CheckCircle2 className="h-4 w-4" />محاكاة التحقق</Button>}</div></div><div className="mt-4 grid gap-3 sm:grid-cols-3"><ValueBox label="القيمة" value={result.value} /><ValueBox label="النطاق المرجعي" value={result.reference} /><ValueBox label="مصدر النتيجة" value={result.instrument} /></div></div>)}{results.length === 0 && <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">لا توجد نتيجة مطابقة.</div>}</CardContent></Card>; }

function ValueBox({ label, value }: { label: string; value: string }) { return <div className="rounded-lg bg-muted/50 p-3"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 font-semibold">{value}</p></div>; }

function AnalyzersBoard({ analyzers }: { analyzers: AnalyzerRecord[] }) { return <div className="grid gap-4 md:grid-cols-2">{analyzers.map((analyzer) => <Card key={analyzer.id}><CardHeader className="pb-3"><div className="flex items-start justify-between gap-3"><div><CardTitle className="text-base">{analyzer.name}</CardTitle><p className="mt-1 text-sm text-muted-foreground">{analyzer.category}</p></div><Badge variant={analyzerVariant(analyzer.state)}>{analyzer.state}</Badge></div></CardHeader><CardContent className="space-y-4"><div className="grid grid-cols-2 gap-3"><ValueBox label="البروتوكول" value={analyzer.protocol} /><ValueBox label="فحوصات اليوم" value={String(analyzer.testsToday)} /></div><div className="flex items-center gap-2 text-xs text-muted-foreground"><RefreshCw className="h-3.5 w-3.5" />آخر مزامنة: {analyzer.lastSync}</div><div className="h-2 overflow-hidden rounded-full bg-muted"><div className={`h-full rounded-full ${analyzer.state === "متصل" ? "w-[88%] bg-teal-500" : analyzer.state === "متدهور" ? "w-[54%] bg-amber-500" : "w-[8%] bg-red-500"}`} /></div><p className="text-xs text-muted-foreground">التكامل المقترح: mapping مستقل يحول ASTM/HL7/CSV إلى LOINC وموارد FHIR.</p></CardContent></Card>)}</div>; }

function QualityBoard({ records }: { records: QualityRecord[] }) { const attention = records.filter((record) => record.state === "يحتاج مراجعة").length; return <div className="space-y-4"><div className="grid gap-3 sm:grid-cols-3"><Card><CardContent className="p-4"><p className="text-xs text-muted-foreground">سجلات QC</p><p className="mt-2 text-2xl font-bold">{records.length}</p></CardContent></Card><Card><CardContent className="p-4"><p className="text-xs text-muted-foreground">مطابقة</p><p className="mt-2 text-2xl font-bold text-teal-700 dark:text-teal-300">{records.length - attention}</p></CardContent></Card><Card><CardContent className="p-4"><p className="text-xs text-muted-foreground">تحتاج مراجعة</p><p className="mt-2 text-2xl font-bold text-amber-700 dark:text-amber-300">{attention}</p></CardContent></Card></div><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><ClipboardCheck className="h-5 w-5 text-teal-600" />ضبط الجودة والتشغيل</CardTitle></CardHeader><CardContent className="space-y-3">{records.map((record) => <div key={record.id} className="flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">{record.analyte} · {record.level}</p><p className="mt-1 text-xs text-muted-foreground">Lot {record.lot} · القيمة {record.measured} · الهدف {record.target}</p></div><Badge variant={record.state === "مطابق" ? "success" : "warning"}>{record.state}</Badge></div>)}</CardContent></Card></div>; }

export default LabOperationsWorkspacePage;
