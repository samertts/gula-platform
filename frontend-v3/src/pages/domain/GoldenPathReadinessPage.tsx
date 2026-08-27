import { ArrowLeft, CheckCircle2, CircleDashed, LockKeyhole, Route } from "lucide-react";
import { Link } from "react-router-dom";
import { ClinicalStatePanel, ClinicalStatusBadge } from "@/components/clinical";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { GOLDEN_PATH_STAGES } from "@/contracts/clinicalJourneyContractRegistry";

export default function GoldenPathReadinessPage() {
  const available = GOLDEN_PATH_STAGES.filter((step) => step.state === "loaded").length;
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
          <ClinicalStatePanel state="partial" title={`الأساس متاح جزئياً · ${available}/${GOLDEN_PATH_STAGES.length} مراحل جاهزة`} description="وجود الواجهة أو القراءة المحدودة لا يساوي GOLDEN PATH PASSED. الكتابات السريرية والانتقالات الحساسة تحتاج عقود backend واختبارات E2E قبل الفتح." />
          <div className="grid gap-3 sm:grid-cols-3"><Metric label="Foundation" value={`${available}/${GOLDEN_PATH_STAGES.length}`} /><Metric label="Live clinical writes" value="0" /><Metric label="Demo data" value="Synthetic" /></div>
          <ol className="grid gap-3 md:grid-cols-2" aria-label="مراحل الرحلة الذهبية">{GOLDEN_PATH_STAGES.map((step, index) => <li key={step.id} className="relative rounded-2xl border bg-card p-4 shadow-sm"><div className="flex items-start gap-3"><span className={`mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${step.state === "loaded" ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-200" : "bg-muted text-muted-foreground"}`}>{step.state === "loaded" ? <CheckCircle2 className="h-4 w-4" /> : step.state === "maintenance" ? <LockKeyhole className="h-4 w-4" /> : <CircleDashed className="h-4 w-4" />}</span><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><span className="text-xs text-muted-foreground">{String(index + 1).padStart(2, "0")}</span><h3 className="font-bold">{step.label}</h3><ClinicalStatusBadge status={step.state} /></div><p className="mt-2 text-sm leading-6 text-muted-foreground">{step.detail}</p></div></div></li>)}</ol>
          <div className="flex flex-wrap gap-3"><Link className="gula-focus-ring inline-flex min-h-11 items-center rounded-xl bg-primary px-4 text-sm font-semibold text-primary-foreground transition hover:opacity-90" to="/screen-by-screen">مشاهدة الشاشات الاصطناعية <ArrowLeft className="ms-2 h-4 w-4" /></Link><Link className="gula-focus-ring inline-flex min-h-11 items-center rounded-xl border border-border bg-background px-4 text-sm font-semibold transition hover:bg-muted" to="/dashboard">العودة إلى مساحة العمل</Link></div>
        </CardContent>
      </Card>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) { return <div className="rounded-xl border bg-muted/20 p-4"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 text-xl font-bold">{value}</p></div>; }
