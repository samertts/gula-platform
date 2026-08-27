import { AlertTriangle, ArrowLeft, Filter, ListChecks } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ClinicalStatePanel, ClinicalStatusBadge } from "@/components/clinical";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { PREVIOUS_WORKSTREAMS, summarizeRemainingWork, type WorkstreamStatus } from "@/contracts/clinicalJourneyContractRegistry";

type FilterKey = "all" | "partial" | "blocked" | "implemented";

const statusLabels: Record<WorkstreamStatus, string> = {
  "implemented-safely": "أساس آمن",
  partial: "جزئي",
  "backend-blocked": "محجوب بعقد backend",
  "external-input-blocked": "ينتظر تكاملاً أو مدخلاً",
  "remote-blocked": "ينتظر فحوصاً بعيدة",
};

function badgeStatus(status: WorkstreamStatus) {
  if (status === "implemented-safely") return "loaded";
  if (status === "partial") return "partial";
  if (status === "remote-blocked") return "error";
  if (status === "external-input-blocked") return "forbidden";
  return "maintenance";
}

function matchesFilter(status: WorkstreamStatus, filter: FilterKey) {
  if (filter === "all") return true;
  if (filter === "partial") return status === "partial";
  if (filter === "implemented") return status === "implemented-safely";
  return status !== "partial" && status !== "implemented-safely";
}

export default function RemainingWorkstreamsPage() {
  const [filter, setFilter] = useState<FilterKey>("all");
  const summary = summarizeRemainingWork();
  const visibleWorkstreams = useMemo(() => PREVIOUS_WORKSTREAMS.filter((workstream) => matchesFilter(workstream.status, filter)), [filter]);

  return (
    <div className="mx-auto max-w-6xl space-y-5" dir="rtl">
      <Card className="gula-interactive-surface overflow-hidden">
        <CardHeader className="bg-gradient-to-l from-slate-950 via-slate-800 to-[#0f766e] text-white">
          <div className="flex items-center gap-3"><span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/10"><ListChecks className="h-5 w-5" /></span><div><p className="gula-section-label text-teal-200">PROGRAM GAP REGISTER</p><CardTitle className="mt-1 text-2xl">سجل المتبقي من المهام السابقة</CardTitle></div></div>
          <p className="max-w-4xl text-sm leading-7 text-slate-200">عرض موحد للمنجز والمتبقي وسبب عدم فتح كل قدرة. لا تعتبر الصفحة وجود واجهة أو wrapper دليلاً على عقد backend أو صلاحية أو جاهزية إنتاجية.</p>
        </CardHeader>
        <CardContent className="space-y-5 p-6">
          <ClinicalStatePanel state="partial" title={`${summary.complete}/${summary.total} مسارات مؤهلة للإعلان كمكتملة`} description="الأساس الآمن موجود، لكن الإكمال يتطلب عقداً خادمياً وتفويضاً كائناً وحالات رسمية وتدقيقاً وتزامناً واختبارات بعيدة بحسب طبيعة المسار." />
          <div className="grid gap-3 sm:grid-cols-4"><Metric label="الإجمالي" value={String(summary.total)} /><Metric label="مكتمل وفق الدليل" value={String(summary.complete)} /><Metric label="جزئي" value={String(summary.partial)} /><Metric label="محجوب" value={String(summary.blocked)} /></div>
          <div className="flex flex-wrap items-center gap-2" aria-label="تصفية سجل الفجوات"><span className="me-1 inline-flex items-center gap-2 text-sm font-semibold"><Filter className="h-4 w-4" />التصفية</span>{(["all", "partial", "blocked", "implemented"] as const).map((key) => <button key={key} type="button" aria-pressed={filter === key} onClick={() => setFilter(key)} className={`gula-focus-ring min-h-10 rounded-xl border px-3 text-sm font-semibold transition ${filter === key ? "border-primary bg-primary text-primary-foreground" : "border-border bg-background hover:bg-muted"}`}>{key === "all" ? "الكل" : key === "partial" ? "الجزئي" : key === "blocked" ? "المحجوب" : "الأساس الآمن"}</button>)}</div>
          <div className="grid gap-4 lg:grid-cols-2" aria-label="قائمة المهام السابقة">{visibleWorkstreams.map((workstream, index) => <article key={workstream.id} className="rounded-2xl border bg-card p-5 shadow-sm"><div className="flex items-start gap-3"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-muted text-muted-foreground"><span className="text-xs font-bold">{String(index + 1).padStart(2, "0")}</span></span><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><h2 className="text-lg font-bold">{workstream.title}</h2><ClinicalStatusBadge status={badgeStatus(workstream.status)} label={statusLabels[workstream.status]} /></div><p className="mt-3 text-sm leading-6 text-muted-foreground"><strong className="text-foreground">الحالة الحالية:</strong> {workstream.currentState}</p><div className="mt-3 rounded-xl border border-amber-200 bg-amber-50/70 p-3 text-sm leading-6 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-100"><p className="flex items-start gap-2 font-semibold"><AlertTriangle className="mt-1 h-4 w-4 shrink-0" />سبب الحجب</p><p className="mt-1">{workstream.blocker}</p></div><p className="mt-3 text-sm leading-6"><strong>الخطوة الآمنة التالية:</strong> {workstream.safeNextAction}</p><div className="mt-4 flex flex-wrap gap-2">{workstream.requirements.map((requirement) => <span key={requirement.id} className="rounded-lg border bg-muted/40 px-2.5 py-1 text-xs text-muted-foreground">{requirement.label} · {requirement.status === "met" ? "متحقق" : requirement.kind === "external" ? "تكامل مطلوب" : requirement.kind === "remote" ? "فحص بعيد مطلوب" : "مفقود/محجوب"}</span>)}</div></div></div></article>)}</div>
          {visibleWorkstreams.length === 0 && <ClinicalStatePanel state="empty" title="لا توجد نتائج" description="غيّر التصفية لرؤية عناصر أخرى." />}
          <div className="flex flex-wrap gap-3"><Link className="gula-focus-ring inline-flex min-h-11 items-center rounded-xl bg-primary px-4 text-sm font-semibold text-primary-foreground transition hover:opacity-90" to="/golden-path">عرض الرحلة الذهبية <ArrowLeft className="ms-2 h-4 w-4" /></Link><Link className="gula-focus-ring inline-flex min-h-11 items-center rounded-xl border border-border bg-background px-4 text-sm font-semibold transition hover:bg-muted" to="/screen-by-screen">عرض الشاشات الاصطناعية</Link></div>
        </CardContent>
      </Card>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) { return <div className="rounded-xl border bg-muted/20 p-4"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 text-xl font-bold">{value}</p></div>; }
