import { ArrowLeft, CheckCircle2, CircleDashed, LockKeyhole, Route } from "lucide-react";
import { Link } from "react-router-dom";
import { ClinicalStatePanel, ClinicalStatusBadge, type ClinicalSurfaceState } from "@/components/clinical";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

type GoldenPathStep = {
  id: string;
  label: string;
  status: ClinicalSurfaceState;
  detail: string;
};

const steps: GoldenPathStep[] = [
  { id: "identity", label: "Identity", status: "loaded", detail: "جلسة وملف هوية معادان من الخادم" },
  { id: "workspace", label: "Workspace", status: "loaded", detail: "اختيار المساحة يمر عبر switchWorkspace" },
  { id: "access", label: "Patient Access", status: "partial", detail: "قراءات محدودة فقط عند تحقق السياق والعلاقة" },
  { id: "appointment", label: "Appointment", status: "maintenance", detail: "يحتاج عقد دورة الموعد ومنع التكرار" },
  { id: "encounter", label: "Encounter", status: "maintenance", detail: "يحتاج state machine وتوقيعاً وتعديلات مدققة" },
  { id: "lab-order", label: "Lab Order", status: "maintenance", detail: "يحتاج Patient + Encounter + Facility + Idempotency" },
  { id: "specimen", label: "Specimen", status: "maintenance", detail: "لا جمع أو رفض أو حذف قبل عقد العينة" },
  { id: "result", label: "Result", status: "maintenance", detail: "لا تحقق أو إطلاق قبل عقد النتيجة" },
  { id: "review", label: "Doctor Review", status: "maintenance", detail: "لا acknowledgment أو clinical action من الواجهة" },
  { id: "citizen-result", label: "Citizen Access", status: "partial", detail: "يعتمد على حالة الإطلاق والنطاق المسموح" },
  { id: "sharing", label: "Sharing / Revoke", status: "partial", detail: "السحب المتاح يمر عبر عقد الخادم؛ الإنشاء محكوم" },
  { id: "audit", label: "Audit", status: "maintenance", detail: "التدقيق الحي لا يفتح من هذا المسار" },
];

export default function GoldenPathReadinessPage() {
  const available = steps.filter((step) => step.status === "loaded").length;
  return (
    <div className="mx-auto max-w-5xl space-y-5" dir="rtl">
      <Card className="gula-interactive-surface overflow-hidden">
        <CardHeader className="bg-gradient-to-l from-slate-950 via-[#0f766e] to-[#0d9488] text-white">
          <div className="flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/10"><Route className="h-5 w-5" /></span>
            <div><p className="gula-section-label text-teal-200">PROGRAM-GOLDEN-PATH-001</p><CardTitle className="mt-1 text-2xl">جاهزية الرحلة السريرية الذهبية</CardTitle></div>
          </div>
          <p className="max-w-3xl text-sm leading-7 text-slate-200">خريطة تنفيذية واحدة من المواطن إلى الطبيب والمختبر ثم عودة النتيجة والمشاركة والتدقيق. هذه الشاشة تميز بين الأساس المتاح والعقد المحجوب ولا تسمي المسار ناجحاً قبل اكتماله فعلياً.</p>
        </CardHeader>
        <CardContent className="space-y-5 p-6">
          <ClinicalStatePanel state="partial" title={`الأساس متاح جزئياً · ${available}/${steps.length} مراحل جاهزة`} description="وجود الواجهة أو القراءة المحدودة لا يساوي GOLDEN PATH PASSED. الكتابات السريرية والانتقالات الحساسة تحتاج عقود backend واختبارات E2E قبل الفتح." />
          <div className="grid gap-3 sm:grid-cols-3"><Metric label="Foundation" value={`${available}/${steps.length}`} /><Metric label="Live clinical writes" value="0" /><Metric label="Demo data" value="Synthetic" /></div>
          <ol className="grid gap-3 md:grid-cols-2" aria-label="مراحل الرحلة الذهبية">{steps.map((step, index) => <li key={step.id} className="relative rounded-2xl border bg-card p-4 shadow-sm"><div className="flex items-start gap-3"><span className={`mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${step.status === "loaded" ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-200" : "bg-muted text-muted-foreground"}`}>{step.status === "loaded" ? <CheckCircle2 className="h-4 w-4" /> : step.status === "maintenance" ? <LockKeyhole className="h-4 w-4" /> : <CircleDashed className="h-4 w-4" />}</span><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><span className="text-xs text-muted-foreground">{String(index + 1).padStart(2, "0")}</span><h3 className="font-bold">{step.label}</h3><ClinicalStatusBadge status={step.status} /></div><p className="mt-2 text-sm leading-6 text-muted-foreground">{step.detail}</p></div></div></li>)}</ol>
          <div className="flex flex-wrap gap-3"><Link className="gula-focus-ring inline-flex min-h-11 items-center rounded-xl bg-primary px-4 text-sm font-semibold text-primary-foreground transition hover:opacity-90" to="/screen-by-screen">مشاهدة الشاشات الاصطناعية <ArrowLeft className="ms-2 h-4 w-4" /></Link><Link className="gula-focus-ring inline-flex min-h-11 items-center rounded-xl border border-border bg-background px-4 text-sm font-semibold transition hover:bg-muted" to="/dashboard">العودة إلى مساحة العمل</Link></div>
        </CardContent>
      </Card>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) { return <div className="rounded-xl border bg-muted/20 p-4"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 text-xl font-bold">{value}</p></div>; }
