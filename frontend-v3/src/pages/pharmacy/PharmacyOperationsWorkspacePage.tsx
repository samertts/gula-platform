import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRightLeft,
  Boxes,
  CheckCircle2,
  ClipboardList,
  Clock3,
  Database,
  FileCheck2,
  History,
  Info,
  PackageCheck,
  Pill,
  Plus,
  Search,
  ShieldCheck,
  ShoppingCart,
  Tags,
  Truck,
} from "lucide-react";
import { PageHeader } from "@/components/shared/PageComponents";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type PharmacyTab = "overview" | "catalog" | "inventory" | "dispense" | "movements" | "alerts";
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

const tabs: Array<{ id: PharmacyTab; label: string; icon: typeof Pill }> = [
  { id: "overview", label: "نظرة الصيدلية", icon: ShoppingCart },
  { id: "catalog", label: "كتالوج الأدوية", icon: Tags },
  { id: "inventory", label: "المخزون", icon: Boxes },
  { id: "dispense", label: "الوصفات والصرف", icon: Pill },
  { id: "movements", label: "الحركات", icon: ArrowRightLeft },
  { id: "alerts", label: "التنبيهات", icon: AlertTriangle },
];

const stockVariant = (state: StockState): "success" | "warning" => state === "متاح" ? "success" : "warning";
const prescriptionVariant = (state: PrescriptionState): "success" | "warning" | "destructive" | "outline" => state === "مصروف" ? "success" : state === "موقوف" ? "destructive" : state === "قيد الصرف" ? "warning" : "outline";
const movementVariant = (type: Movement["type"]): "success" | "secondary" | "warning" | "outline" => type === "استلام" ? "success" : type === "صرف" ? "secondary" : type === "تسوية" ? "warning" : "outline";

export default function PharmacyOperationsWorkspacePage() {
  const [activeTab, setActiveTab] = useState<PharmacyTab>("overview");
  const [medications, setMedications] = useState(INITIAL_MEDICATIONS);
  const [prescriptions, setPrescriptions] = useState(INITIAL_PRESCRIPTIONS);
  const [selectedMedicationId, setSelectedMedicationId] = useState(1);
  const [medicationSearch, setMedicationSearch] = useState("");
  const [prescriptionSearch, setPrescriptionSearch] = useState("");
  const [notice, setNotice] = useState("");

  const filteredMedications = useMemo(() => {
    const term = medicationSearch.trim().toLocaleLowerCase("ar");
    if (!term) return medications;
    return medications.filter((medication) => `${medication.name} ${medication.generic} ${medication.code} ${medication.lot} ${medication.location}`.toLocaleLowerCase("ar").includes(term));
  }, [medicationSearch, medications]);

  const filteredPrescriptions = useMemo(() => {
    const term = prescriptionSearch.trim().toLocaleLowerCase("ar");
    if (!term) return prescriptions;
    return prescriptions.filter((prescription) => `${prescription.number} ${prescription.patient} ${prescription.medication} ${prescription.prescriber}`.toLocaleLowerCase("ar").includes(term));
  }, [prescriptionSearch, prescriptions]);

  const selectedMedication = medications.find((medication) => medication.id === selectedMedicationId) ?? medications[0];
  const lowStock = medications.filter((medication) => medication.state === "منخفض").length;
  const expiringSoon = medications.filter((medication) => medication.state === "منتهي قريبًا").length;
  const pendingDispense = prescriptions.filter((prescription) => prescription.state === "مصدق" || prescription.state === "قيد الصرف").length;

  const simulateDispense = (prescriptionId: number) => {
    setPrescriptions((current) => current.map((prescription) => prescription.id === prescriptionId ? { ...prescription, state: "مصروف" } : prescription));
    setNotice("تمت محاكاة صرف الوصفة محليًا؛ لم تُخصم كمية من مخزون فعلي ولم تُرسل وصفة إلى نظام خارجي.");
  };

  const simulateReceive = (medicationId: number) => {
    setMedications((current) => current.map((medication) => medication.id === medicationId ? { ...medication, onHand: medication.onHand + 100, state: "متاح" } : medication));
    setNotice("تمت محاكاة استلام 100 وحدة محليًا، دون إنشاء حركة خادمية أو تعديل مخزون حقيقي.");
  };

  return <div className="mx-auto max-w-7xl space-y-6" dir="rtl">
    <PageHeader title="إدارة الصيدلية والأدوية" description="مساحة GULA الأصلية لإدارة الكتالوج والمخزون والوصفات والصرف والحركات والتنبيهات، مستلهمة من OpenBoxes وFreeMedForms وOpenMRS دون نسخ الكود." />

    <Card className="overflow-hidden border-indigo-200 bg-gradient-to-l from-indigo-50 via-white to-teal-50 dark:border-indigo-900/50 dark:from-indigo-950/30 dark:via-background dark:to-teal-950/30"><CardContent className="p-6"><div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between"><div className="max-w-3xl space-y-3"><div className="flex items-center gap-2 text-indigo-700 dark:text-indigo-300"><Pill className="h-5 w-5" /><span className="text-sm font-semibold">Medication & Supply Operations</span></div><h2 className="text-2xl font-bold tracking-tight">من الكتالوج إلى صرف آمن قابل للتدقيق</h2><p className="text-sm leading-7 text-muted-foreground">تنظيم أصلي للمخزون حسب الموقع والدفعة والانتهاء، الوصفة المصادق عليها، الصرف، التحويلات، وإشعارات إعادة الطلب. البيانات اصطناعية ولا تُستخدم لتقديم توصية علاجية.</p><div className="flex flex-wrap gap-2"><Badge variant="success"><ShieldCheck className="ml-1 h-3.5 w-3.5" />عرض معزول</Badge><Badge variant="outline"><Database className="ml-1 h-3.5 w-3.5" />MedicationRequest-ready</Badge><Badge variant="outline"><History className="ml-1 h-3.5 w-3.5" />Audit-ready</Badge></div></div><div className="grid min-w-[290px] grid-cols-2 gap-3"><Metric label="أصناف الكتالوج" value={medications.length} icon={Tags} /><Metric label="تحت حد الطلب" value={lowStock} icon={Boxes} /><Metric label="انتهاء قريب" value={expiringSoon} icon={Clock3} /><Metric label="وصفات بانتظار الصرف" value={pendingDispense} icon={ClipboardList} /></div></div></CardContent></Card>

    <Card><CardContent className="p-0"><div className="flex flex-wrap border-b">{tabs.map((tab) => { const Icon = tab.icon; return <button key={tab.id} type="button" onClick={() => { setActiveTab(tab.id); setNotice(""); }} className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${activeTab === tab.id ? "border-b-2 border-indigo-600 text-indigo-700 dark:text-indigo-300" : "text-muted-foreground hover:text-foreground"}`}><Icon className="h-4 w-4" />{tab.label}</button>; })}</div></CardContent></Card>
    {notice && <div className="rounded-lg border border-indigo-200 bg-indigo-50 px-4 py-3 text-sm text-indigo-800 dark:border-indigo-900/60 dark:bg-indigo-950/30 dark:text-indigo-300" role="status"><CheckCircle2 className="ml-2 inline h-4 w-4" />{notice}</div>}

    {activeTab === "overview" && <Overview medications={medications} prescriptions={prescriptions} onTab={setActiveTab} />}
    {activeTab === "catalog" && <Catalog medications={filteredMedications} selected={selectedMedication} search={medicationSearch} onSearch={setMedicationSearch} onSelect={setSelectedMedicationId} onReceive={simulateReceive} />}
    {activeTab === "inventory" && <Inventory medications={filteredMedications} search={medicationSearch} onSearch={setMedicationSearch} onReceive={simulateReceive} />}
    {activeTab === "dispense" && <DispenseQueue prescriptions={filteredPrescriptions} search={prescriptionSearch} onSearch={setPrescriptionSearch} onDispense={simulateDispense} />}
    {activeTab === "movements" && <Movements movements={MOVEMENTS} />}
    {activeTab === "alerts" && <Alerts alerts={ALERTS} />}

    <Card className="border-amber-200 bg-amber-50/60 dark:border-amber-900/50 dark:bg-amber-950/20"><CardContent className="flex items-start gap-3 p-5 text-sm leading-7"><Info className="mt-1 h-5 w-5 shrink-0 text-amber-700 dark:text-amber-400" /><p><strong>حدود الدفعة الحالية:</strong> عمليات الاستلام والصرف محاكاة محلية فقط. الصرف الحقيقي يجب أن يتحقق من الوصفة والمريض والدواء والكمية والصلاحية والحساسية وصلاحية المستخدم، ثم يسجل MedicationRequest وMedicationDispense وAuditEvent في الخادم.</p></CardContent></Card>
  </div>;
}

function Metric({ label, value, icon: Icon }: { label: string; value: number; icon: typeof Pill }) { return <div className="rounded-xl bg-background/80 p-4 shadow-sm"><div className="flex items-center justify-between gap-2"><p className="text-xs text-muted-foreground">{label}</p><Icon className="h-4 w-4 text-indigo-600" /></div><p className="mt-1 text-2xl font-bold">{value}</p></div>; }

function Overview({ medications, prescriptions, onTab }: { medications: Medication[]; prescriptions: Prescription[]; onTab: (tab: PharmacyTab) => void }) { return <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(300px,0.8fr)]"><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><ShoppingCart className="h-5 w-5 text-indigo-600" />مسار الصيدلية الحالي</CardTitle></CardHeader><CardContent className="space-y-3">{[
  { label: "الكتالوج والمخزون", detail: `${medications.length} أصناف · ${medications.filter((item) => item.state === "متاح").length} متاحة`, icon: Tags, tab: "catalog" as PharmacyTab },
  { label: "الوصفات المصادق عليها", detail: `${prescriptions.filter((item) => item.state === "مصدق").length} وصفات`, icon: FileCheck2, tab: "dispense" as PharmacyTab },
  { label: "الصرف والتحقق", detail: `${prescriptions.filter((item) => item.state === "قيد الصرف").length} قيد الصرف`, icon: PackageCheck, tab: "dispense" as PharmacyTab },
  { label: "التوريد والتحويل", detail: "استلام وتحويل مع سجل حركة", icon: Truck, tab: "movements" as PharmacyTab },
].map((step, index) => { const Icon = step.icon; return <button key={step.label} type="button" onClick={() => onTab(step.tab)} className="flex w-full items-center gap-3 rounded-xl border p-4 text-right transition hover:border-indigo-300 hover:bg-indigo-50/40 dark:hover:bg-indigo-950/20"><span className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300">{index + 1}</span><span className="flex-1"><span className="block font-semibold">{step.label}</span><span className="mt-1 block text-xs text-muted-foreground">{step.detail}</span></span><Icon className="h-4 w-4 text-indigo-600" /><ArrowLeft className="h-4 w-4 text-muted-foreground" /></button>; })}</CardContent></Card><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><AlertTriangle className="h-5 w-5 text-amber-600" />تنبيهات تشغيلية</CardTitle></CardHeader><CardContent className="space-y-3"><AlertRow title="مخزون ميتفورمين منخفض" detail="318 وحدة · تحت حد إعادة الطلب" tone="warning" /><AlertRow title="وصفة موقوفة" detail="RX-260814-0047 · تحتاج مراجعة" tone="critical" /><AlertRow title="إنسولين قريب الانتهاء" detail="FEFO مطلوب قبل استلام دفعة جديدة" tone="warning" /><Link to="/pharmacy-operations" className="mt-2 inline-flex items-center gap-2 text-sm font-medium text-indigo-700 hover:underline dark:text-indigo-300">فتح مساحة الصيدلية <ArrowLeft className="h-4 w-4" /></Link></CardContent></Card></div>; }

function AlertRow({ title, detail, tone }: { title: string; detail: string; tone: "critical" | "warning" }) { return <div className={`rounded-xl border p-3 ${tone === "critical" ? "border-red-200 bg-red-50/70 dark:border-red-900/50 dark:bg-red-950/20" : "border-amber-200 bg-amber-50/70 dark:border-amber-900/50 dark:bg-amber-950/20"}`}><div className="flex items-center gap-2"><AlertTriangle className={`h-4 w-4 ${tone === "critical" ? "text-red-600" : "text-amber-600"}`} /><p className="text-sm font-semibold">{title}</p></div><p className="mt-1 text-xs text-muted-foreground">{detail}</p></div>; }

function Catalog({ medications, selected, search, onSearch, onSelect, onReceive }: { medications: Medication[]; selected?: Medication; search: string; onSearch: (value: string) => void; onSelect: (id: number) => void; onReceive: (id: number) => void }) { return <div className="grid gap-4 xl:grid-cols-[minmax(0,1.35fr)_minmax(300px,0.75fr)]"><Card><CardHeader><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><CardTitle className="text-base">كتالوج الأدوية</CardTitle><p className="mt-1 text-xs text-muted-foreground">بحث بالاسم العلمي أو التجاري أو الرمز أو التشغيلة.</p></div><SearchBox value={search} onChange={onSearch} placeholder="ابحث عن دواء..." /></div></CardHeader><CardContent className="space-y-2">{medications.map((medication) => <button key={medication.id} type="button" onClick={() => onSelect(medication.id)} className={`w-full rounded-xl border p-4 text-right transition hover:border-indigo-300 ${selected?.id === medication.id ? "border-indigo-400 bg-indigo-50/60 dark:border-indigo-700 dark:bg-indigo-950/25" : "border-border"}`}><div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">{medication.name} · {medication.strength}</p><p className="mt-1 text-xs text-muted-foreground">{medication.generic} · {medication.form} · {medication.code}</p></div><Badge variant={stockVariant(medication.state)}>{medication.state}</Badge></div><div className="mt-3 flex flex-wrap gap-4 text-xs text-muted-foreground"><span>{medication.onHand} وحدة</span><span>{medication.location}</span><span>انتهاء {medication.expiry}</span></div></button>)}{medications.length === 0 && <EmptyMessage text="لا يوجد دواء مطابق." />}</CardContent></Card><MedicationDetail medication={selected} onReceive={onReceive} /></div>; }

function MedicationDetail({ medication, onReceive }: { medication?: Medication; onReceive: (id: number) => void }) { if (!medication) return <Card><CardContent className="p-8 text-center text-sm text-muted-foreground">اختر صنفًا لعرض تفاصيله.</CardContent></Card>; return <Card><CardHeader><CardTitle className="text-base">بطاقة الدواء</CardTitle><p className="mt-1 text-sm text-muted-foreground">{medication.code}</p></CardHeader><CardContent className="space-y-4"><div><p className="text-lg font-bold">{medication.name}</p><p className="mt-1 text-sm text-muted-foreground">{medication.generic} · {medication.strength} · {medication.form}</p></div><div className="grid grid-cols-2 gap-3"><ValueBox label="الرصيد" value={`${medication.onHand} وحدة`} /><ValueBox label="حد الطلب" value={`${medication.reorderPoint} وحدة`} /><ValueBox label="التشغيلة" value={medication.lot} /><ValueBox label="الموقع" value={medication.location} /></div><div className="rounded-xl border border-indigo-100 bg-indigo-50/60 p-4 text-sm dark:border-indigo-900/50 dark:bg-indigo-950/20"><p className="font-semibold">تعريفات التكامل المستقبلية</p><p className="mt-1 text-xs leading-6 text-muted-foreground">ATC وRxNorm للهوية الدوائية، MedicationRequest للوصفة، MedicationDispense للصرف، وSupplyDelivery للحركة.</p></div><Button type="button" variant="outline" onClick={() => onReceive(medication.id)}><Plus className="h-4 w-4" />محاكاة استلام 100 وحدة</Button></CardContent></Card>; }

function Inventory({ medications, search, onSearch, onReceive }: { medications: Medication[]; search: string; onSearch: (value: string) => void; onReceive: (id: number) => void }) { return <Card><CardHeader><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><CardTitle className="text-base">المخزون حسب الموقع والتشغيلة</CardTitle><p className="mt-1 text-xs text-muted-foreground">عرض FEFO، الحد الأدنى، والموقع دون تعديل مخزون حقيقي.</p></div><SearchBox value={search} onChange={onSearch} placeholder="ابحث في المخزون..." /></div></CardHeader><CardContent className="space-y-2">{medications.map((medication) => <div key={medication.id} className="flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">{medication.name} · {medication.strength}</p><p className="mt-1 text-xs text-muted-foreground">{medication.lot} · {medication.location} · انتهاء {medication.expiry}</p></div><div className="flex flex-wrap items-center gap-2"><span className="rounded-lg bg-muted px-3 py-2 text-sm font-semibold">{medication.onHand} / حد {medication.reorderPoint}</span><Badge variant={stockVariant(medication.state)}>{medication.state}</Badge>{medication.state === "منخفض" && <Button size="sm" type="button" variant="outline" onClick={() => onReceive(medication.id)}>استلام محاكى</Button>}</div></div>)}{medications.length === 0 && <EmptyMessage text="لا يوجد صنف مطابق." />}</CardContent></Card>; }

function DispenseQueue({ prescriptions, search, onSearch, onDispense }: { prescriptions: Prescription[]; search: string; onSearch: (value: string) => void; onDispense: (id: number) => void }) { return <Card><CardHeader><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><CardTitle className="text-base">الوصفات والصرف</CardTitle><p className="mt-1 text-xs text-muted-foreground">وصفة مصادق عليها، حالة الصرف، المريض، الواصف، والكمية.</p></div><SearchBox value={search} onChange={onSearch} placeholder="ابحث بالوصفة أو المريض..." /></div></CardHeader><CardContent className="space-y-3">{prescriptions.map((prescription) => <div key={prescription.id} className="rounded-xl border p-4"><div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between"><div><p className="font-semibold">{prescription.number} · {prescription.patient}</p><p className="mt-1 text-xs text-muted-foreground">{prescription.medication} {prescription.strength} · {prescription.quantity} وحدة · {prescription.prescriber} · {prescription.requestedAt}</p></div><div className="flex items-center gap-2"><Badge variant={prescription.priority === "عاجل" ? "warning" : "outline"}>{prescription.priority}</Badge><Badge variant={prescriptionVariant(prescription.state)}>{prescription.state}</Badge>{(prescription.state === "مصدق" || prescription.state === "قيد الصرف") && <Button type="button" size="sm" onClick={() => onDispense(prescription.id)}><PackageCheck className="h-4 w-4" />محاكاة الصرف</Button>}</div></div><div className="mt-4 flex items-center gap-3 text-xs text-muted-foreground"><span className="flex items-center gap-1"><FileCheck2 className="h-3.5 w-3.5" />MedicationRequest</span><ArrowLeft className="h-3.5 w-3.5" /><span className="flex items-center gap-1"><PackageCheck className="h-3.5 w-3.5" />MedicationDispense</span></div></div>)}{prescriptions.length === 0 && <EmptyMessage text="لا توجد وصفة مطابقة." />}</CardContent></Card>; }

function Movements({ movements }: { movements: Movement[] }) { return <Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><ArrowRightLeft className="h-5 w-5 text-indigo-600" />سجل الحركات</CardTitle><p className="mt-1 text-xs text-muted-foreground">استلام وصرف وتحويل وتسوية مع المصدر والوجهة والتشغيلة.</p></CardHeader><CardContent className="space-y-2">{movements.map((movement) => <div key={movement.id} className="flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">{movement.medication} · {movement.quantity > 0 ? "+" : ""}{movement.quantity} وحدة</p><p className="mt-1 text-xs text-muted-foreground">{movement.lot} · {movement.from} ← {movement.to} · {movement.time}</p></div><Badge variant={movementVariant(movement.type)}>{movement.type}</Badge></div>)}</CardContent></Card>; }

function Alerts({ alerts }: { alerts: PharmacyAlert[] }) { return <div className="grid gap-3 md:grid-cols-2">{alerts.map((alert) => <Card key={alert.id} className={alert.tone === "critical" ? "border-red-200 dark:border-red-900/50" : alert.tone === "warning" ? "border-amber-200 dark:border-amber-900/50" : "border-sky-200 dark:border-sky-900/50"}><CardContent className="p-5"><div className="flex items-start gap-3"><AlertTriangle className={`mt-0.5 h-5 w-5 ${alert.tone === "critical" ? "text-red-600" : alert.tone === "warning" ? "text-amber-600" : "text-sky-600"}`} /><div className="flex-1"><div className="flex items-center justify-between gap-3"><p className="font-semibold">{alert.title}</p><Badge variant={alert.tone === "critical" ? "destructive" : alert.tone === "warning" ? "warning" : "outline"}>{alert.category}</Badge></div><p className="mt-2 text-sm leading-6 text-muted-foreground">{alert.detail}</p></div></div></CardContent></Card>)}</div>; }

function SearchBox({ value, onChange, placeholder }: { value: string; onChange: (value: string) => void; placeholder: string }) { return <div className="relative w-full sm:w-80"><Search className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" /><Input value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} className="pr-9" /></div>; }
function ValueBox({ label, value }: { label: string; value: string }) { return <div className="rounded-lg bg-muted/50 p-3"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 font-semibold">{value}</p></div>; }
function EmptyMessage({ text }: { text: string }) { return <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">{text}</div>; }
