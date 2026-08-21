import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, ArrowRight, MailCheck, RefreshCw, ShieldCheck } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useLocale } from "@/contexts/LocaleContext";
import { authApi } from "@/api/endpoints";
import { classifyApiError } from "@/api/errorHandling";
import { Button, Input } from "@/components/ui";

type VerificationStatus = "idle" | "pending" | "success" | "failed" | "expired";

type VerificationStage = "request" | "code" | "verified";

export function VerificationPage() {
  const { t } = useTranslation();
  const { isRTL } = useLocale();
  const Arrow = isRTL ? ArrowLeft : ArrowRight;
  const [identifier, setIdentifier] = useState("");
  const [code, setCode] = useState("");
  const [stage, setStage] = useState<VerificationStage>("request");
  const [status, setStatus] = useState<VerificationStatus>("idle");
  const [message, setMessage] = useState("");

  const classifyFailure = (caught: unknown, fallback: string) => {
    const info = classifyApiError(caught, fallback);
    setMessage(info.message);
    setStatus(info.code.toLowerCase().includes("expired") ? "expired" : "failed");
  };

  const requestCode = async () => {
    setStatus("pending");
    setMessage("");
    try {
      await authApi.requestVerification(identifier.trim());
      setStage("code");
      setStatus("success");
      setMessage("إذا كانت البيانات مرتبطة بحساب، فسيتم إرسال رمز تحقق عبر القناة المعتمدة.");
    } catch (caught) {
      classifyFailure(caught, "تعذر بدء طلب التحقق.");
    }
  };

  const submitRequest = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await requestCode();
  };

  const confirmCode = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setStatus("pending");
    setMessage("");
    try {
      await authApi.confirmVerification(identifier.trim(), code.trim());
      setStage("verified");
      setStatus("success");
      setMessage("تم تسجيل التحقق بنجاح. يمكنك العودة إلى تسجيل الدخول.");
    } catch (caught) {
      classifyFailure(caught, "تعذر إكمال التحقق.");
    }
  };

  return (
    <section className="mx-auto max-w-xl rounded-[1.75rem] border border-slate-200 bg-white p-7 shadow-[0_24px_70px_-40px_rgba(15,23,42,0.45)] dark:border-white/10 dark:bg-slate-950 sm:p-10">
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary"><MailCheck className="h-6 w-6" /></div>
      <p className="mt-5 text-xs font-bold uppercase tracking-[0.16em] text-primary">GULA · {t("loginPage.secureAccess")}</p>
      <h1 className="mt-2 text-2xl font-bold tracking-tight">التحقق من وسيلة الاتصال</h1>
      <p className="mt-3 text-sm leading-7 text-muted-foreground">يتم التحقق من البريد أو الهاتف عبر الخادم فقط. لا تكشف هذه الصفحة وجود حساب، ولا تقبل حالة تحقق مرسلة من المتصفح.</p>

      {message && <div className={`mt-6 rounded-2xl border p-4 text-sm leading-7 ${status === "success" ? "border-emerald-500/25 bg-emerald-50 text-emerald-900 dark:bg-emerald-500/10 dark:text-emerald-100" : "border-destructive/20 bg-destructive/10 text-destructive"}`} role={status === "success" ? "status" : "alert"}>{status === "success" && <ShieldCheck className="mb-2 h-5 w-5" />}{message}</div>}

      {stage === "verified" ? (
        <div className="mt-6 rounded-2xl border border-slate-200 p-4 text-sm leading-7 text-muted-foreground dark:border-white/10">تمت العملية دون إنشاء جلسة جديدة أو منح صلاحية إضافية.</div>
      ) : stage === "request" ? (
        <form className="mt-7 space-y-4" onSubmit={submitRequest} aria-busy={status === "pending"}>
          <div className="space-y-2"><label className="text-sm font-semibold" htmlFor="verification-identifier">البريد الإلكتروني أو رقم الهاتف</label><Input id="verification-identifier" autoComplete="username" value={identifier} onChange={(event) => setIdentifier(event.target.value)} required /></div>
          <Button className="h-11 w-full" type="submit" loading={status === "pending"}>إرسال طلب التحقق</Button>
        </form>
      ) : (
        <form className="mt-7 space-y-4" onSubmit={confirmCode} aria-busy={status === "pending"}>
          <div className="space-y-2"><label className="text-sm font-semibold" htmlFor="verification-code">رمز التحقق</label><Input id="verification-code" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} value={code} onChange={(event) => setCode(event.target.value.replace(/\D/g, "").slice(0, 6))} required /></div>
          {status === "expired" && <p className="text-xs text-amber-700" role="status">انتهت صلاحية الرمز أو الطلب. اطلب رمزاً جديداً.</p>}
          <Button className="h-11 w-full" type="submit" loading={status === "pending"}>تأكيد الرمز</Button>
          <Button className="h-10 w-full" type="button" variant="outline" loading={status === "pending"} onClick={() => void requestCode()}><RefreshCw className="me-2 h-4 w-4" />إعادة إرسال الرمز</Button>
        </form>
      )}

      <div className="mt-7 flex flex-wrap items-center justify-between gap-4 border-t border-slate-200 pt-6 dark:border-white/10"><Link className="inline-flex items-center gap-2 text-sm font-bold text-primary hover:underline" to="/login">العودة إلى تسجيل الدخول <Arrow className="h-4 w-4" /></Link><Link className="text-sm font-bold text-primary hover:underline" to="/register">طلب حساب</Link></div>
    </section>
  );
}
