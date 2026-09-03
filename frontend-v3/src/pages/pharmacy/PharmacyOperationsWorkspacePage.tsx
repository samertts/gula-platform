import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRightLeft,
  Boxes,
  ClipboardList,
  Clock3,
  Database,
  FileCheck2,
  History,
  Info,
  LockKeyhole,
  PackageCheck,
  Pill,
  Search,
  ShieldCheck,
  ShoppingCart,
  Tags,
  Truck,
  type LucideIcon,
} from "lucide-react";
import { apiClient, type WorkspaceSummary } from "@/api/client";
import { pharmacyApi, type PharmacyPosSummary, type PharmacyStockRecord } from "@/api/endpoints";
import { useAuth } from "@/contexts/AuthContext";
import { PageHeader } from "@/components/shared/PageComponents";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type PharmacyTab = "overview" | "pos" | "catalog" | "inventory" | "dispense" | "movements" | "alerts";
type StockState = "متاح" | "منخفض" | "منتهي قريبًا";
type PrescriptionState = "مصدق" | "قيد الصرف" | "مصروف" | "موقوف";

type Medication = {
  id: number;
  code: string;
  name: string;
  generic: string;
  strength: string;
  form: string;
  lot: string;
  expiry: string;
  onHand: number;
  reorderPoint: number;
  location: string;
  state: StockState;
};

type Prescription = {
  id: number;
  number: string;
  patient: string;
  medication: string;
  strength: string;
  quantity: number;
  prescriber: string;
  state: PrescriptionState;
  priority: "عادي" | "عاجل";
  requestedAt: string;
};

type Movement = {
  id: number;
  type: "استلام" | "صرف" | "تحويل" | "تسوية";
  medication: string;
  quantity: number;
  lot: string;
  from: string;
  to: string;
  time: string;
};

type PharmacyAlert = {
  id: number;
  title: string;
  detail: string;
  tone: "critical" | "warning" | "info";
  category: string;
};

const INITIAL_MEDICATIONS: Medication[] = [
  { id: 1, code: "AMX-500-CAP", name: "أموكسيسيلين", generic: "Amoxicillin", strength: "500 mg", form: "كبسولات", lot: "AMX-26-041", expiry: "2027-04-30", onHand: 1280, reorderPoint: 400, location: "رف A-04", state: "متاح" },
  { id: 2, code: "MET-850-TAB", name: "ميتفورمين", generic: "Metformin", strength: "850 mg", form: "أقراص", lot: "MET-26-017", expiry: "2026-11-15", onHand: 318, reorderPoint: 350, location: "رف B-02", state: "منخفض" },
  { id: 3, code: "INS-100-VIAL", name: "إنسولين بشري", generic: "Human insulin", strength: "100 IU/mL", form: "قنينة", lot: "INS-25-109", expiry: "2026-10-08", onHand: 46, reorderPoint: 20, location: "ثلاجة C-01", state: "منتهي قريبًا" },
  { id: 4, code: "PAR-500-TAB", name: "باراسيتامول", generic: "Paracetamol", strength: "500 mg", form: "أقراص", lot: "PAR-26-088", expiry: "2028-01-31", onHand: 2440, reorderPoint: 600, location: "رف A-01", state: "متاح" },
  { id: 5, code: "SAL-09-INF", name: "محلول ملحي", generic: "Sodium chloride", strength: "0.9% 500 mL", form: "كيس وريدي", lot: "SAL-26-203", expiry: "2027-08-20", onHand: 86, reorderPoint: 100, location: "مخزن الطوارئ", state: "منخفض" },
];

const INITIAL_PRESCRIPTIONS: Prescription[] = [
  { id: 1, number: "RX-260814-0041", patient: "سارة عبد الرحمن", medication: "ميتفورمين", strength: "850 mg", quantity: 60, prescriber: "د. ليان أحمد", state: "مصدق", priority: "عادي", requestedAt: "09:18" },
  { id: 2, number: "RX-260814-0044", patient: "حسن نوري", medication: "أموكسيسيلين", strength: "500 mg", quantity: 21, prescriber: "د. سامر كريم", state: "قيد الصرف", priority: "عاجل", requestedAt: "09:22" },
  { id: 3, number: "RX-260814-0047", patient: "مريم فاضل", medication: "إنسولين بشري", strength: "100 IU/mL", quantity: 2, prescriber: "د. نور فاضل", state: "موقوف", priority: "عاجل", requestedAt: "09:29" },
  { id: 4, number: "RX-260814-0039", patient: "علي كريم حسن", medication: "باراسيتامول", strength: "500 mg", quantity: 20, prescriber: "د. رنا جبار", state: "مصروف", priority: "عادي", requestedAt: "08:54" },
];

const MOVEMENTS: Movement[] = [
  { id: 1, type: "استلام", medication: "أموكسيسيلين", quantity: 800, lot: "AMX-26-041", from: "المورد المركزي", to: "رف A-04", time: "09:10" },
  { id: 2, type: "صرف", medication: "باراسيتامول", quantity: 20, lot: "PAR-26-088", from: "رف A-01", to: "مريض RX-260814-0039", time: "08:54" },
  { id: 3, type: "تحويل", medication: "محلول ملحي", quantity: 30, lot: "SAL-26-203", from: "المخزن الرئيسي", to: "مخزن الطوارئ", time: "08:40" },
  { id: 4, type: "تسوية", medication: "ميتفورمين", quantity: -12, lot: "MET-26-017", from: "رف B-02", to: "سجل التسوية", time: "08:26" },
];

const ALERTS: PharmacyAlert[] = [
  { id: 1, title: "مخزون ميتفورمين تحت حد إعادة الطلب", detail: "318 وحدة متبقية مقابل حد 350 · رف B-02", tone: "warning", category: "مخزون" },
  { id: 2, title: "إنسولين تنتهي صلاحيته خلال 90 يومًا", detail: "Lot INS-25-109 · ثلاجة C-01 · راجع FEFO", tone: "warning", category: "انتهاء" },
  { id: 3, title: "وصفة موقوفة تحتاج مراجعة", detail: "RX-260814-0047 · لا يبدأ الصرف قبل استكمال التحقق", tone: "critical", category: "صرف" },
  { id: 4, title: "حركة تحويل بانتظار الاستلام", detail: "30 كيس محلول ملحي إلى مخزن الطوارئ", tone: "info", category: "تحويل" },
];

const TABS: Array<{ id: PharmacyTab; label: string; icon: LucideIcon }> = [
  { id: "overview", label: "نظرة الصيدلية", icon: ShoppingCart },
  { id: "pos", label: "بيع سريع", icon: ShoppingCart },
  { id: "catalog", label: "كتالوج الأدوية", icon: Tags },
  { id: "inventory", label: "المخزون", icon: Boxes },
  { id: "dispense", label: "الوصفات والصرف", icon: Pill },
  { id: "movements", label: "الحركات", icon: ArrowRightLeft },
  { id: "alerts", label: "التنبيهات", icon: AlertTriangle },
];

const stockVariant = (state: StockState): "success" | "warning" => state === "متاح" ? "success" : "warning";
const prescriptionVariant = (state: PrescriptionState): "success" | "warning" | "destructive" | "outline" => state === "مصروف" ? "success" : state === "موقوف" ? "destructive" : state === "قيد الصرف" ? "warning" : "outline";
const movementVariant = (type: Movement["type"]): "success" | "secondary" | "warning" | "outline" => type === "استلام" ? "success" : type === "صرف" ? "secondary" : type === "تسوية" ? "warning" : "outline";

function isActiveWorkspace(workspace: WorkspaceSummary) {
  return ["active", "verified", "approved"].includes(workspace.status.toLowerCase());
}

export default function PharmacyOperationsWorkspacePage() {
  const { demoMode } = useAuth();
  return demoMode ? <PharmacyDemoWorkspace /> : <LivePharmacyWorkspace />;
}

function PharmacyDemoWorkspace() {
  const [activeTab, setActiveTab] = useState<PharmacyTab>("overview");
  const [selectedMedicationId, setSelectedMedicationId] = useState(1);
  const [medicationSearch, setMedicationSearch] = useState("");
  const [prescriptionSearch, setPrescriptionSearch] = useState("");
  const medications = useMemo(() => filterMedications(INITIAL_MEDICATIONS, medicationSearch), [medicationSearch]);
  const prescriptions = useMemo(() => filterPrescriptions(INITIAL_PRESCRIPTIONS, prescriptionSearch), [prescriptionSearch]);
  const selectedMedication = INITIAL_MEDICATIONS.find((medication) => medication.id === selectedMedicationId) ?? INITIAL_MEDICATIONS[0];
  const lowStock = INITIAL_MEDICATIONS.filter((medication) => medication.state === "منخفض").length;
  const expiringSoon = INITIAL_MEDICATIONS.filter((medication) => medication.state === "منتهي قريبًا").length;
  const pendingDispense = INITIAL_PRESCRIPTIONS.filter((prescription) => prescription.state === "مصدق" || prescription.state === "قيد الصرف").length;

  return <PharmacyShell demoMode activeTab={activeTab} onTab={setActiveTab} metrics={[
    ["أصناف الكتالوج", String(INITIAL_MEDICATIONS.length), Tags],
    ["تحت حد الطلب", String(lowStock), Boxes],
    ["انتهاء قريب", String(expiringSoon), Clock3],
    ["وصفات بانتظار الصرف", String(pendingDispense), ClipboardList],
  ]}>
    <PharmacyDemoOverview onTab={setActiveTab} />
    {activeTab === "pos" && <GatedPanel title="معاينة الصرف فقط" description="مسار البيع والصرف ظاهر للشرح، لكن لا توجد عملية صرف أو فاتورة أو خصم مخزون في Demo." />}
    {activeTab === "catalog" && <Catalog medications={medications} selected={selectedMedication} search={medicationSearch} onSearch={setMedicationSearch} onSelect={setSelectedMedicationId} />}
    {activeTab === "inventory" && <Inventory medications={medications} search={medicationSearch} onSearch={setMedicationSearch} />}
    {activeTab === "dispense" && <DispenseQueue prescriptions={prescriptions} search={prescriptionSearch} onSearch={setPrescriptionSearch} />}
    {activeTab === "movements" && <Movements movements={MOVEMENTS} />}
    {activeTab === "alerts" && <Alerts alerts={ALERTS} />}
    <DemoBoundary />
  </PharmacyShell>;
}

function LivePharmacyWorkspace() {
  const [activeTab, setActiveTab] = useState<PharmacyTab>("overview");
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string | null>(null);
  const [switchingWorkspaceId, setSwitchingWorkspaceId] = useState<string | null>(null);
  const [catalogSearch, setCatalogSearch] = useState("");
  const [switchError, setSwitchError] = useState("");
  const workspacesQuery = useQuery({ queryKey: ["pharmacy-workspaces", "me"], queryFn: () => apiClient.listWorkspaces(), retry: false, staleTime: 30_000 });
  const pharmacyWorkspaces = (workspacesQuery.data?.workspaces ?? []).filter((workspace) => !workspace.is_personal && Boolean(workspace.facility_id));
  const selectedWorkspace = pharmacyWorkspaces.find((workspace) => workspace.id === selectedWorkspaceId);
  const contextReady = Boolean(selectedWorkspaceId && selectedWorkspace && isActiveWorkspace(selectedWorkspace));
  const summaryQuery = useQuery({ queryKey: ["pharmacy-summary", selectedWorkspaceId], queryFn: () => pharmacyApi.summary(30), enabled: contextReady, retry: false, staleTime: 15_000 });
  const stockQuery = useQuery({ queryKey: ["pharmacy-stock", selectedWorkspaceId], queryFn: () => pharmacyApi.stock({ limit: 50 }), enabled: contextReady, retry: false, staleTime: 15_000 });
  const activateWorkspace = async (workspace: WorkspaceSummary) => {
    if (!isActiveWorkspace(workspace) || workspace.id === selectedWorkspaceId) return;
    setSwitchingWorkspaceId(workspace.id);
    setSwitchError("");
    try {
      await apiClient.switchWorkspace(workspace.id);
      setSelectedWorkspaceId(workspace.id);
    } catch (error) {
      setSwitchError(error instanceof Error ? error.message : "تعذر تفعيل سياق الصيدلية.");
    } finally {
      setSwitchingWorkspaceId(null);
    }
  };

  return <PharmacyShell demoMode={false} activeTab={activeTab} onTab={setActiveTab} metrics={liveMetrics(summaryQuery.data, stockQuery.data)}>
    <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70"><CardHeader><CardTitle className="flex items-center gap-2 text-base"><ShieldCheck className="h-5 w-5 text-indigo-600" />سياق الصيدلية المؤسسي</CardTitle><p className="mt-1 text-xs text-muted-foreground">لا تُقرأ الكتالوجات أو المخزونات الحية قبل أن يثبت الخادم مساحة منشأة وسياق عضوية صالحاً.</p></CardHeader><CardContent className="space-y-3">{workspacesQuery.isLoading ? <div className="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">جارٍ تحميل مساحات الصيدلية…</div> : pharmacyWorkspaces.length === 0 ? <GatedPanel title="لا توجد مساحة صيدلية مؤكدة" description="تحتاج القراءة الحية إلى Professional Verification وMembership وFacility Context معاد من الخادم." /> : pharmacyWorkspaces.map((workspace) => <WorkspaceCard key={workspace.id} workspace={workspace} selected={workspace.id === selectedWorkspaceId} switching={switchingWorkspaceId === workspace.id} onSelect={() => void activateWorkspace(workspace)} />)}{switchError && <p className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/20 dark:text-rose-200" role="alert">{switchError}</p>}{workspacesQuery.error && <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200" role="alert">تعذر قراءة مساحات الصيدلية من الخادم.</p>}</CardContent></Card>
    {activeTab === "overview" && <LiveOverview summary={summaryQuery.data} stock={stockQuery.data} loading={summaryQuery.isLoading || stockQuery.isLoading} error={summaryQuery.error || stockQuery.error} selectedWorkspace={selectedWorkspace} onTab={setActiveTab} />}
    {activeTab === "pos" && <GatedPanel title="عقد الصرف الحي يحتاج خطوة تحقق مخصصة" description="يوجد backend POS مع idempotency، لكن هذا المسار لا يفتح صرفاً حياً قبل إضافة سياق الصيدلية والتحقق من المريض/الوصفة والصلاحية والـaudit ضمن عقد موحد." />}
    {activeTab === "catalog" && <LiveCatalog enabled={contextReady} search={catalogSearch} onSearch={setCatalogSearch} />}
    {activeTab === "inventory" && <LiveInventory enabled={contextReady} stock={stockQuery.data} loading={stockQuery.isLoading} error={stockQuery.error} />}
    {activeTab === "dispense" && <GatedPanel title="عقد الوصفة والصرف غير مفعّل في هذه الواجهة" description="لا تُعرض وصفات أو معلومات مرضى من endpoint عام. يلزم عقد Prescription/Dispense يفرض patient verification وremaining quantity وFEFO وidempotency وسجل التدقيق." />}
    {activeTab === "movements" && <GatedPanel title="عقد الحركات والتحويلات غير مفعّل" description="التحويل والاستلام والمرتجع والإتلاف تحتاج state machine ونطاق فرع وموافقة وتدقيقاً قبل القراءة أو الكتابة الحية." />}
    {activeTab === "alerts" && <GatedPanel title="عقد تنبيهات الصيدلية غير مفعّل" description="لا تُعرض تنبيهات حية من دون عقد يميز الصرف والمخزون والاستدعاء والسلسلة الباردة ويطبق نطاق المؤسسة." />}
    {(summaryQuery.error || stockQuery.error) && <div className="rounded-2xl border border-amber-200 bg-amber-50/70 p-5 text-sm leading-7 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200" role="status"><LockKeyhole className="ml-2 inline h-4 w-4" />تم إيقاف قراءة بيانات الصيدلية بأمان؛ لم يتم استخدام بيانات Demo أو fallback legacy.</div>}
    <LiveBoundary />
  </PharmacyShell>;
}

function PharmacyShell({ demoMode, activeTab, onTab, metrics, children }: { demoMode: boolean; activeTab: PharmacyTab; onTab: (tab: PharmacyTab) => void; metrics: Array<[string, string, LucideIcon]>; children: React.ReactNode }) {
  return <div className="mx-auto max-w-7xl space-y-6" dir="rtl"><PageHeader title="إدارة الصيدلية والأدوية" description="مساحة GULA لدورة الوصفة والدواء والصرف والمخزون، مع فصل واضح بين العرض التجريبي والعقود التشغيلية الحية." /><Card className="overflow-hidden border-indigo-200 bg-gradient-to-l from-indigo-50 via-white to-teal-50 dark:border-indigo-900/50 dark:from-indigo-950/30 dark:via-background dark:to-teal-950/30"><CardContent className="p-6"><div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between"><div className="max-w-3xl space-y-3"><div className="flex items-center gap-2 text-indigo-700 dark:text-indigo-300"><Pill className="h-5 w-5" /><span className="text-sm font-semibold">Medication & Supply Operations</span></div><h2 className="text-2xl font-bold tracking-tight">من الوصفة إلى صرف آمن قابل للتدقيق</h2><p className="text-sm leading-7 text-muted-foreground">تنظيم الوصفة والكتالوج والمخزون والدفعات والانتهاء والصرف والتتبع، مع منع أي خلط بين القرار السريري والعملية المالية.</p><div className="flex flex-wrap gap-2"><Badge variant={demoMode ? "success" : "outline"}><ShieldCheck className="ml-1 h-3.5 w-3.5" />{demoMode ? "عرض اصطناعي معزول" : "سياق خادمي مطلوب"}</Badge><Badge variant="outline"><Database className="ml-1 h-3.5 w-3.5" />MedicationRequest-ready</Badge><Badge variant="outline"><History className="ml-1 h-3.5 w-3.5" />Audit boundary</Badge></div></div>{demoMode && <div className="grid min-w-[290px] grid-cols-2 gap-3"><Metric label="وصفات اليوم" value="24" icon={ClipboardList} /><Metric label="بانتظار التحقق" value="5" icon={FileCheck2} /><Metric label="تنبيهات مخزون" value="3" icon={Boxes} /><Metric label="طلبات تأمين" value="4" icon={ShieldCheck} /></div>}</div></CardContent></Card><MetricGrid metrics={metrics} /><PharmacyTabs activeTab={activeTab} onChange={onTab} />{children}</div>;
}

function PharmacyTabs({ activeTab, onChange }: { activeTab: PharmacyTab; onChange: (tab: PharmacyTab) => void }) { return <Card><CardContent className="p-0"><div className="flex flex-wrap border-b">{TABS.map(({ id, label, icon: Icon }) => <button key={id} type="button" onClick={() => onChange(id)} aria-selected={activeTab === id} className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 ${activeTab === id ? "border-b-2 border-indigo-600 text-indigo-700 dark:text-indigo-300" : "text-muted-foreground hover:text-foreground"}`}><Icon className="h-4 w-4" />{label}</button>)}</div></CardContent></Card>; }

function MetricGrid({ metrics }: { metrics: Array<[string, string, LucideIcon]> }) { return <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="مؤشرات الصيدلية">{metrics.map(([label, value, Icon]) => <Card key={label} className="overflow-hidden rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70"><CardContent className="relative p-5"><div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-l from-indigo-500 to-teal-400" /><div className="flex items-start justify-between gap-3"><span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200"><Icon className="h-5 w-5" /></span><Badge variant="outline">{value === "—" ? "محجوب" : "حالة"}</Badge></div><p className="mt-5 text-sm text-muted-foreground">{label}</p><p className="mt-1 text-3xl font-bold tracking-tight text-[#0F172A] dark:text-white">{value}</p></CardContent></Card>)}</section>; }

function Metric({ label, value, icon: Icon }: { label: string; value: string; icon: LucideIcon }) { return <div className="rounded-xl bg-background/80 p-4 shadow-sm"><div className="flex items-center justify-between gap-2"><p className="text-xs text-muted-foreground">{label}</p><Icon className="h-4 w-4 text-indigo-600" /></div><p className="mt-1 text-2xl font-bold">{value}</p></div>; }

function PharmacyDemoOverview({ onTab }: { onTab: (tab: PharmacyTab) => void }) { const steps: Array<{ label: string; detail: string; icon: LucideIcon; tab: PharmacyTab }> = [{ label: "الكتالوج والمخزون", detail: "5 أصناف · FEFO والتشغيلة للشرح", icon: Tags, tab: "catalog" }, { label: "الوصفات المصادق عليها", detail: "2 وصفة ضمن سيناريو الصرف", icon: FileCheck2, tab: "dispense" }, { label: "التحقق والصرف", detail: "مراحل محجوبة في Demo", icon: PackageCheck, tab: "pos" }, { label: "التوريد والتحويل", detail: "سجل حركة اصطناعي", icon: Truck, tab: "movements" }]; return <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(300px,0.8fr)]"><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><ShoppingCart className="h-5 w-5 text-indigo-600" />مسار الصيدلية التجريبي</CardTitle></CardHeader><CardContent className="space-y-3">{steps.map((step, index) => { const Icon = step.icon; return <button key={step.label} type="button" onClick={() => onTab(step.tab)} className="flex w-full items-center gap-3 rounded-xl border p-4 text-right transition hover:border-indigo-300 hover:bg-indigo-50/40 dark:hover:bg-indigo-950/20"><span className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300">{index + 1}</span><span className="flex-1"><span className="block font-semibold">{step.label}</span><span className="mt-1 block text-xs text-muted-foreground">{step.detail}</span></span><Icon className="h-4 w-4 text-indigo-600" /><ArrowLeft className="h-4 w-4 text-muted-foreground" /></button>; })}</CardContent></Card><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><AlertTriangle className="h-5 w-5 text-amber-600" />تنبيهات تشغيلية للشرح</CardTitle></CardHeader><CardContent className="space-y-3"><AlertRow title="مخزون ميتفورمين منخفض" detail="سيناريو اصطناعي · FEFO مطلوب" tone="warning" /><AlertRow title="وصفة موقوفة" detail="سيناريو اصطناعي · لا يبدأ الصرف" tone="critical" /><AlertRow title="إنسولين قريب الانتهاء" detail="سيناريو اصطناعي · مراجعة السلسلة الباردة" tone="warning" /><Link to="/alerts" className="mt-2 inline-flex items-center gap-2 text-sm font-medium text-indigo-700 hover:underline dark:text-indigo-300">فتح التنبيهات <ArrowLeft className="h-4 w-4" /></Link></CardContent></Card></div>; }

function LiveOverview({ summary, stock, loading, error, selectedWorkspace, onTab }: { summary?: PharmacyPosSummary; stock?: PharmacyStockRecord[]; loading: boolean; error: unknown; selectedWorkspace?: WorkspaceSummary; onTab: (tab: PharmacyTab) => void }) { return <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(300px,0.8fr)]"><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><ClipboardList className="h-5 w-5 text-indigo-600" />ملخص الصيدلية الحي</CardTitle><p className="mt-1 text-xs text-muted-foreground">{selectedWorkspace ? "قراءة محدودة من عقود الصيدلية بعد تفعيل سياق الخادم." : "فعّل سياق الصيدلية من الخادم أولاً."}</p></CardHeader><CardContent>{loading ? <div className="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">جارٍ التحقق من عقود الصيدلية…</div> : error ? <GatedPanel title="قراءة الصيدلية موقوفة بأمان" description="رفض العقد القراءة أو تعذر الاتصال؛ لم يتم استخدام fallback legacy." /> : <div className="grid gap-3 sm:grid-cols-2"><ValueBox label="مبيعات الفترة" value={summary ? `${summary.sales_total} IQD` : "غير معروضة"} /><ValueBox label="أصناف منخفضة" value={summary ? String(summary.low_stock_count) : "غير معروض"} /><ValueBox label="أصناف المخزون المعادة" value={stock ? String(stock.length) : "غير معروض"} /><ValueBox label="الصرف" value="محجوب حتى عقد التحقق" /></div>}</CardContent></Card><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><LockKeyhole className="h-5 w-5 text-amber-600" />العقود التالية</CardTitle></CardHeader><CardContent className="space-y-3"><GatedLine label="Prescription / Patient verification" onClick={() => onTab("dispense")} /><GatedLine label="Medication dispense / FEFO" onClick={() => onTab("pos")} /><GatedLine label="Transfers / Returns / Recall" onClick={() => onTab("movements")} /><GatedLine label="Insurance / Payment separation" onClick={() => onTab("alerts")} /></CardContent></Card></div>; }

function liveMetrics(summary?: PharmacyPosSummary, stock?: PharmacyStockRecord[]): Array<[string, string, LucideIcon]> { return [["مبيعات 30 يوماً", summary ? `${summary.sales_total} IQD` : "—", ShoppingCart], ["أصناف منخفضة", summary ? String(summary.low_stock_count) : "—", Boxes], ["سجلات المخزون", stock ? String(stock.length) : "—", Tags], ["الصرف الحي", "محجوب", PackageCheck]]; }

function LiveCatalog({ enabled, search, onSearch }: { enabled: boolean; search: string; onSearch: (value: string) => void }) { const query = useQuery({ queryKey: ["pharmacy-catalog", search], queryFn: () => pharmacyApi.drugs(search.trim()), enabled: enabled && search.trim().length >= 2, retry: false, staleTime: 30_000 }); return <Card><CardHeader><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><CardTitle className="text-base">كتالوج الأدوية الحي</CardTitle><p className="mt-1 text-xs text-muted-foreground">قراءة أصناف الكتالوج بعد تفعيل سياق المنشأة؛ لا تنفذ الوصفة أو الصرف.</p></div><SearchBox value={search} onChange={onSearch} placeholder="ابحث باسم الدواء أو الرمز..." /></div></CardHeader><CardContent className="space-y-2">{!enabled ? <GatedPanel title="فعّل سياق الصيدلية أولاً" description="لا يتم البحث في الكتالوج قبل إثبات workspace خادمي." /> : query.isLoading ? <div className="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">جارٍ البحث…</div> : query.error ? <GatedPanel title="تعذر قراءة الكتالوج" description="لم يتم استخدام بيانات اصطناعية كبديل." /> : search.trim().length < 2 ? <div className="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">اكتب حرفين على الأقل لبدء البحث.</div> : query.data?.items.length ? query.data.items.map((drug) => <div key={drug.id} className="flex items-center justify-between gap-3 rounded-xl border p-4"><div><p className="font-semibold">{drug.name_ar || drug.name}</p><p className="mt-1 text-xs text-muted-foreground">{drug.generic_name || drug.brand_name || drug.code} · {drug.barcode_gs1 || "بدون باركود"}</p></div><Badge variant={drug.is_active ? "success" : "outline"}>{drug.is_active ? "فعال" : "موقوف"}</Badge></div>) : <EmptyMessage text="لا توجد أصناف مطابقة ضمن السياق." />}</CardContent></Card>; }

function LiveInventory({ enabled, stock, loading, error }: { enabled: boolean; stock?: PharmacyStockRecord[]; loading: boolean; error: unknown }) { return <Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Boxes className="h-5 w-5 text-indigo-600" />المخزون الحي</CardTitle><p className="mt-1 text-xs text-muted-foreground">قراءة كميات محدودة؛ لا توجد تسوية أو استلام أو تحويل من هذه الصفحة.</p></CardHeader><CardContent>{!enabled ? <GatedPanel title="فعّل سياق الصيدلية أولاً" description="المخزون فرعي النطاق ولا يُقرأ من دون workspace خادمي." /> : loading ? <div className="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">جارٍ تحميل المخزون…</div> : error ? <GatedPanel title="تعذر قراءة المخزون" description="لم يتم استخدام Demo أو fallback legacy." /> : stock?.length ? <div className="space-y-2">{stock.map((item) => <div key={item.id} className="flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">صنف دوائي ضمن الكتالوج</p><p className="mt-1 text-xs text-muted-foreground">التشغيلة {item.batch_id ?? "غير معروضة"} · حالة التخزين {item.storage_condition ?? "غير معروضة"}</p></div><div className="flex items-center gap-2"><Badge variant={item.available_quantity > 0 ? "success" : "warning"}>متاح {item.available_quantity}</Badge><span className="text-xs text-muted-foreground">محجوز {item.reserved_quantity}</span></div></div>)}</div> : <EmptyMessage text="لا توجد سجلات مخزون ضمن السياق." />}</CardContent></Card>; }

function WorkspaceCard({ workspace, selected, switching, onSelect }: { workspace: WorkspaceSummary; selected: boolean; switching: boolean; onSelect: () => void }) { const active = isActiveWorkspace(workspace); return <div className={`rounded-xl border p-4 transition ${selected ? "border-indigo-400 bg-indigo-50/60 dark:border-indigo-700 dark:bg-indigo-950/20" : "border-slate-200/80 dark:border-white/10"}`}><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div className="flex items-start gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200"><Pill className="h-5 w-5" /></span><div><p className="text-sm font-bold">{workspace.name_ar ?? workspace.name}</p><p className="mt-1 text-xs text-muted-foreground">{workspace.facility_id ?? "منشأة غير معروضة"} · {workspace.department_id ?? "قسم غير معروض"}</p></div></div><div className="flex items-center gap-2"><Badge variant={active ? "success" : "outline"}>{workspace.status}</Badge><Button type="button" size="sm" variant={selected ? "secondary" : "outline"} disabled={!active || selected || switching} onClick={onSelect}>{switching ? "جارٍ التفعيل…" : selected ? "السياق الحالي" : "تفعيل سياق الصيدلية"}</Button></div></div></div>; }

function GatedLine({ label, onClick }: { label: string; onClick: () => void }) { return <button type="button" onClick={onClick} className="flex w-full items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50/60 p-3 text-right text-sm text-amber-950 transition hover:border-amber-300 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200"><span>{label}</span><LockKeyhole className="h-4 w-4" /></button>; }
function GatedPanel({ title, description }: { title: string; description: string }) { return <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-5 text-sm leading-7 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200"><LockKeyhole className="ml-2 inline h-4 w-4" /><strong>{title}</strong><p className="mt-2 text-xs leading-6 opacity-80">{description}</p></div>; }
function DemoBoundary() { return <Card className="border-amber-200 bg-amber-50/60 dark:border-amber-900/50 dark:bg-amber-950/20"><CardContent className="flex items-start gap-3 p-5 text-sm leading-7"><Info className="mt-1 h-5 w-5 shrink-0 text-amber-700 dark:text-amber-400" /><p><strong>حدود Demo:</strong> الوصفات والصرف والمخزون والحركات اصطناعية للعرض فقط. لا يوجد بيع أو صرف أو خصم أو إنشاء فاتورة.</p></CardContent></Card>; }
function LiveBoundary() { return <Card className="border-amber-200 bg-amber-50/60 dark:border-amber-900/50 dark:bg-amber-950/20"><CardContent className="flex items-start gap-3 p-5 text-sm leading-7"><Info className="mt-1 h-5 w-5 shrink-0 text-amber-700 dark:text-amber-400" /><p><strong>حدود Live الحالية:</strong> القراءة الحية تقتصر على سياق المؤسسة والكتالوج والمخزون والملخص. لا تُنفذ وصفة أو صرف أو استبدال أو تحويل أو تعديل مخزون أو دفع حتى تكتمل العقود الخادمية.</p></CardContent></Card>; }

function Catalog({ medications, selected, search, onSearch, onSelect }: { medications: Medication[]; selected?: Medication; search: string; onSearch: (value: string) => void; onSelect: (id: number) => void }) { return <div className="grid gap-4 xl:grid-cols-[minmax(0,1.35fr)_minmax(300px,0.75fr)]"><Card><CardHeader><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><CardTitle className="text-base">كتالوج الأدوية</CardTitle><p className="mt-1 text-xs text-muted-foreground">بيانات اصطناعية للبحث بالاسم أو الرمز أو التشغيلة.</p></div><SearchBox value={search} onChange={onSearch} placeholder="ابحث عن دواء..." /></div></CardHeader><CardContent className="space-y-2">{medications.map((medication) => <button key={medication.id} type="button" onClick={() => onSelect(medication.id)} className={`w-full rounded-xl border p-4 text-right transition hover:border-indigo-300 ${selected?.id === medication.id ? "border-indigo-400 bg-indigo-50/60 dark:border-indigo-700 dark:bg-indigo-950/25" : "border-border"}`}><div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">{medication.name} · {medication.strength}</p><p className="mt-1 text-xs text-muted-foreground">{medication.generic} · {medication.form} · {medication.code}</p></div><Badge variant={stockVariant(medication.state)}>{medication.state}</Badge></div><div className="mt-3 flex flex-wrap gap-4 text-xs text-muted-foreground"><span>{medication.onHand} وحدة</span><span>{medication.location}</span><span>انتهاء {medication.expiry}</span></div></button>)}{medications.length === 0 && <EmptyMessage text="لا يوجد دواء مطابق." />}</CardContent></Card><MedicationDetail medication={selected} /></div>; }
function MedicationDetail({ medication }: { medication?: Medication }) { if (!medication) return <Card><CardContent className="p-8 text-center text-sm text-muted-foreground">اختر صنفًا لعرض تفاصيله.</CardContent></Card>; return <Card><CardHeader><CardTitle className="text-base">بطاقة الدواء التجريبية</CardTitle><p className="mt-1 text-sm text-muted-foreground">{medication.code}</p></CardHeader><CardContent className="space-y-4"><div><p className="text-lg font-bold">{medication.name}</p><p className="mt-1 text-sm text-muted-foreground">{medication.generic} · {medication.strength} · {medication.form}</p></div><div className="grid grid-cols-2 gap-3"><ValueBox label="الرصيد" value={`${medication.onHand} وحدة`} /><ValueBox label="حد الطلب" value={`${medication.reorderPoint} وحدة`} /><ValueBox label="التشغيلة" value={medication.lot} /><ValueBox label="الموقع" value={medication.location} /></div><GatedPanel title="العملية التشغيلية محجوبة" description="لا يضيف Demo دفعة أو يغير رصيداً أو ينشئ وصفة." /></CardContent></Card>; }
function Inventory({ medications, search, onSearch }: { medications: Medication[]; search: string; onSearch: (value: string) => void }) { return <Card><CardHeader><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><CardTitle className="text-base">المخزون حسب الموقع والتشغيلة</CardTitle><p className="mt-1 text-xs text-muted-foreground">عرض اصطناعي لـFEFO والحد الأدنى والموقع دون تعديل.</p></div><SearchBox value={search} onChange={onSearch} placeholder="ابحث في المخزون..." /></div></CardHeader><CardContent className="space-y-2">{medications.map((medication) => <div key={medication.id} className="flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">{medication.name} · {medication.strength}</p><p className="mt-1 text-xs text-muted-foreground">{medication.lot} · {medication.location} · انتهاء {medication.expiry}</p></div><div className="flex flex-wrap items-center gap-2"><span className="rounded-lg bg-muted px-3 py-2 text-sm font-semibold">{medication.onHand} / حد {medication.reorderPoint}</span><Badge variant={stockVariant(medication.state)}>{medication.state}</Badge></div></div>)}{medications.length === 0 && <EmptyMessage text="لا يوجد صنف مطابق." />}</CardContent></Card>; }
function DispenseQueue({ prescriptions, search, onSearch }: { prescriptions: Prescription[]; search: string; onSearch: (value: string) => void }) { return <Card><CardHeader><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><CardTitle className="text-base">الوصفات والصرف</CardTitle><p className="mt-1 text-xs text-muted-foreground">بيانات اصطناعية لحالة الوصفة والمريض والكمية والواصف، دون صرف.</p></div><SearchBox value={search} onChange={onSearch} placeholder="ابحث بالوصفة أو المريض..." /></div></CardHeader><CardContent className="space-y-3">{prescriptions.map((prescription) => <div key={prescription.id} className="rounded-xl border p-4"><div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between"><div><p className="font-semibold">{prescription.number} · {prescription.patient}</p><p className="mt-1 text-xs text-muted-foreground">{prescription.medication} {prescription.strength} · {prescription.quantity} وحدة · {prescription.prescriber} · {prescription.requestedAt}</p></div><div className="flex items-center gap-2"><Badge variant={prescription.priority === "عاجل" ? "warning" : "outline"}>{prescription.priority}</Badge><Badge variant={prescriptionVariant(prescription.state)}>{prescription.state}</Badge></div></div><div className="mt-4 flex items-center gap-3 text-xs text-muted-foreground"><span className="flex items-center gap-1"><FileCheck2 className="h-3.5 w-3.5" />MedicationRequest</span><ArrowLeft className="h-3.5 w-3.5" /><span className="flex items-center gap-1"><PackageCheck className="h-3.5 w-3.5" />MedicationDispense</span></div></div>)}{prescriptions.length === 0 && <EmptyMessage text="لا توجد وصفة مطابقة." />}</CardContent></Card>; }
function Movements({ movements }: { movements: Movement[] }) { return <Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><ArrowRightLeft className="h-5 w-5 text-indigo-600" />سجل الحركات التجريبي</CardTitle><p className="mt-1 text-xs text-muted-foreground">استلام وصرف وتحويل وتسوية اصطناعية مع المصدر والوجهة والتشغيلة.</p></CardHeader><CardContent className="space-y-2">{movements.map((movement) => <div key={movement.id} className="flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">{movement.medication} · {movement.quantity > 0 ? "+" : ""}{movement.quantity} وحدة</p><p className="mt-1 text-xs text-muted-foreground">{movement.lot} · {movement.from} ← {movement.to} · {movement.time}</p></div><Badge variant={movementVariant(movement.type)}>{movement.type}</Badge></div>)}</CardContent></Card>; }
function Alerts({ alerts }: { alerts: PharmacyAlert[] }) { return <div className="grid gap-3 md:grid-cols-2">{alerts.map((alert) => <Card key={alert.id} className={alert.tone === "critical" ? "border-red-200 dark:border-red-900/50" : alert.tone === "warning" ? "border-amber-200 dark:border-amber-900/50" : "border-sky-200 dark:border-sky-900/50"}><CardContent className="p-5"><div className="flex items-start gap-3"><AlertTriangle className={`mt-0.5 h-5 w-5 ${alert.tone === "critical" ? "text-red-600" : alert.tone === "warning" ? "text-amber-600" : "text-sky-600"}`} /><div className="flex-1"><div className="flex items-center justify-between gap-3"><p className="font-semibold">{alert.title}</p><Badge variant={alert.tone === "critical" ? "destructive" : alert.tone === "warning" ? "warning" : "outline"}>{alert.category}</Badge></div><p className="mt-2 text-sm leading-6 text-muted-foreground">{alert.detail}</p></div></div></CardContent></Card>)}</div>; }
function SearchBox({ value, onChange, placeholder }: { value: string; onChange: (value: string) => void; placeholder: string }) { return <div className="relative w-full sm:w-80"><Search className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" /><Input value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} className="pr-9" /></div>; }
function ValueBox({ label, value }: { label: string; value: string }) { return <div className="rounded-lg bg-muted/50 p-3"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 font-semibold">{value}</p></div>; }
function EmptyMessage({ text }: { text: string }) { return <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">{text}</div>; }
function AlertRow({ title, detail, tone }: { title: string; detail: string; tone: "critical" | "warning" }) { return <div className={`rounded-xl border p-3 ${tone === "critical" ? "border-red-200 bg-red-50/70 dark:border-red-900/50 dark:bg-red-950/20" : "border-amber-200 bg-amber-50/70 dark:border-amber-900/50 dark:bg-amber-950/20"}`}><div className="flex items-center gap-2"><AlertTriangle className={`h-4 w-4 ${tone === "critical" ? "text-red-600" : "text-amber-600"}`} /><p className="text-sm font-semibold">{title}</p></div><p className="mt-1 text-xs text-muted-foreground">{detail}</p></div>; }
function filterMedications(medications: Medication[], search: string) { const term = search.trim().toLocaleLowerCase("ar"); return term ? medications.filter((medication) => `${medication.name} ${medication.generic} ${medication.code} ${medication.lot} ${medication.location}`.toLocaleLowerCase("ar").includes(term)) : medications; }
function filterPrescriptions(prescriptions: Prescription[], search: string) { const term = search.trim().toLocaleLowerCase("ar"); return term ? prescriptions.filter((prescription) => `${prescription.number} ${prescription.patient} ${prescription.medication} ${prescription.prescriber}`.toLocaleLowerCase("ar").includes(term)) : prescriptions; }

export { PharmacyDemoWorkspace };
