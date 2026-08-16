import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, ArrowRight, KeyRound, ShieldCheck } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useLocale } from "@/contexts/LocaleContext";
import { authApi } from "@/api/endpoints";
import { classifyApiError } from "@/api/errorHandling";
import { Button, Input } from "@/components/ui";

export function RecoveryPage() {
  const { t } = useTranslation();
  const { isRTL } = useLocale();
  const [identifier, setIdentifier] = useState("");
  const [status, setStatus] = useState<"idle" | "pending" | "success" | "failed" | "expired">("idle");
  const [error, setError] = useState("");
  const Arrow = isRTL ? ArrowLeft : ArrowRight;

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setStatus("pending");
    setError("");
    try {
      await authApi.forgotPassword(identifier.trim());
      setStatus("success");
    } catch (caught) {
      const info = classifyApiError(caught, "تعذر إنشاء طلب الاسترداد.");
      setError(info.message);
      setStatus(info.code.toLowerCase().includes("expired") ? "expired" : "failed");
    }
  };

  return (
    <section className="mx-auto max-w-xl rounded-[1.75rem] border border-slate-200 bg-white p-7 shadow-[0_24px_70px_-40px_rgba(15,23,42,0.45)] dark:border-white/10 dark:bg-slate-950 sm:p-10">
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary"><KeyRound className="h-6 w-6" /></div>
      <p className="mt-5 text-xs font-bold uppercase tracking-[0.16em] text-primary">GULA · {t("loginPage.secureAccess")}</p>
      <h1 className="mt-2 text-2xl font-bold tracking-tight">استرداد الوصول</h1>
      <p className="mt-3 text-sm leading-7 text-muted-foreground">سيتم التعامل مع الطلب بطريقة موحدة لا تكشف ما إذا كان الحساب موجوداً. أي رابط استرداد حساس يتم التحقق منه في الخادم.</p>
      {status === "success" ? (
        <div className="mt-6 rounded-2xl border border-emerald-500/25 bg-emerald-50 p-4 text-sm leading-7 text-emerald-900 dark:bg-emerald-500/10 dark:text-emerald-100" role="status">
          <ShieldCheck className="mb-2 h-5 w-5" /> تم استلام الطلب. إذا كانت البيانات مرتبطة بحساب، ستصل تعليمات آمنة عبر القناة المعتمدة.
        </div>
      ) : (
        <form className="mt-7 space-y-4" onSubmit={submit} aria-busy={status === "pending"}>
          {error && <div className="rounded-xl border border-destructive/20 bg-destructive/10 px-3.5 py-3 text-sm leading-6 text-destructive" role="alert">{error}</div>}
          {status === "expired" && <p className="text-xs text-amber-700" role="status">انتهت صلاحية الطلب. ابدأ طلباً جديداً.</p>}
          <div className="space-y-2">
            <label className="text-sm font-semibold" htmlFor="recovery-identifier">البريد الإلكتروني أو رقم الهاتف</label>
            <Input id="recovery-identifier" autoComplete="username" value={identifier} onChange={(event) => setIdentifier(event.target.value)} required />
          </div>
          <Button className="h-11 w-full" type="submit" loading={status === "pending"}>إرسال طلب الاسترداد</Button>
        </form>
      )}
      <Link className="mt-6 inline-flex items-center gap-2 text-sm font-bold text-primary hover:underline" to="/login">العودة إلى تسجيل الدخول <Arrow className="h-4 w-4" /></Link>
    </section>
  );
}
