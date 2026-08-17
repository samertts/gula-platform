import { useMemo, useRef, useState, type ChangeEvent, type ReactNode } from "react";
import { AlertTriangle, CheckCircle2, FileJson2, Filter, Info, LockKeyhole, RefreshCcw, Search, ShieldCheck, Upload } from "lucide-react";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Input } from "@/components/ui";

type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
type Finding = {
  severity: Severity;
  rule: string;
  path: string;
  line: number;
  message: string;
};

const numberFormatter = new Intl.NumberFormat("ar-IQ");
const severities: Severity[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];
const snapshotSummary = { total: 153, blocking: 152, critical: 74, high: 78, medium: 1 };
const initialFindings: Finding[] = [
  { severity: "CRITICAL", rule: "SECRET_EXPOSED", path: ".github/actions/build-android/action.yml", line: 90, message: "possible generic-secret-assignment; value redacted" },
  { severity: "CRITICAL", rule: "SECRET_EXPOSED", path: "config/postgres-ha/patroni.yml", line: 55, message: "possible generic-secret-assignment; value redacted" },
  { severity: "CRITICAL", rule: "SECRET_EXPOSED", path: "terraform/modules/postgres/main.tf", line: 28, message: "possible generic-secret-assignment; value redacted" },
  { severity: "CRITICAL", rule: "SECRET_EXPOSED", path: "config/cert-manager/cluster-issuer.yaml", line: 102, message: "possible generic-secret-assignment; value redacted" },
  { severity: "HIGH", rule: "UNPINNED_ACTION", path: ".github/workflows/nightly.yml", line: 26, message: "GitHub Action must be pinned to a full commit SHA" },
  { severity: "HIGH", rule: "UNPINNED_IMAGE", path: "k8s/base/backend/deployment.yaml", line: 54, message: "container image uses latest; pin an immutable digest or version" },
  { severity: "HIGH", rule: "PLAINTEXT_ENDPOINT", path: "k8s/base/configmap.yaml", line: 8, message: "non-local HTTP endpoint; use HTTPS or an approved isolated test endpoint" },
  { severity: "HIGH", rule: "SERVICE_ACCOUNT_TOKEN", path: "helm/gula-platform/values.yaml", line: 33, message: "disable automatic service-account token mounting unless required" },
  { severity: "HIGH", rule: "MUTATING_COMMAND", path: "k8s/base/mesh/linkerd.yaml", line: 2, message: "configuration contains a mutating command; review and gate it" },
  { severity: "HIGH", rule: "PARSE_ERROR", path: "backend/app/capabilities/clinical_foundation/capability.json", line: 12, message: "configuration does not parse" },
  { severity: "MEDIUM", rule: "WILDCARD_BIND", path: "helm/gula-platform/templates/redis/configmap.yaml", line: 17, message: "wildcard bind address requires explicit environment justification" },
];

const severityTone: Record<Severity, { label: string; className: string; dot: string }> = {
  CRITICAL: { label: "حرج", className: "border-rose-200 bg-rose-50 text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-200", dot: "bg-rose-500" },
  HIGH: { label: "مرتفع", className: "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-200", dot: "bg-amber-500" },
  MEDIUM: { label: "متوسط", className: "border-sky-200 bg-sky-50 text-sky-800 dark:border-sky-900/50 dark:bg-sky-950/30 dark:text-sky-200", dot: "bg-sky-500" },
  LOW: { label: "منخفض", className: "border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300", dot: "bg-slate-400" },
};

function isFinding(value: unknown): value is Finding {
  if (!value || typeof value !== "object") return false;
  const item = value as Partial<Finding>;
  return severities.includes(item.severity as Severity) && typeof item.rule === "string" && typeof item.path === "string" && typeof item.line === "number" && typeof item.message === "string";
}

export function SecurityScannerPage() {
  const [findings, setFindings] = useState<Finding[]>(initialFindings);
  const [severity, setSeverity] = useState<Severity | "ALL">("ALL");
  const [rule, setRule] = useState("ALL");
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Finding | null>(initialFindings[0] ?? null);
  const [notice, setNotice] = useState("لقطة منقحة من آخر فحص؛ القيم الحساسة غير معروضة.");
  const inputRef = useRef<HTMLInputElement>(null);
  const isSnapshot = notice.startsWith("لقطة");

  const counts = useMemo(() => findings.reduce<Record<Severity, number>>((acc, item) => ({ ...acc, [item.severity]: acc[item.severity] + 1 }), { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 }), [findings]);
  const rules = useMemo(() => Array.from(new Set(findings.map((item) => item.rule))), [findings]);
  const visibleFindings = useMemo(() => findings.filter((item) => {
    const haystack = `${item.rule} ${item.path} ${item.message}`.toLowerCase();
    return (severity === "ALL" || item.severity === severity) && (rule === "ALL" || item.rule === rule) && haystack.includes(query.toLowerCase());
  }), [findings, query, rule, severity]);

  const handleFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const raw = JSON.parse(await file.text()) as unknown;
      const candidate = Array.isArray(raw) ? raw : (raw as { findings?: unknown })?.findings;
      const parsed = Array.isArray(candidate) ? candidate.filter(isFinding) : [];
      if (!parsed.length) throw new Error("invalid findings");
      setFindings(parsed);
      setSelected(parsed[0] ?? null);
      setNotice(`تمت قراءة ${numberFormatter.format(parsed.length)} نتيجة محلياً من ${file.name}. لم تُرسل البيانات إلى أي خادم.`);
      setSeverity("ALL");
      setRule("ALL");
      setQuery("");
    } catch {
      setNotice("تعذر قراءة الملف. استخدم JSON منقحاً يحتوي findings أو مصفوفة findings مباشرة.");
    }
    event.target.value = "";
  };

  const reset = () => {
    setFindings(initialFindings);
    setSelected(initialFindings[0] ?? null);
    setNotice("لقطة منقحة من آخر فحص؛ القيم الحساسة غير معروضة.");
    setSeverity("ALL");
    setRule("ALL");
    setQuery("");
  };

  const total = isSnapshot ? snapshotSummary.total : findings.length;
  const blocking = isSnapshot ? snapshotSummary.blocking : counts.CRITICAL + counts.HIGH;
  const displayedCount = (level: Severity) => isSnapshot ? snapshotSummary[level.toLowerCase() as "critical" | "high" | "medium"] ?? 0 : counts[level];

  return (
    <div dir="rtl" className="mx-auto max-w-7xl space-y-6">
      <header className="overflow-hidden rounded-[1.5rem] border border-slate-200 bg-gradient-to-l from-slate-950 via-slate-900 to-slate-800 p-6 text-white shadow-[0_18px_55px_-36px_rgba(15,23,42,0.65)] dark:border-white/10 sm:p-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="mb-4 flex items-center gap-2 text-xs font-bold text-amber-200"><ShieldCheck className="h-4 w-4" /> GULA · Security Operations</div>
            <div className="flex items-start gap-3"><span className="mt-1 h-12 w-1 rounded-full bg-[#D78B49]" /><div><p className="text-xs font-semibold text-amber-200">محطة فرز الأدلة</p><h1 className="mt-2 text-2xl font-bold tracking-tight sm:text-3xl">اعرض الدليل، لا تَعِد بالأمان.</h1><p className="mt-3 max-w-2xl text-sm leading-7 text-slate-300">لوحة قراءة للنتائج المنقحة من Security Linting &amp; Scanning قبل قرار Go/No-Go. لا تنفذ التكوين ولا تعرض قيمة الأسرار.</p></div></div>
            <p className="mt-5 text-xs text-slate-400">{notice}</p>
          </div>
          <div className="flex shrink-0 flex-col gap-3 lg:items-end"><Badge className="w-fit border-amber-300/30 bg-amber-300/10 text-amber-100">قراءة محلية فقط</Badge><input ref={inputRef} type="file" accept="application/json,.json" onChange={handleFile} className="hidden" /><Button onClick={() => inputRef.current?.click()} className="gap-2 bg-[#D78B49] text-slate-950 hover:bg-[#e6a15e]"><Upload className="h-4 w-4" /> تحميل JSON منقح</Button></div>
        </div>
      </header>

      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-label="ملخص فحص الأمان">
        <SummaryCard label="إجمالي النتائج" value={total} icon={<FileJson2 className="h-4 w-4" />} />
        <SummaryCard label="حاجز للنشر" value={blocking} icon={<AlertTriangle className="h-4 w-4" />} tone="rose" />
        <SummaryCard label="نتائج حرجة" value={isSnapshot ? snapshotSummary.critical : counts.CRITICAL} icon={<TriangleIcon />} tone="amber" />
        <SummaryCard label="حالة الإدخال" value="محلي" icon={<LockKeyhole className="h-4 w-4" />} tone="emerald" />
      </section>

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]" id="security-findings">
        <Card className="overflow-hidden border-slate-200 dark:border-white/10">
          <CardHeader className="border-b border-slate-100 p-5 dark:border-white/10 sm:p-6"><div className="flex flex-wrap items-start justify-between gap-3"><div><CardTitle className="text-lg">نتائج تحتاج قراراً</CardTitle><p className="mt-1 text-xs text-muted-foreground">{numberFormatter.format(visibleFindings.length)} نتيجة ظاهرة من العينة الحالية</p></div><Button variant="ghost" size="sm" onClick={reset} className="gap-2"><RefreshCcw className="h-3.5 w-3.5" /> استعادة اللقطة</Button></div><div className="mt-5 flex flex-col gap-3 md:flex-row"><div className="relative flex-1"><Search className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" /><Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="ابحث في القاعدة أو المسار…" className="pr-10" /></div><label className="relative"><Filter className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" /><select value={rule} onChange={(event) => setRule(event.target.value)} className="h-10 min-w-48 appearance-none rounded-md border border-input bg-background px-9 text-sm"><option value="ALL">كل القواعد</option>{rules.map((item) => <option key={item} value={item}>{item}</option>)}</select></label></div><div className="mt-4 flex flex-wrap gap-2"><button onClick={() => setSeverity("ALL")} className={`rounded-full border px-3 py-1.5 text-xs ${severity === "ALL" ? "border-slate-300 bg-slate-100 text-slate-900 dark:border-white/20 dark:bg-white/10 dark:text-white" : "border-input text-muted-foreground"}`}>الكل {numberFormatter.format(total)}</button>{severities.map((item) => <button key={item} onClick={() => setSeverity(item)} className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs ${severity === item ? severityTone[item].className : "border-input text-muted-foreground"}`}><span className={`h-1.5 w-1.5 rounded-full ${severityTone[item].dot}`} />{severityTone[item].label} {numberFormatter.format(displayedCount(item))}</button>)}</div></CardHeader>
          <CardContent className="p-0"><div className="divide-y divide-slate-100 dark:divide-white/6">{visibleFindings.length ? visibleFindings.map((item, index) => <button key={`${item.path}-${item.line}-${index}`} onClick={() => setSelected(item)} className={`flex w-full items-center gap-3 p-4 text-right transition hover:bg-slate-50 dark:hover:bg-white/[0.035] ${selected === item ? "bg-slate-50 dark:bg-white/[0.045]" : ""}`}><span className={`h-2.5 w-2.5 shrink-0 rounded-full ${severityTone[item.severity].dot}`} /><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-3"><span className="font-mono-ui text-xs font-semibold">{item.rule}</span><span className="font-mono-ui text-[10px] text-muted-foreground">L{item.line}</span></div><div dir="ltr" className="mt-1 truncate text-right font-mono-ui text-[11px] text-muted-foreground">{item.path}</div></div></button>) : <div className="p-10 text-center"><CheckCircle2 className="mx-auto h-7 w-7 text-emerald-500" /><p className="mt-3 text-sm font-semibold">لا توجد نتائج مطابقة</p><p className="mt-1 text-xs text-muted-foreground">غيّر الفلاتر أو عبارة البحث.</p></div>}</div></CardContent>
        </Card>

        <Card className="h-fit border-amber-200 dark:border-amber-900/40"><CardHeader className="border-b border-amber-100 p-5 dark:border-amber-900/30"><CardTitle className="flex items-center gap-2 text-base"><Info className="h-4 w-4 text-amber-600" /> دليل النتيجة</CardTitle></CardHeader><CardContent className="p-5">{selected ? <div><Badge className={severityTone[selected.severity].className}>{severityTone[selected.severity].label}</Badge><h2 className="mt-5 font-mono-ui text-base font-bold">{selected.rule}</h2><p className="mt-3 text-sm leading-7 text-muted-foreground">{selected.message}</p><div className="mt-5 space-y-3 border-y border-slate-100 py-4 text-xs dark:border-white/10"><div className="text-muted-foreground">المسار المنقح</div><div dir="ltr" className="break-all text-left font-mono-ui leading-6">{selected.path}</div><div className="flex items-center justify-between"><span className="text-muted-foreground">رقم السطر</span><span className="font-mono-ui">{selected.line}</span></div></div><div className="mt-5 rounded-xl bg-amber-50 p-3 text-xs leading-6 text-amber-900 dark:bg-amber-950/25 dark:text-amber-100"><AlertTriangle className="ml-1 inline h-3.5 w-3.5" /> القيمة السرية منقحة. المراجعة البشرية مطلوبة قبل أي تغيير.</div></div> : <p className="text-sm text-muted-foreground">اختر نتيجة من القائمة لعرض الدليل.</p>}</CardContent></Card>
      </section>

      <section className="grid gap-3 md:grid-cols-3" aria-label="ضوابط العرض الآمن"><SafePoint icon={<LockKeyhole className="h-4 w-4" />} title="قراءة محلية" text="ملف JSON يُحلل داخل المتصفح ولا يُرسل إلى خادم." /><SafePoint icon={<ShieldCheck className="h-4 w-4" />} title="نتائج منقحة" text="لا تظهر قيم الأسرار أو tokens أو بيانات مواطنين." /><SafePoint icon={<CheckCircle2 className="h-4 w-4" />} title="قرار بشري" text="الواجهة تعرض الدليل ولا تمنح اعتماد Go/No-Go تلقائياً." /></section>
    </div>
  );
}

function SummaryCard({ label, value, icon, tone = "slate" }: { label: string; value: number | string; icon: ReactNode; tone?: "slate" | "rose" | "amber" | "emerald" }) {
  const colors = { slate: "border-slate-200 dark:border-white/10", rose: "border-rose-200 dark:border-rose-900/40", amber: "border-amber-200 dark:border-amber-900/40", emerald: "border-emerald-200 dark:border-emerald-900/40" };
  const text = { slate: "", rose: "text-rose-700 dark:text-rose-300", amber: "text-amber-700 dark:text-amber-300", emerald: "text-emerald-700 dark:text-emerald-300" };
  return <Card className={colors[tone]}><CardContent className="p-4"><div className="flex items-center justify-between text-muted-foreground">{icon}<span className="text-[11px]">قراءة محلية</span></div><div className={`mt-4 text-2xl font-bold ${text[tone]}`}>{typeof value === "number" ? numberFormatter.format(value) : value}</div><p className="mt-1 text-xs text-muted-foreground">{label}</p></CardContent></Card>;
}

function SafePoint({ icon, title, text }: { icon: ReactNode; title: string; text: string }) {
  return <Card className="border-slate-200/80 dark:border-white/10"><CardContent className="p-4"><div className="text-[#0D9488]">{icon}</div><h3 className="mt-3 text-sm font-semibold">{title}</h3><p className="mt-1 text-xs leading-6 text-muted-foreground">{text}</p></CardContent></Card>;
}

function TriangleIcon() {
  return <AlertTriangle className="h-4 w-4" />;
}
