import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, KeyRound, LockKeyhole, LogOut, MonitorSmartphone, ShieldCheck, Smartphone, XCircle } from "lucide-react";
import { securityApi, mfaApi, identityLifecycleApi } from "@/api/endpoints";
import { useAuth } from "@/contexts/AuthContext";
import { classifyApiError } from "@/api/errorHandling";
import { Card, CardContent, CardHeader, CardTitle, Badge, Button } from "@/components/ui";
import { LoadingSpinner, ErrorDisplay } from "@/components/shared/PageComponents";

const numberFormatter = new Intl.NumberFormat("ar-IQ");

export function SecurityPage() {
  const { user, workspaceContext, error: authError } = useAuth();
  const securityQuery = useQuery({ queryKey: ["security"], queryFn: () => securityApi.status() });
  const mfaQuery = useQuery({ queryKey: ["mfa", "status"], queryFn: () => mfaApi.status() });
  const sessionsQuery = useQuery({
    queryKey: ["identity", "sessions", workspaceContext?.account_id],
    queryFn: () => identityLifecycleApi.listSessions(workspaceContext!.account_id),
    enabled: Boolean(workspaceContext?.account_id),
  });
  const mfaEnabled = Boolean(mfaQuery.data?.mfa_enabled);
  const devices = mfaQuery.data?.devices ?? [];
  const sessions = sessionsQuery.data?.sessions ?? [];
  const securityData = securityQuery.data as { status?: string; message?: string; last_24h?: { login_attempts?: number; failed_logins?: number; result_views?: number }; checks?: Record<string, string> } | undefined;
  const failedAttempts = securityData?.last_24h?.failed_logins ?? 0;
  const recentLogins = securityData?.last_24h?.login_attempts ?? 0;

  const logoutAll = async () => {
    if (!workspaceContext?.account_id || !window.confirm("سيتم إنهاء الجلسات الأخرى. هل تريد المتابعة؟")) return;
    try {
      await identityLifecycleApi.terminateAllSessions(workspaceContext.account_id);
      await sessionsQuery.refetch();
    } catch (caught) {
      window.alert(classifyApiError(caught, "تعذر إنهاء الجلسات.").message);
    }
  };

  if (securityQuery.isLoading || mfaQuery.isLoading) return <LoadingSpinner />;
  if (securityQuery.error && mfaQuery.error) return <ErrorDisplay onRetry={() => { void securityQuery.refetch(); void mfaQuery.refetch(); }} />;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <header className="flex flex-col gap-4 rounded-[1.5rem] border border-indigo-100 bg-white p-5 shadow-[0_18px_44px_-36px_rgba(15,23,42,0.48)] dark:border-indigo-900/40 dark:bg-slate-900/70 sm:flex-row sm:items-end sm:justify-between sm:p-6"><div><div className="mb-3 inline-flex items-center gap-2 rounded-full border border-indigo-100 bg-indigo-50 px-3 py-1.5 text-xs font-bold text-indigo-700 dark:border-indigo-900/60 dark:bg-indigo-950/35 dark:text-indigo-200"><ShieldCheck className="h-3.5 w-3.5" /> مركز الحماية</div><h1 className="text-2xl font-bold tracking-tight text-[#0F172A] dark:text-white sm:text-3xl">الأمان والجلسات</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">المعلومات المعروضة منعكسة من الخادم. لا تُعرض secrets أو tokens، ولا تعتمد الواجهة كحد أمني.</p></div><div className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-700 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-200"><LockKeyhole className="h-4 w-4 text-[#0D9488]" /> {user?.email || "الحساب الحالي"}</div></header>

      {authError && <div className="rounded-2xl border border-amber-500/25 bg-amber-50 p-4 text-sm text-amber-950 dark:bg-amber-500/10 dark:text-amber-100" role="alert">{authError.message}</div>}
      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"><Card className="border-teal-100 dark:border-teal-900/40"><CardContent className="p-4"><div className="flex items-center justify-between"><p className="text-xs text-muted-foreground">الجلسات الحالية</p><MonitorSmartphone className="h-4 w-4 text-[#0D9488]" /></div><p className="mt-3 text-2xl font-bold">{workspaceContext ? numberFormatter.format(sessions.length) : "—"}</p><p className="mt-1 text-[11px] text-muted-foreground">{workspaceContext ? "ضمن account context المعتمد" : "يتطلب account context من الخادم"}</p></CardContent></Card><Card className="border-sky-100 dark:border-sky-900/40"><CardContent className="p-4"><div className="flex items-center justify-between"><p className="text-xs text-muted-foreground">تسجيلات آخر 24 ساعة</p><CheckCircle2 className="h-4 w-4 text-sky-600" /></div><p className="mt-3 text-2xl font-bold">{numberFormatter.format(recentLogins)}</p><p className="mt-1 text-[11px] text-muted-foreground">{securityData?.last_24h ? "حسب السجل المتاح" : "ملخص إداري غير متاح لهذا الحساب"}</p></CardContent></Card><Card className={failedAttempts > 0 ? "border-amber-200 dark:border-amber-900/50" : "border-emerald-100 dark:border-emerald-900/40"}><CardContent className="p-4"><div className="flex items-center justify-between"><p className="text-xs text-muted-foreground">محاولات فاشلة</p><AlertTriangle className={`h-4 w-4 ${failedAttempts > 0 ? "text-amber-600" : "text-emerald-600"}`} /></div><p className="mt-3 text-2xl font-bold">{numberFormatter.format(failedAttempts)}</p><p className="mt-1 text-[11px] text-muted-foreground">لا يتم كشف تفاصيل حسابات أخرى</p></CardContent></Card><Card className={mfaEnabled ? "border-emerald-100 dark:border-emerald-900/40" : "border-rose-100 dark:border-rose-900/40"}><CardContent className="p-4"><div className="flex items-center justify-between"><p className="text-xs text-muted-foreground">MFA</p><KeyRound className={`h-4 w-4 ${mfaEnabled ? "text-emerald-600" : "text-rose-600"}`} /></div><p className={`mt-3 text-lg font-bold ${mfaEnabled ? "text-emerald-700 dark:text-emerald-300" : "text-rose-700 dark:text-rose-300"}`}>{mfaEnabled ? "مفعّلة" : "غير مفعّلة"}</p><p className="mt-1 text-[11px] text-muted-foreground">من `/mfa/status`</p></CardContent></Card></section>

      <section className="grid gap-4 lg:grid-cols-2"><Card className="border-indigo-100 dark:border-indigo-900/40"><CardHeader className="border-b border-indigo-100/80 p-5 dark:border-indigo-900/40"><CardTitle className="flex items-center gap-2 text-base"><KeyRound className="h-5 w-5 text-indigo-600" /> MFA وPasskeys</CardTitle></CardHeader><CardContent className="space-y-4 p-5"><div className="flex items-start gap-3 rounded-2xl bg-indigo-50/70 p-4 dark:bg-indigo-950/20"><LockKeyhole className="mt-0.5 h-5 w-5 shrink-0 text-indigo-600 dark:text-indigo-300" /><div><p className="text-sm font-semibold">{mfaEnabled ? "طبقة مصادقة إضافية مفعّلة" : "طبقة مصادقة إضافية غير مفعّلة"}</p><p className="mt-1 text-xs leading-5 text-muted-foreground">عوامل TOTP وWebAuthn تدار بالخادم. لا تحفظ الواجهة secret أو backup codes.</p></div></div>{devices.length === 0 ? <p className="text-sm text-muted-foreground">لا توجد أجهزة MFA مسجلة في الاستجابة الحالية.</p> : <div className="space-y-2">{devices.map((device) => <div key={device.id} className="flex items-center justify-between rounded-xl border border-slate-200 p-3 dark:border-white/10"><div className="flex items-center gap-2"><Smartphone className="h-4 w-4 text-teal-600" /><span className="text-sm font-semibold">{device.name}</span></div><Badge variant="secondary">{device.type}</Badge></div>)}</div>}</CardContent></Card><Card className="border-slate-200/80 dark:border-slate-800"><CardHeader className="border-b border-slate-100 p-5 dark:border-white/10"><CardTitle className="flex items-center gap-2 text-base"><MonitorSmartphone className="h-5 w-5 text-[#0D9488]" /> الجلسات والأجهزة</CardTitle></CardHeader><CardContent className="space-y-4 p-5">{!workspaceContext ? <div className="rounded-2xl border border-amber-500/25 bg-amber-50 p-4 text-sm leading-6 text-amber-950 dark:bg-amber-500/10 dark:text-amber-100">لا يمكن عرض جلسات NIAM قبل أن يعيد الخادم account context صالحاً. لن يتم استخدام user id المحلي كبديل.</div> : sessionsQuery.isLoading ? <LoadingSpinner className="py-5" /> : sessions.length === 0 ? <p className="text-sm text-muted-foreground">لا توجد جلسات نشطة في الاستجابة الحالية.</p> : <div className="space-y-2">{sessions.map((session) => <div key={session.uuid} className="flex items-center justify-between rounded-xl border border-slate-200 p-3 dark:border-white/10"><div><p className="text-sm font-semibold">جلسة {session.id}</p><p className="mt-1 text-xs text-muted-foreground break-all">{session.uuid}</p></div><Badge variant="secondary">نشطة</Badge></div>)}</div>}<Button variant="outline" className="w-full" disabled={!workspaceContext || sessionsQuery.isLoading} onClick={() => void logoutAll}><LogOut className="me-2 h-4 w-4" />إنهاء كل الجلسات</Button>{sessionsQuery.error && <p className="text-xs text-destructive" role="alert">{classifyApiError(sessionsQuery.error, "تعذر تحميل الجلسات.").message}</p>}</CardContent></Card></section>

      <Card><CardHeader><CardTitle className="flex items-center gap-2"><ShieldCheck className="h-5 w-5 text-teal-600" /> حالة الحساب والأحداث</CardTitle></CardHeader><CardContent className="space-y-3 text-sm"><div className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-600" /> حالة endpoint الأمني: {securityData?.status || "غير متاحة"}</div>{securityData?.message && <p className="text-muted-foreground">{securityData.message}</p>}<p className="text-xs leading-6 text-muted-foreground">السجل التفصيلي للأحداث الأمنية وخصائص الأجهزة الموسعة تعتمد على endpoints إدارية أو NIAM إضافية غير متاحة للحساب الحالي. لن تعرض الواجهة بيانات غير موجودة في العقد.</p>{securityData?.checks && <div className="grid gap-2 sm:grid-cols-2">{Object.entries(securityData.checks).map(([key, value]) => <div key={key} className="flex items-center gap-2 rounded-xl bg-slate-50 p-3 text-xs dark:bg-white/[0.04]"><XCircle className="h-3.5 w-3.5 text-slate-400" />{key}: {value}</div>)}</div>}</CardContent></Card>
    </div>
  );
}
