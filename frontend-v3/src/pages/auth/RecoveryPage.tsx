import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, ArrowRight, CheckCircle2, KeyRound, ShieldAlert, ShieldCheck } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useLocale } from "@/contexts/LocaleContext";
import { authApi } from "@/api/endpoints";
import { classifyApiError } from "@/api/errorHandling";
import { Button, Input } from "@/components/ui";

type RecoveryStep = "request" | "verify" | "reset" | "success";

type RecoveryErrorInfo = {
  code?: string;
  message?: string;
  detail?: { code?: string; message?: string };
};

function createIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID();
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function RecoveryPage() {
  const { t } = useTranslation();
  const { isRTL } = useLocale();
  const [identifier, setIdentifier] = useState("");
  const [token, setToken] = useState("");
  const [requestId, setRequestId] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [step, setStep] = useState<RecoveryStep>("request");
  const [pendingReview, setPendingReview] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const Arrow = isRTL ? ArrowLeft : ArrowRight;

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const queryToken = params.get("token");
    const queryRequestId = params.get("request_id");
    if (queryToken) {
      setToken(queryToken);
      setStep("verify");
      // Remove recovery material from browser history and referrer surfaces.
      window.history.replaceState({}, document.title, window.location.pathname);
    }
    if (queryRequestId) setRequestId(queryRequestId);
  }, []);

  const submitRequest = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    setPendingReview(false);
    try {
      await authApi.forgotPassword(identifier.trim(), createIdempotencyKey());
      setStep("success");
    } catch (caught) {
      const info = classifyApiError(caught, "تعذر إنشاء طلب الاسترداد.");
      setError(info.message);
    } finally {
      setBusy(false);
    }
  };

  const verifyToken = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    setPendingReview(false);
    try {
      const result = await authApi.verifyRecovery(token.trim(), requestId.trim() || undefined);
      if (typeof result.status === "string" && result.status === "pending_review") {
        setPendingReview(true);
        return;
      }
      setStep("reset");
    } catch (caught) {
      const raw = caught as RecoveryErrorInfo;
      const code = raw.detail?.code ?? raw.code ?? "";
      if (code === "RECOVERY_PENDING_REVIEW") setPendingReview(true);
      setError(classifyApiError(caught, "تعذر التحقق من طلب الاسترداد.").message);
    } finally {
      setBusy(false);
    }
  };

  const resetPassword = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await authApi.resetPassword(token.trim(), newPassword, requestId.trim() || undefined);
      setStep("success");
    } catch (caught) {
      setError(classifyApiError(caught, "تعذر تغيير كلمة المرور.").message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="mx-auto max-w-xl rounded-[1.75rem] border border-slate-200 bg-white p-7 shadow-[0_24px_70px_-40px_rgba(15,23,42,0.45)] dark:border-white/10 dark:bg-slate-950 sm:p-10">
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary"><KeyRound className="h-6 w-6" /></div>
      <p className="mt-5 text-xs font-bold uppercase tracking-[0.16em] text-primary">GULA · {t("loginPage.secureAccess")}</p>
      <h1 className="mt-2 text-2xl font-bold tracking-tight">استرداد الوصول</h1>
      <p className="mt-3 text-sm leading-7 text-muted-foreground">التحقق من الاسترداد يتم بالخادم فقط. لا تعرض الواجهة token في النص، ولا تحفظه في التخزين المحلي، وتزيله من عنوان الصفحة مباشرةً عند فتح رابط رسمي.</p>

      {error && <div className="mt-5 rounded-xl border border-destructive/20 bg-destructive/10 px-3.5 py-3 text-sm leading-6 text-destructive" role="alert">{error}</div>}
      {pendingReview && <div className="mt-5 flex gap-3 rounded-2xl border border-amber-500/25 bg-amber-50 p-4 text-sm leading-7 text-amber-950 dark:bg-amber-500/10 dark:text-amber-100" role="status"><ShieldAlert className="mt-1 h-5 w-5 shrink-0" /><span>يتطلب هذا الطلب مراجعة أمنية يدوية لأن قناة الاسترداد المعتمدة غير متاحة أو لأن العملية عالية الحساسية. لم يتم تغيير كلمة المرور.</span></div>}

      {step === "request" && (
        <form className="mt-7 space-y-4" onSubmit={submitRequest} aria-busy={busy}>
          <div className="space-y-2"><label className="text-sm font-semibold" htmlFor="recovery-identifier">البريد الإلكتروني أو رقم الهاتف</label><Input id="recovery-identifier" autoComplete="username" value={identifier} onChange={(event) => setIdentifier(event.target.value)} required /></div>
          <Button className="h-11 w-full" type="submit" loading={busy}>إرسال طلب الاسترداد</Button>
        </form>
      )}

      {step === "verify" && (
        <form className="mt-7 space-y-4" onSubmit={verifyToken} aria-busy={busy}>
          <div className="rounded-2xl border border-sky-500/20 bg-sky-50 p-4 text-sm leading-7 text-sky-950 dark:bg-sky-500/10 dark:text-sky-100">أدخل الرمز الذي وصل عبر القناة الرسمية. سيُستهلك التحقق مرة واحدة، ولن يكشف الخادم حالة أي حساب.</div>
          <div className="space-y-2"><label className="text-sm font-semibold" htmlFor="recovery-token">رمز الاسترداد</label><Input id="recovery-token" type="password" autoComplete="one-time-code" value={token} onChange={(event) => setToken(event.target.value)} required /></div>
          <div className="space-y-2"><label className="text-sm font-semibold" htmlFor="recovery-request-id">معرّف الطلب، إن وُجد في الرسالة</label><Input id="recovery-request-id" inputMode="text" value={requestId} onChange={(event) => setRequestId(event.target.value)} /></div>
          <Button className="h-11 w-full" type="submit" loading={busy}>تحقق من الرمز</Button>
        </form>
      )}

      {step === "reset" && (
        <form className="mt-7 space-y-4" onSubmit={resetPassword} aria-busy={busy}>
          <div className="flex gap-3 rounded-2xl border border-indigo-500/20 bg-indigo-50 p-4 text-sm leading-7 text-indigo-950 dark:bg-indigo-500/10 dark:text-indigo-100"><ShieldCheck className="mt-1 h-5 w-5 shrink-0" /><span>الرمز موثق من الخادم. اختر كلمة مرور جديدة من 12 محرفاً على الأقل. بعد النجاح ستُبطل الجلسات السابقة ويجب تسجيل الدخول مجدداً.</span></div>
          <div className="space-y-2"><label className="text-sm font-semibold" htmlFor="new-recovery-password">كلمة المرور الجديدة</label><Input id="new-recovery-password" type="password" autoComplete="new-password" minLength={12} value={newPassword} onChange={(event) => setNewPassword(event.target.value)} required /></div>
          <Button className="h-11 w-full" type="submit" loading={busy}>تغيير كلمة المرور</Button>
        </form>
      )}

      {step === "success" && (
        <div className="mt-6 flex gap-3 rounded-2xl border border-emerald-500/25 bg-emerald-50 p-4 text-sm leading-7 text-emerald-900 dark:bg-emerald-500/10 dark:text-emerald-100" role="status"><CheckCircle2 className="mt-1 h-5 w-5 shrink-0" /><span>{token ? "تم تغيير كلمة المرور وإبطال الجلسات السابقة. سجّل الدخول من جديد." : "تم استلام الطلب. إذا كان الحساب مؤهلاً فستتم المعالجة عبر القناة المعتمدة أو المراجعة الأمنية؛ لم يتم تغيير الحساب بعد."}</span></div>
      )}

      <Link className="mt-6 inline-flex items-center gap-2 text-sm font-bold text-primary hover:underline" to="/login">العودة إلى تسجيل الدخول <Arrow className="h-4 w-4" /></Link>
    </section>
  );
}
