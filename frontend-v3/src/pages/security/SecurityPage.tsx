import { useQuery } from "@tanstack/react-query";
import { securityApi } from "@/api/endpoints";
import { Card, CardContent, CardHeader, CardTitle, Badge } from "@/components/ui";
import { LoadingSpinner, ErrorDisplay } from "@/components/shared/PageComponents";
import { AlertTriangle, CheckCircle2, KeyRound, LockKeyhole, MonitorSmartphone, Shield, ShieldCheck } from "lucide-react";

const numberFormatter = new Intl.NumberFormat("ar-IQ");

export function SecurityPage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["security"],
    queryFn: () => securityApi.status(),
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  const mfaEnabled = Boolean(data?.mfa_enabled);
  const failedAttempts = data?.failed_attempts ?? 0;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <header className="flex flex-col gap-4 rounded-[1.5rem] border border-indigo-100 bg-white p-5 shadow-[0_18px_44px_-36px_rgba(15,23,42,0.48)] dark:border-indigo-900/40 dark:bg-slate-900/70 sm:flex-row sm:items-end sm:justify-between sm:p-6"><div><div className="mb-3 inline-flex items-center gap-2 rounded-full border border-indigo-100 bg-indigo-50 px-3 py-1.5 text-xs font-bold text-indigo-700 dark:border-indigo-900/60 dark:bg-indigo-950/35 dark:text-indigo-200"><ShieldCheck className="h-3.5 w-3.5" /> مركز الحماية</div><h1 className="text-2xl font-bold tracking-tight text-[#0F172A] dark:text-white sm:text-3xl">الأمان</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">مؤشرات الحماية والجلسة كما يثبتها الخادم في السياق الحالي. لا تُنفذ تغييرات أمنية مباشرة من هذه الصفحة.</p></div><div className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-700 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-200"><LockKeyhole className="h-4 w-4 text-[#0D9488]" /> عرض أمني محكوم</div></header>

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="border-teal-100 dark:border-teal-900/40"><CardContent className="p-4"><div className="flex items-center justify-between"><p className="text-xs text-muted-foreground">جلسات نشطة</p><MonitorSmartphone className="h-4 w-4 text-[#0D9488]" /></div><p className="mt-3 text-2xl font-bold">{numberFormatter.format(data?.active_sessions ?? 0)}</p><p className="mt-1 text-[11px] text-muted-foreground">ضمن نطاق الجلسة</p></CardContent></Card>
        <Card className="border-sky-100 dark:border-sky-900/40"><CardContent className="p-4"><div className="flex items-center justify-between"><p className="text-xs text-muted-foreground">تسجيلات حديثة</p><CheckCircle2 className="h-4 w-4 text-sky-600" /></div><p className="mt-3 text-2xl font-bold">{numberFormatter.format(data?.recent_logins ?? 0)}</p><p className="mt-1 text-[11px] text-muted-foreground">حسب حالة الخادم</p></CardContent></Card>
        <Card className={failedAttempts > 0 ? "border-amber-200 dark:border-amber-900/50" : "border-emerald-100 dark:border-emerald-900/40"}><CardContent className="p-4"><div className="flex items-center justify-between"><p className="text-xs text-muted-foreground">محاولات فاشلة</p><AlertTriangle className={`h-4 w-4 ${failedAttempts > 0 ? "text-amber-600" : "text-emerald-600"}`} /></div><p className="mt-3 text-2xl font-bold">{numberFormatter.format(failedAttempts)}</p><p className="mt-1 text-[11px] text-muted-foreground">يتطلب الانتباه عند الارتفاع</p></CardContent></Card>
        <Card className={mfaEnabled ? "border-emerald-100 dark:border-emerald-900/40" : "border-rose-100 dark:border-rose-900/40"}><CardContent className="p-4"><div className="flex items-center justify-between"><p className="text-xs text-muted-foreground">المصادقة الثنائية</p><KeyRound className={`h-4 w-4 ${mfaEnabled ? "text-emerald-600" : "text-rose-600"}`} /></div><p className={`mt-3 text-lg font-bold ${mfaEnabled ? "text-emerald-700 dark:text-emerald-300" : "text-rose-700 dark:text-rose-300"}`}>{mfaEnabled ? "مفعّلة" : "غير مفعّلة"}</p><p className="mt-1 text-[11px] text-muted-foreground">الحالة الموثقة حاليًا</p></CardContent></Card>
      </section>

      <section className="grid gap-4 lg:grid-cols-2"><Card className="border-indigo-100 dark:border-indigo-900/40"><CardHeader className="border-b border-indigo-100/80 p-5 dark:border-indigo-900/40"><CardTitle className="flex items-center gap-2 text-base"><Shield className="h-5 w-5 text-indigo-600" /> حالة المصادقة</CardTitle></CardHeader><CardContent className="p-5"><div className="flex items-start gap-3 rounded-2xl bg-indigo-50/70 p-4 dark:bg-indigo-950/20"><LockKeyhole className="mt-0.5 h-5 w-5 shrink-0 text-indigo-600 dark:text-indigo-300" /><div><p className="text-sm font-semibold">{mfaEnabled ? "طبقة مصادقة إضافية مفعّلة" : "طبقة مصادقة إضافية غير مفعّلة"}</p><p className="mt-1 text-xs leading-5 text-muted-foreground">تتم إدارة عوامل المصادقة من نظام الهوية المؤسسي، ولا تُحفظ تغييرات مباشرة من هذه الواجهة.</p></div></div></CardContent></Card><Card className="border-slate-200/80 dark:border-slate-800"><CardHeader className="border-b border-slate-100 p-5 dark:border-white/10"><CardTitle className="flex items-center gap-2 text-base"><MonitorSmartphone className="h-5 w-5 text-[#0D9488]" /> الجلسات والأجهزة</CardTitle></CardHeader><CardContent className="p-5"><div className="flex items-center justify-between rounded-2xl bg-slate-50 p-4 dark:bg-white/[0.04]"><div><p className="text-sm font-semibold">جلسات ظاهرة</p><p className="mt-1 text-xs text-muted-foreground">{numberFormatter.format(data?.active_sessions ?? 0)} جلسة ضمن التقرير الحالي</p></div><Badge variant="secondary">قراءة فقط</Badge></div><p className="mt-4 text-xs leading-5 text-muted-foreground">سيظهر سجل تفصيلي وإجراء إبطال الجلسة بعد ربط عقد إدارة الجلسات وتسجيل التدقيق.</p></CardContent></Card></section>
    </div>
  );
}
