import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { dashboardApi } from "@/api/endpoints";
import { useAuth } from "@/contexts/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { Activity, AlertTriangle, ArrowLeft, ClipboardList, FlaskConical, HeartPulse, ShieldCheck, Users } from "lucide-react";

const statCards = [
  { label: "إجمالي المرضى", key: "total_patients", icon: Users, color: "from-blue-500 to-cyan-500", surface: "bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-200" },
  { label: "الطلبات اليوم", key: "today_orders", icon: ClipboardList, color: "from-emerald-500 to-teal-500", surface: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-200" },
  { label: "النتائج اليوم", key: "today_results", icon: FlaskConical, color: "from-violet-500 to-fuchsia-500", surface: "bg-violet-50 text-violet-700 dark:bg-violet-950/40 dark:text-violet-200" },
  { label: "التنبيهات الحرجة", key: "critical_alerts", icon: AlertTriangle, color: "from-rose-500 to-orange-500", surface: "bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-200" },
] as const;

const DEMO_ROLE_SUMMARIES: Record<string, { label: string; summary: string }> = {
  doctor: { label: "طبيب تجريبي", summary: "قراءة المرضى والطلبات والنتائج الاصطناعية ضمن نطاق العرض." },
  technician: { label: "فني مختبر تجريبي", summary: "استعراض مسار العينات والنتائج المختبرية الاصطناعية." },
  lab_admin: { label: "مدير مختبر تجريبي", summary: "استعراض مؤشرات المختبر والموظفين والتقارير دون عمليات كتابة." },
  citizen: { label: "مواطن تجريبي", summary: "استعراض مساحة المواطن ببيانات اصطناعية ومعزولة بالكامل." },
};

const quickLinks = [
  { label: "المرضى", description: "الوصول إلى السجلات المصرح بها", path: "/patients", icon: Users },
  { label: "الطلبات", description: "متابعة مسار الطلبات والعينات", path: "/orders", icon: ClipboardList },
  { label: "النتائج", description: "مراجعة النتائج والتحقق منها", path: "/results", icon: FlaskConical },
  { label: "التنبيهات", description: "مراقبة الحالات ذات الأولوية", path: "/alerts", icon: AlertTriangle },
];

export function DashboardPage() {
  const { demoMode, user } = useAuth();
  const demoRole = DEMO_ROLE_SUMMARIES[user?.role ?? ""] ?? DEMO_ROLE_SUMMARIES.doctor!;
  const { data, isLoading, isError } = useQuery<Record<string, unknown>>({
          queryKey: ["dashboard", demoMode ? "demo" : "institution", user?.role],

    queryFn: async () => {
      if (demoMode) return dashboardApi.demo(user?.role as "doctor" | "technician" | "lab_admin" | "citizen") as unknown as Record<string, unknown>;
      return {};
    },
    enabled: demoMode,
  });

  return (
    <div className="mx-auto max-w-7xl space-y-7">
      <section className="relative overflow-hidden rounded-[1.75rem] bg-slate-950 p-6 text-white shadow-[0_24px_70px_-35px_rgba(15,23,42,0.75)] md:p-8">
        <div className="absolute -left-10 -top-24 h-64 w-64 rounded-full bg-cyan-400/20 blur-3xl" />
        <div className="absolute -bottom-28 right-10 h-72 w-72 rounded-full bg-indigo-500/25 blur-3xl" />
        <div className="relative flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
          <div className="max-w-2xl">
            <div className="mb-4 flex flex-wrap items-center gap-2 text-xs font-semibold">
              {demoMode ? (
                <span className="inline-flex items-center gap-2 rounded-full border border-amber-300/20 bg-amber-300/10 px-3 py-1.5 text-amber-100"><ShieldCheck className="h-3.5 w-3.5" /> عرض تجريبي معزول</span>
              ) : (
                <span className="inline-flex items-center gap-2 rounded-full border border-slate-300/20 bg-white/10 px-3 py-1.5 text-slate-200"><span className="h-2 w-2 rounded-full bg-amber-300" /> انتظار عقد قراءة مؤسسي موثق</span>
              )}
            </div>
            <p className="text-sm text-cyan-200">صباح الخير{user?.name ? `، ${user.name}` : ""}</p>
            {demoMode && <div className="mt-3 inline-flex max-w-xl flex-wrap items-center gap-2 rounded-xl border border-amber-200/20 bg-amber-200/10 px-3 py-2 text-xs text-amber-100"><ShieldCheck className="h-3.5 w-3.5" /><strong>{demoRole.label}</strong><span className="text-amber-100/70">— {demoRole.summary}</span></div>}
            <h1 className="mt-2 text-3xl font-bold tracking-tight md:text-4xl">مركز العمليات الصحية</h1>
            <p className="mt-3 max-w-xl text-sm leading-7 text-slate-300">نظرة موحّدة على سير العمل، مؤشرات الأداء، والتنبيهات ذات الأولوية ضمن مساحة العمل الحالية.</p>
          </div>
          <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.07] p-4 text-sm text-slate-200"><HeartPulse className="h-7 w-7 text-cyan-300" /><div><p className="font-bold">مساحة عمل آمنة</p><p className="mt-1 text-xs text-slate-400">RBAC · Tenant isolation · Audit</p></div></div>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {statCards.map(({ label, key, icon: Icon, color, surface }) => {
          const value = data?.[key];
          return <Card key={key} className="group overflow-hidden rounded-2xl border-slate-200/80 shadow-sm transition duration-200 hover:-translate-y-0.5 hover:shadow-lg dark:border-white/10"><CardContent className="relative p-5"><div className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-l ${color}`} /><div className="flex items-start justify-between gap-3"><span className={`flex h-11 w-11 items-center justify-center rounded-2xl ${surface}`}><Icon className="h-5 w-5" /></span><span className="text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground">{demoMode ? "تجريبي" : "غير مهيأ"}</span></div><p className="mt-5 text-sm text-muted-foreground">{label}</p><p className="mt-1 text-3xl font-bold tracking-tight">{demoMode ? (isLoading ? "…" : isError ? "—" : String(value ?? 0)) : "—"}</p></CardContent></Card>;
        })}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <Card className="rounded-2xl border-slate-200/80 shadow-sm dark:border-white/10"><CardHeader className="flex flex-row items-center justify-between space-y-0"><div><CardTitle className="flex items-center gap-2 text-base"><Activity className="h-5 w-5 text-primary" /> مسارات العمل السريعة</CardTitle><p className="mt-1 text-xs text-muted-foreground">انتقل مباشرة إلى الجزء الذي تريد متابعته.</p></div><span className="rounded-full bg-primary/10 px-2.5 py-1 text-[10px] font-bold text-primary">وصول سريع</span></CardHeader><CardContent className="grid gap-3 sm:grid-cols-2">{quickLinks.map(({ label, description, path, icon: Icon }) => <Link key={path} to={path} className="group flex items-center gap-3 rounded-2xl border border-slate-200/80 p-3.5 transition hover:-translate-y-0.5 hover:border-primary/30 hover:bg-primary/[0.03] dark:border-white/10"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-primary transition group-hover:bg-primary group-hover:text-white dark:bg-white/10"><Icon className="h-[18px] w-[18px]" /></span><span className="min-w-0 flex-1"><span className="block text-sm font-bold">{label}</span><span className="mt-1 block truncate text-xs text-muted-foreground">{description}</span></span><ArrowLeft className="h-4 w-4 text-muted-foreground transition group-hover:-translate-x-1 group-hover:text-primary" /></Link>)}</CardContent></Card>
        <Card className="rounded-2xl border-slate-200/80 shadow-sm dark:border-white/10"><CardHeader><CardTitle className="flex items-center gap-2 text-base"><ShieldCheck className="h-5 w-5 text-emerald-500" /> حالة التشغيل</CardTitle></CardHeader><CardContent className="space-y-4"><div className={`flex items-center justify-between rounded-2xl p-4 ${demoMode ? "bg-emerald-50 dark:bg-emerald-950/30" : "bg-amber-50 dark:bg-amber-950/30"}`}><div><p className={`text-sm font-bold ${demoMode ? "text-emerald-800 dark:text-emerald-200" : "text-amber-800 dark:text-amber-200"}`}>{demoMode ? "العرض التجريبي" : "التكامل المؤسسي غير مهيأ"}</p><p className={`mt-1 text-xs ${demoMode ? "text-emerald-700/70 dark:text-emerald-300/70" : "text-amber-700/70 dark:text-amber-300/70"}`}>{demoMode ? "بيانات اصطناعية معزولة للعرض" : "لن تُعرض مؤشرات أو بيانات حتى اعتماد عقد القراءة والسياق."}</p></div><span className={`rounded-full px-2.5 py-1 text-[10px] font-bold text-white ${demoMode ? "bg-emerald-500" : "bg-amber-600"}`}>{demoMode ? "معزول" : "محمي"}</span></div><div className="space-y-3"><div className="flex items-center justify-between text-xs"><span className="text-muted-foreground">حماية الجلسة</span><span className="font-bold text-emerald-600">مفعلة</span></div><div className="h-2 overflow-hidden rounded-full bg-muted"><div className="h-full w-full rounded-full bg-gradient-to-l from-emerald-400 to-teal-500" /></div><div className="flex items-center justify-between text-xs"><span className="text-muted-foreground">قراءة مؤسسية</span><span className={`font-bold ${demoMode ? "text-emerald-600" : "text-amber-700"}`}>{demoMode ? "معزولة" : "معلقة حتى التوثيق"}</span></div><div className="h-2 overflow-hidden rounded-full bg-muted"><div className={`h-full rounded-full bg-gradient-to-l ${demoMode ? "w-full from-cyan-400 to-blue-500" : "w-1/4 from-amber-300 to-amber-500"}`} /></div></div></CardContent></Card>
      </section>
    </div>
  );
}
