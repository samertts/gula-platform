import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  ArrowLeft,
  BadgeDollarSign,
  CheckCircle2,
  ClipboardCheck,
  CreditCard,
  Database,
  FileCheck2,
  FileText,
  History,
  Info,
  Landmark,
  LifeBuoy,
  Plus,
  Receipt,
  RefreshCw,
  Search,
  ShieldCheck,
  Stethoscope,
  WalletCards,
} from "lucide-react";
import { PageHeader } from "@/components/shared/PageComponents";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type BillingTab = "overview" | "services" | "invoices" | "claims" | "insurance" | "payments" | "alerts";
type InvoiceState = "مسودة" | "جاهزة للإرسال" | "مُرسلة" | "مدفوعة" | "متأخرة";
type ClaimState = "مسودة" | "مُرسلة" | "مقبولة" | "مرفوضة" | "مدفوعة";
type CoverageState = "سارية" | "تنتهي قريبًا" | "منتهية" | "تحتاج تحقق";

type BillingService = {
  id: number;
  code: string;
  codeSystem: "خدمة داخلية" | "ICD-10-CM-ready" | "CPT-ready";
  name: string;
  group: string;
  amount: number;
  state: "نشطة" | "مراجعة";
};

type Invoice = {
  id: number;
  number: string;
  patient: string;
  encounter: string;
  serviceCount: number;
  grossAmount: number;
  coveredAmount: number;
  patientDue: number;
  state: InvoiceState;
  issuedAt: string;
  claimId?: string;
};

type Claim = {
  id: number;
  number: string;
  invoiceNumber: string;
  patient: string;
  payer: string;
  memberId: string;
  amount: number;
  state: ClaimState;
  submittedAt: string;
  updatedAt: string;
  reason?: string;
};

type InsurancePolicy = {
  id: number;
  patient: string;
  payer: string;
  plan: string;
  memberId: string;
  expires: string;
  state: CoverageState;
  verification: string;
  lastChecked: string;
};

type Payment = {
  id: number;
  invoiceNumber: string;
  patient: string;
  amount: number;
  method: "تسوية محاكاة" | "مراجعة داخلية" | "تغطية تأمينية";
  recordedAt: string;
  reference: string;
};

type BillingAlert = {
  id: number;
  title: string;
  detail: string;
  tone: "critical" | "warning" | "info";
  category: string;
};

const INITIAL_SERVICES: BillingService[] = [
  { id: 1, code: "GULA-SVC-001", codeSystem: "CPT-ready", name: "زيارة عيادة عامة", group: "زيارات", amount: 180, state: "نشطة" },
  { id: 2, code: "GULA-SVC-014", codeSystem: "CPT-ready", name: "متابعة رعاية مزمنة", group: "زيارات", amount: 240, state: "نشطة" },
  { id: 3, code: "GULA-LAB-022", codeSystem: "خدمة داخلية", name: "لوحة تحاليل أساسية", group: "مختبر", amount: 95, state: "نشطة" },
  { id: 4, code: "GULA-DX-007", codeSystem: "ICD-10-CM-ready", name: "تشخيص تنفسي توضيحي", group: "تشخيصات", amount: 0, state: "مراجعة" },
  { id: 5, code: "GULA-RAD-009", codeSystem: "CPT-ready", name: "تصوير تشخيصي أولي", group: "تصوير", amount: 320, state: "نشطة" },
];

const INITIAL_INVOICES: Invoice[] = [
  { id: 1, number: "INV-260814-011", patient: "سارة عبد الرحمن", encounter: "ENC-260814-092", serviceCount: 2, grossAmount: 275, coveredAmount: 220, patientDue: 55, state: "جاهزة للإرسال", issuedAt: "14 أغسطس 2026", claimId: "CLM-260814-018" },
  { id: 2, number: "INV-260814-009", patient: "حسن نوري", encounter: "ENC-260814-087", serviceCount: 1, grossAmount: 180, coveredAmount: 180, patientDue: 0, state: "مُرسلة", issuedAt: "14 أغسطس 2026", claimId: "CLM-260814-016" },
  { id: 3, number: "INV-260813-044", patient: "مريم فاضل", encounter: "ENC-260813-231", serviceCount: 3, grossAmount: 415, coveredAmount: 0, patientDue: 415, state: "متأخرة", issuedAt: "13 أغسطس 2026" },
  { id: 4, number: "INV-260812-031", patient: "علي كريم حسن", encounter: "ENC-260812-144", serviceCount: 2, grossAmount: 275, coveredAmount: 220, patientDue: 55, state: "مدفوعة", issuedAt: "12 أغسطس 2026", claimId: "CLM-260812-007" },
];

const INITIAL_CLAIMS: Claim[] = [
  { id: 1, number: "CLM-260814-018", invoiceNumber: "INV-260814-011", patient: "سارة عبد الرحمن", payer: "صندوق الرعاية الوطني التجريبي", memberId: "MBR-SYN-1044", amount: 220, state: "مسودة", submittedAt: "لم تُرسل", updatedAt: "09:28" },
  { id: 2, number: "CLM-260814-016", invoiceNumber: "INV-260814-009", patient: "حسن نوري", payer: "تأمين المدن النموذجي", memberId: "MBR-SYN-0881", amount: 180, state: "مُرسلة", submittedAt: "14 أغسطس 2026 09:02", updatedAt: "09:02" },
  { id: 3, number: "CLM-260813-013", invoiceNumber: "INV-260813-044", patient: "مريم فاضل", payer: "خطة الحماية الصحية التجريبية", memberId: "MBR-SYN-0720", amount: 280, state: "مرفوضة", submittedAt: "13 أغسطس 2026 15:10", updatedAt: "13 أغسطس 2026 15:42", reason: "بيانات التغطية تحتاج مراجعة محلية" },
  { id: 4, number: "CLM-260812-007", invoiceNumber: "INV-260812-031", patient: "علي كريم حسن", payer: "صندوق الرعاية الوطني التجريبي", memberId: "MBR-SYN-0328", amount: 220, state: "مدفوعة", submittedAt: "12 أغسطس 2026 10:14", updatedAt: "12 أغسطس 2026 13:05" },
];

const INITIAL_POLICIES: InsurancePolicy[] = [
  { id: 1, patient: "سارة عبد الرحمن", payer: "صندوق الرعاية الوطني التجريبي", plan: "أساسي-أ", memberId: "MBR-SYN-1044", expires: "2027-02-28", state: "سارية", verification: "تمت مطابقة البيانات محليًا", lastChecked: "09:12" },
  { id: 2, patient: "حسن نوري", payer: "تأمين المدن النموذجي", plan: "شبكة-ب", memberId: "MBR-SYN-0881", expires: "2026-09-18", state: "تنتهي قريبًا", verification: "تحتاج إعادة تحقق قبل الإرسال", lastChecked: "أمس 16:40" },
  { id: 3, patient: "مريم فاضل", payer: "خطة الحماية الصحية التجريبية", plan: "أساسي-ج", memberId: "MBR-SYN-0720", expires: "2026-07-31", state: "منتهية", verification: "لا توجد تغطية محلية صالحة", lastChecked: "13 أغسطس 2026" },
  { id: 4, patient: "علي كريم حسن", payer: "صندوق الرعاية الوطني التجريبي", plan: "أساسي-أ", memberId: "MBR-SYN-0328", expires: "2026-12-12", state: "تحتاج تحقق", verification: "لم يتم تشغيل تحقق محلي لهذه الزيارة", lastChecked: "لم يُتحقق" },
];

const INITIAL_PAYMENTS: Payment[] = [
  { id: 1, invoiceNumber: "INV-260812-031", patient: "علي كريم حسن", amount: 55, method: "تسوية محاكاة", recordedAt: "12 أغسطس 2026 13:08", reference: "PAY-SYN-0021" },
  { id: 2, invoiceNumber: "INV-260812-031", patient: "علي كريم حسن", amount: 220, method: "تغطية تأمينية", recordedAt: "12 أغسطس 2026 13:05", reference: "EOB-SYN-0007" },
  { id: 3, invoiceNumber: "INV-260814-009", patient: "حسن نوري", amount: 180, method: "تغطية تأمينية", recordedAt: "بانتظار التسوية", reference: "CLAIM-SYN-016" },
];

const ALERTS: BillingAlert[] = [
  { id: 1, title: "مطالبة مرفوضة تحتاج مراجعة", detail: "CLM-260813-013 · بيانات التغطية لا تطابق قواعد التحقق المحلية", tone: "critical", category: "مطالبات" },
  { id: 2, title: "بطاقة تأمين تنتهي قريبًا", detail: "حسن نوري · تنتهي في 2026-09-18 · أعد التحقق قبل الإرسال", tone: "warning", category: "تأمين" },
  { id: 3, title: "فاتورة متأخرة", detail: "INV-260813-044 · رصيد المريض 415 وحدة حسابية اصطناعية", tone: "warning", category: "مستحقات" },
  { id: 4, title: "كتالوج الخدمة يحتاج ربطًا محليًا", detail: "GULA-SVC-001 · حقول CPT/ICD-10-CM معروضة كجاهزة للتكامل فقط", tone: "info", category: "ترميز" },
];

const tabs: Array<{ id: BillingTab; label: string; icon: typeof Receipt }> = [
  { id: "overview", label: "نظرة الفوترة", icon: BadgeDollarSign },
  { id: "services", label: "كتالوج الخدمات", icon: Stethoscope },
  { id: "invoices", label: "الفواتير", icon: Receipt },
  { id: "claims", label: "المطالبات", icon: FileCheck2 },
  { id: "insurance", label: "التأمين والتحقق", icon: ShieldCheck },
  { id: "payments", label: "المدفوعات والمستحقات", icon: WalletCards },
  { id: "alerts", label: "التنبيهات", icon: AlertTriangle },
];

const invoiceVariant = (state: InvoiceState): "success" | "warning" | "destructive" | "outline" | "secondary" => state === "مدفوعة" ? "success" : state === "متأخرة" ? "destructive" : state === "مُرسلة" ? "secondary" : state === "جاهزة للإرسال" ? "warning" : "outline";
const claimVariant = (state: ClaimState): "success" | "warning" | "destructive" | "outline" | "secondary" => state === "مدفوعة" || state === "مقبولة" ? "success" : state === "مرفوضة" ? "destructive" : state === "مُرسلة" ? "secondary" : state === "مسودة" ? "outline" : "warning";
const coverageVariant = (state: CoverageState): "success" | "warning" | "destructive" | "outline" => state === "سارية" ? "success" : state === "منتهية" ? "destructive" : state === "تنتهي قريبًا" ? "warning" : "outline";

export default function BillingInsuranceWorkspacePage() {
  const [activeTab, setActiveTab] = useState<BillingTab>("overview");
  const [services] = useState(INITIAL_SERVICES);
  const [invoices, setInvoices] = useState(INITIAL_INVOICES);
  const [claims, setClaims] = useState(INITIAL_CLAIMS);
  const [policies, setPolicies] = useState(INITIAL_POLICIES);
  const [payments, setPayments] = useState(INITIAL_PAYMENTS);
  const [search, setSearch] = useState("");
  const [notice, setNotice] = useState("");

  const term = search.trim().toLocaleLowerCase("ar");
  const filteredServices = useMemo(() => !term ? services : services.filter((item) => `${item.code} ${item.name} ${item.group} ${item.codeSystem}`.toLocaleLowerCase("ar").includes(term)), [services, term]);
  const filteredInvoices = useMemo(() => !term ? invoices : invoices.filter((item) => `${item.number} ${item.patient} ${item.encounter} ${item.state}`.toLocaleLowerCase("ar").includes(term)), [invoices, term]);
  const filteredClaims = useMemo(() => !term ? claims : claims.filter((item) => `${item.number} ${item.invoiceNumber} ${item.patient} ${item.payer} ${item.memberId} ${item.state}`.toLocaleLowerCase("ar").includes(term)), [claims, term]);
  const filteredPolicies = useMemo(() => !term ? policies : policies.filter((item) => `${item.patient} ${item.payer} ${item.plan} ${item.memberId} ${item.state}`.toLocaleLowerCase("ar").includes(term)), [policies, term]);

  const selectTab = (tab: BillingTab) => {
    setActiveTab(tab);
    setSearch("");
    setNotice("");
  };

  const openInvoices = invoices.filter((invoice) => invoice.state !== "مدفوعة").length;
  const outstanding = invoices.filter((invoice) => invoice.state !== "مدفوعة").reduce((total, invoice) => total + invoice.patientDue, 0);
  const rejectedClaims = claims.filter((claim) => claim.state === "مرفوضة").length;
  const pendingVerification = policies.filter((policy) => policy.state !== "سارية").length;

  const createInvoice = () => {
    const nextId = invoices.length + 1;
    setInvoices((current) => [{ id: nextId, number: `INV-260814-${String(11 + nextId).padStart(3, "0")}`, patient: "مريض اصطناعي جديد", encounter: `ENC-SYN-${String(200 + nextId)}`, serviceCount: 1, grossAmount: 180, coveredAmount: 0, patientDue: 180, state: "مسودة", issuedAt: "14 أغسطس 2026" }, ...current]);
    setNotice("تم إنشاء فاتورة اصطناعية محليًا؛ لم يتم ربطها بزيارة حقيقية أو إنشاء مطالبة خارجية.");
    selectTab("invoices");
  };

  const advanceClaim = (claimId: number) => {
    setClaims((current) => current.map((claim) => {
      if (claim.id !== claimId) return claim;
      const nextState: ClaimState = claim.state === "مسودة" ? "مُرسلة" : claim.state === "مُرسلة" ? "مقبولة" : claim.state === "مقبولة" ? "مدفوعة" : claim.state === "مرفوضة" ? "مُرسلة" : "مدفوعة";
      return { ...claim, state: nextState, submittedAt: nextState === "مُرسلة" && claim.submittedAt === "لم تُرسل" ? "14 أغسطس 2026 09:34" : claim.submittedAt, updatedAt: "الآن", reason: nextState === "مُرسلة" ? undefined : claim.reason };
    }));
    setNotice("تمت محاكاة انتقال المطالبة محليًا. لم تُرسل أي مطالبة إلى شركة تأمين أو clearinghouse.");
  };

  const simulatePayment = (invoice: Invoice) => {
    setInvoices((current) => current.map((item) => item.id === invoice.id ? { ...item, state: "مدفوعة" } : item));
    if (invoice.claimId) setClaims((current) => current.map((claim) => claim.number === invoice.claimId ? { ...claim, state: "مدفوعة", updatedAt: "الآن" } : claim));
    setPayments((current) => [{ id: current.length + 1, invoiceNumber: invoice.number, patient: invoice.patient, amount: invoice.patientDue || invoice.coveredAmount, method: "تسوية محاكاة", recordedAt: "14 أغسطس 2026 الآن", reference: `PAY-SYN-${String(current.length + 22).padStart(4, "0")}` }, ...current]);
    setNotice("تمت محاكاة تسجيل التسوية محليًا؛ لا توجد عملية دفع أو تحويل مالي حقيقي.");
  };

  const verifyPolicy = (policyId: number) => {
    setPolicies((current) => current.map((policy) => policy.id === policyId ? { ...policy, state: "سارية", verification: "تمت المطابقة في سجل تجريبي محلي", lastChecked: "الآن" } : policy));
    setNotice("تمت محاكاة التحقق من بطاقة التأمين داخل GULA فقط، دون الاتصال بجهة تأمين خارجية.");
  };

  return <div className="mx-auto max-w-7xl space-y-6" dir="rtl">
    <PageHeader title="إدارة الفوترة والتأمين الصحي" description="مساحة GULA الأصلية للفواتير والمطالبات والتغطية والمدفوعات الاصطناعية، مستلهمة من OpenEMR وFreeMED وopenIMIS دون نسخ كود أو واجهات." />

    <Card className="overflow-hidden border-emerald-200 bg-gradient-to-l from-emerald-50 via-white to-cyan-50 dark:border-emerald-900/50 dark:from-emerald-950/30 dark:via-background dark:to-cyan-950/30"><CardContent className="p-6"><div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between"><div className="max-w-3xl space-y-3"><div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-300"><BadgeDollarSign className="h-5 w-5" /><span className="text-sm font-semibold">Billing & Insurance Operations</span></div><h2 className="text-2xl font-bold tracking-tight">من الزيارة إلى مطالبة قابلة للتدقيق</h2><p className="text-sm leading-7 text-muted-foreground">تنظيم أصلي لكتالوج الخدمات والفواتير وبطاقات التأمين ومسار المطالبة وسجل المستحقات. كل المبالغ والجهات والمراجع في هذه الشاشة اصطناعية للعرض والتخطيط فقط.</p><div className="flex flex-wrap gap-2"><Badge variant="success"><ShieldCheck className="ml-1 h-3.5 w-3.5" />عرض معزول</Badge><Badge variant="outline"><Database className="ml-1 h-3.5 w-3.5" />FHIR Claim-ready</Badge><Badge variant="outline"><History className="ml-1 h-3.5 w-3.5" />Audit-ready</Badge></div></div><div className="grid min-w-[300px] grid-cols-2 gap-3"><Metric label="فواتير مفتوحة" value={openInvoices} icon={Receipt} /><Metric label="مستحقات مفتوحة" value={`${outstanding} وحدة`} icon={WalletCards} /><Metric label="مطالبات مرفوضة" value={rejectedClaims} icon={AlertTriangle} /><Metric label="تحتاج تحقق تأميني" value={pendingVerification} icon={ShieldCheck} /></div></div></CardContent></Card>

    <div className="flex flex-col gap-3 rounded-xl border border-emerald-200 bg-emerald-50/70 p-4 text-sm leading-7 text-emerald-950 dark:border-emerald-900/50 dark:bg-emerald-950/20 dark:text-emerald-100"><div className="flex items-start gap-3"><Info className="mt-1 h-5 w-5 shrink-0" /><p><strong>نطاق الدفعة:</strong> لا توجد بوابة دفع، ولا إرسال EDI، ولا تحقق من شركة تأمين حقيقية. الحالات والأرقام محاكاة محلية، ويجب ربطها لاحقًا بعقود قانونية وفنية معتمدة وسجل تدقيق خادمي.</p></div><div className="flex flex-wrap gap-3"><Link to="/patient-management" className="inline-flex items-center gap-1 font-medium underline underline-offset-4">فتح دليل المرضى <ArrowLeft className="h-4 w-4" /></Link><Link to="/lab-operations" className="inline-flex items-center gap-1 font-medium underline underline-offset-4">فتح عمليات المختبر <ArrowLeft className="h-4 w-4" /></Link></div></div>

    <Card><CardContent className="p-0"><div className="flex flex-wrap border-b">{tabs.map((tab) => { const Icon = tab.icon; return <button key={tab.id} type="button" onClick={() => selectTab(tab.id)} className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${activeTab === tab.id ? "border-b-2 border-emerald-600 text-emerald-700 dark:text-emerald-300" : "text-muted-foreground hover:text-foreground"}`}><Icon className="h-4 w-4" />{tab.label}</button>; })}</div></CardContent></Card>
    {notice && <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800 dark:border-emerald-900/60 dark:bg-emerald-950/30 dark:text-emerald-300" role="status"><CheckCircle2 className="ml-2 inline h-4 w-4" />{notice}</div>}

    {activeTab === "overview" && <Overview invoices={invoices} claims={claims} policies={policies} onTab={selectTab} onCreateInvoice={createInvoice} />}
    {activeTab === "services" && <Services services={filteredServices} search={search} onSearch={setSearch} />}
    {activeTab === "invoices" && <Invoices invoices={filteredInvoices} search={search} onSearch={setSearch} onCreateInvoice={createInvoice} onPayment={simulatePayment} />}
    {activeTab === "claims" && <Claims claims={filteredClaims} search={search} onSearch={setSearch} onAdvance={advanceClaim} />}
    {activeTab === "insurance" && <Insurance policies={filteredPolicies} search={search} onSearch={setSearch} onVerify={verifyPolicy} />}
    {activeTab === "payments" && <Payments payments={payments} />}
    {activeTab === "alerts" && <Alerts alerts={ALERTS} />}

    <Card className="border-amber-200 bg-amber-50/60 dark:border-amber-900/50 dark:bg-amber-950/20"><CardContent className="flex items-start gap-3 p-5 text-sm leading-7"><LifeBuoy className="mt-1 h-5 w-5 shrink-0 text-amber-700 dark:text-amber-400" /><p><strong>حدود الامتثال:</strong> هذه الوحدة لا تقدم ترميزًا سريريًا أو قرارًا حول الاستحقاق، ولا تتحقق من تغطية حقيقية، ولا تسجل مدفوعات فعلية. قبل التشغيل، يجب إضافة تفويضات دقيقة، تشفير، فصل صلاحيات، قواعد سوق محلية، ومراجعة قانونية ومالية.</p></CardContent></Card>
  </div>;
}

function Metric({ label, value, icon: Icon }: { label: string; value: number | string; icon: typeof Receipt }) { return <div className="rounded-xl bg-background/80 p-4 shadow-sm"><div className="flex items-center justify-between gap-2"><p className="text-xs text-muted-foreground">{label}</p><Icon className="h-4 w-4 text-emerald-600" /></div><p className="mt-1 text-2xl font-bold">{value}</p></div>; }

function Overview({ invoices, claims, policies, onTab, onCreateInvoice }: { invoices: Invoice[]; claims: Claim[]; policies: InsurancePolicy[]; onTab: (tab: BillingTab) => void; onCreateInvoice: () => void }) { return <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(300px,0.8fr)]"><Card><CardHeader><div className="flex items-center justify-between gap-3"><CardTitle className="flex items-center gap-2 text-base"><Landmark className="h-5 w-5 text-emerald-600" />مسار الفوترة الحالي</CardTitle><Button type="button" size="sm" onClick={onCreateInvoice}><Plus className="h-4 w-4" />فاتورة محاكاة</Button></div></CardHeader><CardContent className="space-y-3">{[
  { label: "الخدمات والفاتورة", detail: `${invoices.length} فواتير · ${invoices.filter((item) => item.state === "مسودة").length} مسودة`, icon: FileText, tab: "invoices" as BillingTab },
  { label: "بطاقة التأمين والتحقق", detail: `${policies.filter((item) => item.state === "سارية").length} بطاقات سارية`, icon: ShieldCheck, tab: "insurance" as BillingTab },
  { label: "المطالبة والتدقيق", detail: `${claims.filter((item) => item.state === "مُرسلة" || item.state === "مسودة").length} في المسار`, icon: ClipboardCheck, tab: "claims" as BillingTab },
  { label: "التسوية والمستحقات", detail: `${invoices.filter((item) => item.state === "متأخرة").length} فواتير متأخرة`, icon: CreditCard, tab: "payments" as BillingTab },
].map((step, index) => { const Icon = step.icon; return <button key={step.label} type="button" onClick={() => onTab(step.tab)} className="flex w-full items-center gap-3 rounded-xl border p-4 text-right transition hover:border-emerald-300 hover:bg-emerald-50/40 dark:hover:bg-emerald-950/20"><span className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">{index + 1}</span><span className="flex-1"><span className="block font-semibold">{step.label}</span><span className="mt-1 block text-xs text-muted-foreground">{step.detail}</span></span><Icon className="h-4 w-4 text-emerald-600" /><ArrowLeft className="h-4 w-4 text-muted-foreground" /></button>; })}</CardContent></Card><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><AlertTriangle className="h-5 w-5 text-amber-600" />مؤشرات تحتاج انتباهًا</CardTitle></CardHeader><CardContent className="space-y-3"><AlertRow title="مطالبة مرفوضة" detail="CLM-260813-013 · راجع بيانات التغطية" tone="critical" /><AlertRow title="تأمين قريب الانتهاء" detail="حسن نوري · تحقق قبل إرسال المطالبة" tone="warning" /><AlertRow title="فاتورة متأخرة" detail="INV-260813-044 · رصيد اصطناعي 415" tone="warning" /><button type="button" onClick={() => onTab("alerts")} className="mt-2 inline-flex items-center gap-2 text-sm font-medium text-emerald-700 hover:underline dark:text-emerald-300">فتح مركز التنبيهات <ArrowLeft className="h-4 w-4" /></button></CardContent></Card></div>; }

function Services({ services, search, onSearch }: { services: BillingService[]; search: string; onSearch: (value: string) => void }) { return <Card><CardHeader><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><CardTitle className="text-base">كتالوج الخدمات والترميز المستقبلي</CardTitle><p className="mt-1 text-xs text-muted-foreground">معرفات GULA داخلية؛ حقول CPT وICD-10-CM جاهزة للتكامل المحلي وليست كتالوجًا قانونيًا مكتملًا.</p></div><SearchBox value={search} onChange={onSearch} placeholder="ابحث عن خدمة أو معرف..." /></div></CardHeader><CardContent className="space-y-2">{services.map((service) => <div key={service.id} className="flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">{service.name}</p><p className="mt-1 text-xs text-muted-foreground">{service.code} · {service.group} · {service.codeSystem}</p></div><div className="flex flex-wrap items-center gap-2"><span className="rounded-lg bg-muted px-3 py-2 text-sm font-semibold">{service.amount ? `${service.amount} وحدة` : "تشخيص بلا قيمة مالية"}</span><Badge variant={service.state === "نشطة" ? "success" : "warning"}>{service.state}</Badge></div></div>)}{services.length === 0 && <EmptyMessage text="لا توجد خدمة مطابقة." />}</CardContent></Card>; }

function Invoices({ invoices, search, onSearch, onCreateInvoice, onPayment }: { invoices: Invoice[]; search: string; onSearch: (value: string) => void; onCreateInvoice: () => void; onPayment: (invoice: Invoice) => void }) { return <Card><CardHeader><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><CardTitle className="text-base">الفواتير المرتبطة بالزيارة</CardTitle><p className="mt-1 text-xs text-muted-foreground">المريض والزيارة والخدمات والتغطية والمستحقات في سجل اصطناعي قابل للمراجعة.</p></div><div className="flex flex-wrap gap-2"><SearchBox value={search} onChange={onSearch} placeholder="ابحث بالفاتورة أو المريض..." /><Button type="button" size="sm" variant="outline" onClick={onCreateInvoice}><Plus className="h-4 w-4" />إنشاء مسودة</Button></div></div></CardHeader><CardContent className="space-y-3">{invoices.map((invoice) => <div key={invoice.id} className="rounded-xl border p-4"><div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between"><div><p className="font-semibold">{invoice.number} · {invoice.patient}</p><p className="mt-1 text-xs text-muted-foreground">{invoice.encounter} · {invoice.serviceCount} خدمات · إصدار {invoice.issuedAt}</p></div><div className="flex flex-wrap items-center gap-2"><Badge variant={invoiceVariant(invoice.state)}>{invoice.state}</Badge>{invoice.state !== "مدفوعة" && <Button type="button" size="sm" onClick={() => onPayment(invoice)}><CreditCard className="h-4 w-4" />محاكاة التسوية</Button>}</div></div><div className="mt-4 grid gap-2 sm:grid-cols-3"><ValueBox label="الإجمالي" value={`${invoice.grossAmount} وحدة`} /><ValueBox label="التغطية" value={`${invoice.coveredAmount} وحدة`} /><ValueBox label="على المريض" value={`${invoice.patientDue} وحدة`} /></div><div className="mt-3 flex flex-wrap gap-3 text-xs text-muted-foreground"><span className="flex items-center gap-1"><FileText className="h-3.5 w-3.5" />Encounter {invoice.encounter}</span>{invoice.claimId && <span className="flex items-center gap-1"><FileCheck2 className="h-3.5 w-3.5" />Claim {invoice.claimId}</span>}</div></div>)}{invoices.length === 0 && <EmptyMessage text="لا توجد فاتورة مطابقة." />}</CardContent></Card>; }

function Claims({ claims, search, onSearch, onAdvance }: { claims: Claim[]; search: string; onSearch: (value: string) => void; onAdvance: (id: number) => void }) { return <Card><CardHeader><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><CardTitle className="text-base">دورة المطالبات</CardTitle><p className="mt-1 text-xs text-muted-foreground">مسودة، إرسال محلي، قبول أو رفض، ثم تسوية محاكاة؛ لا يوجد clearinghouse أو إرسال خارجي.</p></div><SearchBox value={search} onChange={onSearch} placeholder="ابحث بالمطالبة أو الدافع..." /></div></CardHeader><CardContent className="space-y-3">{claims.map((claim) => <div key={claim.id} className="rounded-xl border p-4"><div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between"><div><p className="font-semibold">{claim.number} · {claim.patient}</p><p className="mt-1 text-xs text-muted-foreground">{claim.invoiceNumber} · {claim.payer} · Member {claim.memberId}</p></div><div className="flex items-center gap-2"><Badge variant={claimVariant(claim.state)}>{claim.state}</Badge>{claim.state !== "مدفوعة" && <Button type="button" size="sm" variant={claim.state === "مرفوضة" ? "outline" : "default"} onClick={() => onAdvance(claim.id)}>{claim.state === "مرفوضة" ? <RefreshCw className="h-4 w-4" /> : <FileCheck2 className="h-4 w-4" />}{claim.state === "مرفوضة" ? "إعادة معالجة محاكاة" : claim.state === "مقبولة" ? "محاكاة التسوية" : "نقل الحالة"}</Button>}</div></div><div className="mt-4 grid gap-2 sm:grid-cols-3"><ValueBox label="المبلغ" value={`${claim.amount} وحدة`} /><ValueBox label="آخر تحديث" value={claim.updatedAt} /><ValueBox label="الإرسال" value={claim.submittedAt} /></div>{claim.reason && <div className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800 dark:border-red-900/50 dark:bg-red-950/20 dark:text-red-300"><AlertTriangle className="ml-1 inline h-3.5 w-3.5" />{claim.reason}</div>}</div>)}{claims.length === 0 && <EmptyMessage text="لا توجد مطالبة مطابقة." />}</CardContent></Card>; }

function Insurance({ policies, search, onSearch, onVerify }: { policies: InsurancePolicy[]; search: string; onSearch: (value: string) => void; onVerify: (id: number) => void }) { return <Card><CardHeader><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><CardTitle className="text-base">بطاقات التأمين والتحقق</CardTitle><p className="mt-1 text-xs text-muted-foreground">تسجيل اصطناعي للعضوية والخطة وتاريخ الانتهاء ونتيجة التحقق المحلي.</p></div><SearchBox value={search} onChange={onSearch} placeholder="ابحث بالمريض أو العضوية..." /></div></CardHeader><CardContent className="space-y-3">{policies.map((policy) => <div key={policy.id} className="rounded-xl border p-4"><div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between"><div><p className="font-semibold">{policy.patient} · {policy.payer}</p><p className="mt-1 text-xs text-muted-foreground">{policy.plan} · Member {policy.memberId} · انتهاء {policy.expires}</p></div><div className="flex items-center gap-2"><Badge variant={coverageVariant(policy.state)}>{policy.state}</Badge>{policy.state !== "سارية" && <Button type="button" size="sm" variant="outline" onClick={() => onVerify(policy.id)}><ShieldCheck className="h-4 w-4" />تحقق محلي</Button>}</div></div><div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-muted-foreground"><span className="flex items-center gap-1"><ClipboardCheck className="h-3.5 w-3.5" />{policy.verification}</span><span>آخر تحقق: {policy.lastChecked}</span></div></div>)}{policies.length === 0 && <EmptyMessage text="لا توجد بطاقة تأمين مطابقة." />}</CardContent></Card>; }

function Payments({ payments }: { payments: Payment[] }) { return <Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><WalletCards className="h-5 w-5 text-emerald-600" />سجل المدفوعات والمستحقات</CardTitle><p className="mt-1 text-xs text-muted-foreground">سجل عرضي اصطناعي يميز التغطية التأمينية عن التسوية المحاكية دون حركة مالية حقيقية.</p></CardHeader><CardContent className="space-y-2">{payments.map((payment) => <div key={payment.id} className="flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">{payment.invoiceNumber} · {payment.patient}</p><p className="mt-1 text-xs text-muted-foreground">{payment.reference} · {payment.recordedAt}</p></div><div className="flex items-center gap-2"><span className="rounded-lg bg-muted px-3 py-2 text-sm font-semibold">{payment.amount} وحدة</span><Badge variant={payment.method === "تغطية تأمينية" ? "secondary" : "outline"}>{payment.method}</Badge></div></div>)}{payments.length === 0 && <EmptyMessage text="لا توجد حركة مالية اصطناعية." />}</CardContent></Card>; }

function Alerts({ alerts }: { alerts: BillingAlert[] }) { return <div className="grid gap-3 md:grid-cols-2">{alerts.map((alert) => <Card key={alert.id} className={alert.tone === "critical" ? "border-red-200 dark:border-red-900/50" : alert.tone === "warning" ? "border-amber-200 dark:border-amber-900/50" : "border-sky-200 dark:border-sky-900/50"}><CardContent className="p-5"><div className="flex items-start gap-3"><AlertTriangle className={`mt-0.5 h-5 w-5 ${alert.tone === "critical" ? "text-red-600" : alert.tone === "warning" ? "text-amber-600" : "text-sky-600"}`} /><div className="flex-1"><div className="flex items-center justify-between gap-3"><p className="font-semibold">{alert.title}</p><Badge variant={alert.tone === "critical" ? "destructive" : alert.tone === "warning" ? "warning" : "outline"}>{alert.category}</Badge></div><p className="mt-2 text-sm leading-6 text-muted-foreground">{alert.detail}</p></div></div></CardContent></Card>)}</div>; }

function AlertRow({ title, detail, tone }: { title: string; detail: string; tone: "critical" | "warning" }) { return <div className={`rounded-xl border p-3 ${tone === "critical" ? "border-red-200 bg-red-50/70 dark:border-red-900/50 dark:bg-red-950/20" : "border-amber-200 bg-amber-50/70 dark:border-amber-900/50 dark:bg-amber-950/20"}`}><div className="flex items-center gap-2"><AlertTriangle className={`h-4 w-4 ${tone === "critical" ? "text-red-600" : "text-amber-600"}`} /><p className="text-sm font-semibold">{title}</p></div><p className="mt-1 text-xs text-muted-foreground">{detail}</p></div>; }
function SearchBox({ value, onChange, placeholder }: { value: string; onChange: (value: string) => void; placeholder: string }) { return <div className="relative w-full sm:w-80"><Search className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" /><Input value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} className="pr-9" /></div>; }
function ValueBox({ label, value }: { label: string; value: string }) { return <div className="rounded-lg bg-muted/50 p-3"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 font-semibold">{value}</p></div>; }
function EmptyMessage({ text }: { text: string }) { return <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">{text}</div>; }
