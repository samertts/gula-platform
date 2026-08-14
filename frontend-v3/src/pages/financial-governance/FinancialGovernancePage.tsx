import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Database,
  FileCheck2,
  History,
  Landmark,
  LockKeyhole,
  RefreshCw,
  Scale,
  ShieldCheck,
  WalletCards,
} from "lucide-react";
import { financialControlApi, type FinancialControlRequestRecord, type FinancialControlSummaryRecord } from "@/api/endpoints";
import { useAuth } from "@/contexts/AuthContext";
import { PageHeader } from "@/components/shared/PageComponents";
import { Badge } from "@/components/ui/Badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

const SYNTHETIC_SUMMARY: FinancialControlSummaryRecord = {
  institution_id: 0,
  as_of: "2026-08-14T00:00:00Z",
  currency: "IQD",
  billed_amount: "1250000.00",
  collected_amount: "930000.00",
  outstanding_amount: "320000.00",
  refunded_amount: "15000.00",
  invoice_count: 128,
  control_requests: { REQUESTED: 2, APPROVED: 1, APPLIED: 6, REJECTED: 1 },
  open_reconciliation_cases: 1,
  cash_variance_cases: 0,
  live_operation_enabled: false,
  external_provider_calls: 0,
  data_basis: "سجل مالي اصطناعي معزول للمعاينة فقط",
  limitations: ["لا توجد توقعات أو تقييم أو عائد استثماري", "المزودون الخارجيون معطلون", "تحتاج الأرقام إلى مصدر backend قبل التشغيل"],
};

const SYNTHETIC_REQUESTS: FinancialControlRequestRecord[] = [
  { id: "ctl-syn-001", institution_id: 0, control_type: "provider_approval", resource_type: "payment_provider", resource_id: "provider-sandbox", requested_action: "approve_for_advisory_routing", status: "REQUESTED", reason: "مراجعة فصلية اصطناعية", requested_by: 21, approved_by: null, applied_by: null, external_operation: false, requested_at: "2026-08-14T08:15:00Z" },
  { id: "ctl-syn-002", institution_id: 0, control_type: "refund_approval", resource_type: "payment_refund", resource_id: "refund-sandbox", requested_action: "approve_refund", status: "APPROVED", reason: "مطابقة داخلية مكتملة", requested_by: 18, approved_by: 22, applied_by: null, external_operation: false, requested_at: "2026-08-14T07:45:00Z", approved_at: "2026-08-14T08:05:00Z" },
  { id: "ctl-syn-003", institution_id: 0, control_type: "routing_rule_activation", resource_type: "routing_rule", resource_id: "rule-sandbox-v3", requested_action: "activate_advisory_rule", status: "APPLIED", reason: "اختبار مسار استشاري غير منفذ", requested_by: 16, approved_by: 22, applied_by: 24, external_operation: false, requested_at: "2026-08-13T12:00:00Z", approved_at: "2026-08-13T12:20:00Z", applied_at: "2026-08-13T12:25:00Z" },
];

const INVESTOR_READINESS_ITEMS = [
  { label: "دفتر قيود مزدوج القيد وسجل تصحيحات عكسي", state: "موجود", icon: Landmark },
  { label: "فصل الواجبات وmaker-checker", state: "موجود", icon: Scale },
  { label: "مصفوفة الصلاحيات المالية المتخصصة", state: "موجود", icon: LockKeyhole },
  { label: "تعريف KPI ومصدر كل رقم", state: "قيد التفعيل", icon: Database },
  { label: "اختبار النسخ الاحتياطي والتعافي الموثق", state: "مطلوب قبل الإنتاج المالي", icon: History },
  { label: "مراجعة قانونية ومحاسبية للسوق المستهدف", state: "مطلوب", icon: FileCheck2 },
];

function money(value: string, currency: string) {
  return `${new Intl.NumberFormat("ar-IQ", { maximumFractionDigits: 2 }).format(Number(value))} ${currency}`;
}

function statusLabel(status: FinancialControlRequestRecord["status"]) {
  return { REQUESTED: "بانتظار الاعتماد", APPROVED: "معتمد", REJECTED: "مرفوض", APPLIED: "طُبق كضبط", EXPIRED: "منتهي" }[status];
}

function statusVariant(status: FinancialControlRequestRecord["status"]): "success" | "warning" | "destructive" | "outline" {
  if (status === "APPLIED") return "success";
  if (status === "REQUESTED") return "warning";
  if (status === "REJECTED" || status === "EXPIRED") return "destructive";
  return "outline";
}

export function FinancialGovernancePage() {
  const { demoMode, user } = useAuth();
  const institutionId = typeof user?.lab_id === "number" ? user.lab_id : null;
  const [summary, setSummary] = useState<FinancialControlSummaryRecord>(SYNTHETIC_SUMMARY);
  const [requests, setRequests] = useState<FinancialControlRequestRecord[]>(SYNTHETIC_REQUESTS);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadLive = async () => {
    if (demoMode) return;
    if (!institutionId) {
      setError("لا يتوفر سياق مؤسسة موثق لهذه الجلسة؛ تم منع تحميل مؤشرات مالية غير معزولة.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const [summaryResponse, requestsResponse] = await Promise.all([
        financialControlApi.summary(institutionId),
        financialControlApi.requests(institutionId),
      ]);
      setSummary(summaryResponse);
      setRequests(requestsResponse.items);
    } catch {
      setError("تعذر تحميل مؤشرات الحوكمة من backend؛ لم تُعرض أرقام بديلة في وضع live.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadLive();
  }, [demoMode, institutionId]);

  const openControls = useMemo(() => (summary.control_requests.REQUESTED ?? 0) + (summary.control_requests.APPROVED ?? 0), [summary]);

  return (
    <div className="mx-auto max-w-7xl space-y-6" dir="rtl">
      <PageHeader title="الحوكمة المالية والجاهزية الاستثمارية" description="ضوابط مالية قابلة للتدقيق والتوسع، مع مؤشرات تشغيلية لا تتضمن توقعات عائد أو تقييمًا استثماريًا." />

      <Card className="overflow-hidden border-indigo-200 bg-gradient-to-l from-indigo-50 via-white to-emerald-50 dark:border-indigo-900/50 dark:from-indigo-950/30 dark:via-background dark:to-emerald-950/20">
        <CardContent className="p-6">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div className="max-w-3xl space-y-3">
              <div className="flex items-center gap-2 text-indigo-700 dark:text-indigo-300"><ShieldCheck className="h-5 w-5" /><span className="text-sm font-semibold">Financial Control Plane</span></div>
              <h2 className="text-2xl font-bold tracking-tight">من نظام دفع إلى بنية مالية قابلة للثقة</h2>
              <p className="text-sm leading-7 text-muted-foreground">تجمع هذه المساحة بين دفتر القيود، فصل الواجبات، maker-checker، idempotency، المطابقة، وسجل التدقيق. لا يُسمح من هذه الشاشة بتشغيل مزود خارجي أو تحويل مالي.</p>
              <div className="flex flex-wrap gap-2"><Badge variant="success"><LockKeyhole className="ml-1 h-3.5 w-3.5" />أموال خارجية معطلة</Badge><Badge variant="outline"><Scale className="ml-1 h-3.5 w-3.5" />فصل الواجبات</Badge><Badge variant="outline"><History className="ml-1 h-3.5 w-3.5" />سجل append-only</Badge></div>
            </div>
            <div className="flex min-w-[260px] flex-col gap-3 rounded-2xl border border-indigo-200 bg-white/70 p-4 dark:border-indigo-900/50 dark:bg-white/[0.03]">
              <div className="flex items-center justify-between text-sm"><span>وضع التشغيل المالي</span><Badge variant="success">استشاري / Sandbox</Badge></div>
              <div className="flex items-center justify-between text-sm"><span>طلبات تحتاج مسار اعتماد</span><strong>{openControls}</strong></div>
              <div className="flex items-center justify-between text-sm"><span>استدعاءات مزود خارجي</span><strong>{summary.external_provider_calls}</strong></div>
              {!demoMode && <Button variant="outline" size="sm" onClick={() => void loadLive()} disabled={loading}><RefreshCw className={`ml-1 h-4 w-4 ${loading ? "animate-spin" : ""}`} />تحديث المؤشرات</Button>}
            </div>
          </div>
        </CardContent>
      </Card>

      {demoMode && <div className="rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm leading-7 text-amber-950"><strong>بيانات معاينة اصطناعية:</strong> الأرقام والطلبات أدناه ليست قيودًا مالية ولا تصلح لقرار استثماري أو محاسبي.</div>}
      {loading && <div className="rounded-xl border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-900" role="status"><RefreshCw className="ml-2 inline h-4 w-4 animate-spin" />جارٍ تحميل مؤشرات backend...</div>}
      {error && <div className="rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-950" role="alert"><AlertTriangle className="ml-2 inline h-4 w-4" />{error}</div>}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metric title="المبلغ المفوتر" value={money(summary.billed_amount, summary.currency)} icon={Landmark} />
        <Metric title="النقد المحصل" value={money(summary.collected_amount, summary.currency)} icon={WalletCards} />
        <Metric title="الذمم المفتوحة" value={money(summary.outstanding_amount, summary.currency)} icon={Clock3} />
        <Metric title="حالات المطابقة المفتوحة" value={String(summary.open_reconciliation_cases + summary.cash_variance_cases)} icon={AlertTriangle} />
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2 text-base"><ShieldCheck className="h-5 w-5 text-indigo-600" />طلبات الضبط المالي</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {requests.map((request) => <div key={request.id} className="rounded-xl border p-4"><div className="flex flex-wrap items-center justify-between gap-3"><div><p className="font-semibold">{request.requested_action}</p><p className="mt-1 text-xs text-muted-foreground">{request.control_type} · {request.resource_type}/{request.resource_id}</p></div><Badge variant={statusVariant(request.status)}>{statusLabel(request.status)}</Badge></div><p className="mt-3 text-sm text-muted-foreground">{request.reason}</p><div className="mt-3 flex flex-wrap gap-3 text-xs text-muted-foreground"><span>طلب: {request.requested_by}</span>{request.approved_by && <span>اعتماد: {request.approved_by}</span>}{request.applied_by && <span>تطبيق الضبط: {request.applied_by}</span>}<span>{request.external_operation ? "عملية خارجية" : "لا عملية خارجية"}</span></div></div>)}
            {!requests.length && <p className="text-sm text-muted-foreground">لا توجد طلبات ضبط لهذه المؤسسة.</p>}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2 text-base"><FileCheck2 className="h-5 w-5 text-emerald-600" />حزمة الجاهزية الاستثمارية</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {INVESTOR_READINESS_ITEMS.map(({ label, state, icon: Icon }) => <div key={label} className="flex items-start gap-3 rounded-xl border p-3"><span className="mt-0.5 rounded-lg bg-emerald-500/10 p-2 text-emerald-700"><Icon className="h-4 w-4" /></span><div className="min-w-0 flex-1"><p className="text-sm font-medium">{label}</p><p className="mt-1 text-xs text-muted-foreground">{state}</p></div>{state === "موجود" ? <CheckCircle2 className="mt-1 h-4 w-4 text-emerald-600" /> : <Clock3 className="mt-1 h-4 w-4 text-amber-600" />}</div>)}
          </CardContent>
        </Card>
      </div>

      <Card className="border-slate-200 bg-slate-50/80 dark:border-white/10 dark:bg-white/[0.03]"><CardContent className="p-5"><div className="flex items-start gap-3 text-sm leading-7 text-muted-foreground"><Database className="mt-1 h-5 w-5 shrink-0 text-indigo-600" /><p><strong className="text-foreground">حدود الاستخدام:</strong> مؤشرات هذه الصفحة وصفية ومصدرها facts مالية أو بيانات معاينة معلنة. لا تحسب valuation أو ROI أو توقعات نمو، ولا تستبدل مراجعة محاسب أو مستشار قانوني أو أمني. قبل تشغيل الأموال الحقيقية، يجب اعتماد السوق والمزود، واختبار التعافي، ومراجعة الامتثال، وتوثيق مسؤوليات الأطراف.</p></div></CardContent></Card>
    </div>
  );
}

function Metric({ title, value, icon: Icon }: { title: string; value: string; icon: typeof Landmark }) {
  return <Card><CardContent className="flex items-center gap-3 p-5"><span className="rounded-xl bg-indigo-500/10 p-3 text-indigo-700 dark:text-indigo-300"><Icon className="h-5 w-5" /></span><div><p className="text-xs text-muted-foreground">{title}</p><p className="mt-1 text-lg font-bold">{value}</p></div></CardContent></Card>;
}
