import { useEffect, useState, type FormEvent } from "react";
import { niamAuthApi } from "@/api/endpoints";
import { apiClient, type NiamSessionSummary } from "@/api/client";
import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle, Input } from "@/components/ui";
import { ErrorDisplay, LoadingSpinner } from "@/components/shared/PageComponents";

const pilotEnabled = import.meta.env.VITE_NIAM_WEB_AUTH_PILOT === "true";

type PilotSession = Awaited<ReturnType<typeof niamAuthApi.login>>;

export function NiamAuthPilotPage() {
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [session, setSession] = useState<PilotSession | null>(null);
  const [sessions, setSessions] = useState<NiamSessionSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSessions = async (accountUuid: string) => {
    const response = await apiClient.listNiamSessions(accountUuid);
    setSessions(response.sessions);
  };

  useEffect(() => {
    if (!pilotEnabled) return;
    void niamAuthApi.refresh()
      .then(async (current) => {
        setSession(current);
        await loadSessions(current.account_uuid);
      })
      .catch(() => {
        // An absent refresh cookie is the normal signed-out state for this pilot.
      });
  }, []);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      const current = await niamAuthApi.login({ login, password });
      setSession(current);
      setPassword("");
      await loadSessions(current.account_uuid);
    } catch {
      setError("تعذر تسجيل الدخول عبر مسار NIAM التجريبي. تحقق من حالة الحساب أو بيئة staging.");
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await niamAuthApi.logout();
    } finally {
      setSession(null);
      setSessions([]);
      setIsLoading(false);
    }
  };

  const logoutAll = async () => {
    if (!session) return;
    setIsLoading(true);
    try {
      await niamAuthApi.logoutAll();
    } finally {
      setSession(null);
      setSessions([]);
      setIsLoading(false);
    }
  };

  const terminateSession = async (sessionUuid: string) => {
    if (!session) return;
    setIsLoading(true);
    try {
      await apiClient.terminateNiamSession(sessionUuid);
      await loadSessions(session.account_uuid);
    } finally {
      setIsLoading(false);
    }
  };

  if (!pilotEnabled) {
    return (
      <Card className="mx-auto mt-10 max-w-2xl border-amber-200">
        <CardHeader>
          <CardTitle>بوابة NIAM التجريبية غير مفعّلة</CardTitle>
          <CardDescription>هذه الصفحة لا تغيّر مصادقة المنصة الأساسية. تُفعّل فقط في بيئة staging عبر feature flag صريح.</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (isLoading && !session) return <LoadingSpinner />;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <header className="rounded-[1.5rem] border border-indigo-100 bg-white p-6 shadow-sm dark:border-indigo-900/40 dark:bg-slate-900/70">
        <p className="text-xs font-bold text-indigo-600">NIAM WEB AUTH PILOT · STAGING ONLY</p>
        <h1 className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">اختبار دورة الجلسة canonical</h1>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">المسار يستخدم cookies HttpOnly وCSRF double-submit، ولا يعرض access أو refresh token في الواجهة.</p>
      </header>

      {error ? <ErrorDisplay error={error} onRetry={() => setError(null)} /> : null}

      {!session ? (
        <Card>
          <CardHeader>
            <CardTitle>تسجيل دخول NIAM</CardTitle>
            <CardDescription>يجب أن يكون الحساب active ومسموحاً له بالدخول في بيئة staging.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={submit}>
              <label className="block text-sm font-medium" htmlFor="niam-login">البريد أو معرف الدخول</label>
              <Input id="niam-login" value={login} onChange={(event) => setLogin(event.target.value)} autoComplete="username" required />
              <label className="block text-sm font-medium" htmlFor="niam-password">كلمة المرور</label>
              <Input id="niam-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required />
              <Button type="submit" disabled={isLoading}>دخول عبر NIAM</Button>
            </form>
          </CardContent>
        </Card>
      ) : (
        <>
          <Card>
            <CardHeader>
              <CardTitle>جلسة NIAM فعالة</CardTitle>
              <CardDescription>السياق مصدره الخادم؛ لا تُستخدم هذه الصفحة لاتخاذ قرارات صلاحية محلية.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-3">
              <span className="rounded-lg bg-slate-100 px-3 py-2 text-xs dark:bg-white/10">Account: {session.account_uuid}</span>
              <span className="rounded-lg bg-slate-100 px-3 py-2 text-xs dark:bg-white/10">Session: {session.session_uuid}</span>
              <Button variant="outline" onClick={logout} disabled={isLoading}>إنهاء الجلسة الحالية</Button>
              <Button variant="destructive" onClick={logoutAll} disabled={isLoading}>إنهاء كل الجلسات</Button>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>الجلسات النشطة</CardTitle>
              <CardDescription>{sessions.length} جلسة يعيدها الخادم للحساب الحالي فقط.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {sessions.map((item) => (
                <div key={item.uuid} className="rounded-xl border border-slate-200 p-3 text-sm dark:border-white/10">
                  <div className="flex flex-wrap justify-between gap-2"><span>{item.is_current ? "الجلسة الحالية" : "جلسة أخرى"}</span><span className="text-muted-foreground">{item.session_type}</span></div>
                  <p className="mt-1 text-xs text-muted-foreground">آخر نشاط: {item.last_activity_at} · الانتهاء: {item.expires_at}</p>
                  {!item.is_current ? <Button className="mt-3" variant="outline" onClick={() => void terminateSession(item.uuid)} disabled={isLoading}>إنهاء هذه الجلسة</Button> : null}
                </div>
              ))}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
