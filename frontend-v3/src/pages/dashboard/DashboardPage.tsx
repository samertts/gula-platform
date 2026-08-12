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

const quickLinks = [
  { label: "المرضى", description: "الوصول إلى السجلات المصرح بها", path: "/patients", icon: Users },
  { label: "الطلبات", description: "متابعة مسار الطلبات والعينات", path: "/orders", icon: ClipboardList },
  { label: "النتائج", description: "مراجعة النتائج والتحقق منها", path: "/results", icon: FlaskConical },
  { label: "التنبيهات", description: "مراقبة الحالات ذات الأولوية", path: "/alerts", icon: AlertTriangle },
];

export function DashboardPage() {
  const { demoMode, user } = useAuth();
  const { data, isLoading, isError } = useQuery<Record<string, unknown>>({
    queryKey: ["dashboard", demoMode ? "demo" : "institution"],
    queryFn: async () => {
      if (demoMode) return dashboardApi.demo();
      return dashboardApi.dashboard() as unknown as Record<string, unknown>;
    },
  });

  return (
    <div className="mx-auto max-w-7xl space-y-7">
      <section className="relative overflow-hidden rounded-[1.75rem] bg-slate-950 p-6 text-white shadow-[0_24px_70px_-35px_rgba(15,23,42,0.75)] md:p-8">
        <div className="absolute -left-10 -top-24 h-64 w-64 rounded-full bg-cyan-400/20 blur-3xl" />
        <div className="absolute -bottom-28 right-10 h-72 w-72 rounded-full bg-indigo-500/25 blur-3xl" />
        <div className="relative flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
          <div className="max-w-2xl">
            <div className="mb-4 flex flex-wrap items-center gap-2 text-xs font-semibold"><span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-3 py-1.5"><span className="h-2 w-2 rounded-full bg-emerald-400" /> النظام متصل</span>{demoMode && <span className="inline-flex items-center gap-2 rounded-full border border-amber-300/20 bg-amber-300/10 px-3 py-1.5 text-amber-100"><ShieldCheck className="h-3.5 w-3.5" /> عرض تجريبي معزول</span>}</div>
            <p className="text-sm text-cyan-200">صباح الخير{user?.name ? `، ${user.name}` : ""}</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight md:text-4xl">مركز العمليات الصحية</h1>
            <p className="mt-3 max-w-xl text-sm leading-7 text-slate-300">نظرة موحّدة على سير العمل، مؤشرات الأداء، والتنبيهات ذات الأولوية ضمن مساحة العمل الحالية.</p>
          </div>
          <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.07] p-4 text-sm text-slate-200"><HeartPulse className="h-7 w-7 text-cyan-300" /><div><p className="font-bold">مساحة عمل آمنة</p><p className="mt-1 text-xs text-slate-400">RBAC · Tenant isolation · Audit</p></div></div>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {statCards.map(({ label, key, icon: Icon, color, surface }) => {
          const value = data?.[key];
          return <Card key={key} className="group overflow-hidden rounded-2xl border-slate-200/80 shadow-sm transition duration-200 hover:-translate-y-0.5 hover:shadow-lg dark:border-white/10"><CardContent className="relative p-5"><div className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-l ${color}`} /><div className="flex items-start justify-between gap-3"><span className={`flex h-11 w-11 items-center justify-center rounded-2xl ${surface}`}><Icon className="h-5 w-5" /></span><span className="text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground">اليوم</span></div><p className="mt-5 text-sm text-muted-foreground">{label}</p><p className="mt-1 text-3xl font-bold tracking-tight">{isLoading ? "…" : isError ? "—" : String(value ?? 0)}</p></CardContent></Card>;
        })}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <Card className="rounded-2xl border-slate-200/80 shadow-sm dark:border-white/10"><CardHeader className="flex flex-row items-center justify-between space-y-0"><div><CardTitle className="flex items-center gap-2 text-base"><Activity className="h-5 w-5 text-primary" /> مسارات العمل السريعة</CardTitle><p className="mt-1 text-xs text-muted-foreground">انتقل مباشرة إلى الجزء الذي تريد متابعته.</p></div><span className="rounded-full bg-primary/10 px-2.5 py-1 text-[10px] font-bold text-primary">وصول سريع</span></CardHeader><CardContent className="grid gap-3 sm:grid-cols-2">{quickLinks.map(({ label, description, path, icon: Icon }) => <Link key={path} to={path} className="group flex items-center gap-3 rounded-2xl border border-slate-200/80 p-3.5 transition hover:-translate-y-0.5 hover:border-primary/30 hover:bg-primary/[0.03] dark:border-white/10"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-primary transition group-hover:bg-primary group-hover:text-white dark:bg-white/10"><Icon className="h-[18px] w-[18px]" /></span><span className="min-w-0 flex-1"><span className="block text-sm font-bold">{label}</span><span className="mt-1 block truncate text-xs text-muted-foreground">{description}</span></span><ArrowLeft className="h-4 w-4 text-muted-foreground transition group-hover:-translate-x-1 group-hover:text-primary" /></Link>)}</CardContent></Card>
        <Card className="rounded-2xl border-slate-200/80 shadow-sm dark:border-white/10"><CardHeader><CardTitle className="flex items-center gap-2 text-base"><ShieldCheck className="h-5 w-5 text-emerald-500" /> حالة التشغيل</CardTitle></CardHeader><CardContent className="space-y-4"><div className="flex items-center justify-between rounded-2xl bg-emerald-50 p-4 dark:bg-emerald-950/30"><div><p className="text-sm font-bold text-emerald-800 dark:text-emerald-200">الخدمات الأساسية</p><p className="mt-1 text-xs text-emerald-700/70 dark:text-emerald-300/70">الاتصال والاستجابة ضمن مساحة العمل</p></div><span className="rounded-full bg-emerald-500 px-2.5 py-1 text-[10px] font-bold text-white">نشط</span></div><div className="space-y-3"><div className="flex items-center justify-between text-xs"><span className="text-muted-foreground">حماية الجلسة</span><span className="font-bold text-emerald-600">مفعلة</span></div><div className="h-2 overflow-hidden rounded-full bg-muted"><div className="h-full w-[92%] rounded-full bg-gradient-to-l from-emerald-400 to-teal-500" /></div><div className="flex items-center justify-between text-xs"><span className="text-muted-foreground">عزل المؤسسة</span><span className="font-bold text-emerald-600">مفعّل</span></div><div className="h-2 overflow-hidden rounded-full bg-muted"><div className="h-full w-full rounded-full bg-gradient-to-l from-cyan-400 to-blue-500" /></div></div></CardContent></Card>
      </section>
    </div>
  );
}
