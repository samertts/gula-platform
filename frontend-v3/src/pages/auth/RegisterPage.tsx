import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ArrowLeft, ArrowRight, Building2, CheckCircle2, Landmark, Mail, Phone, ShieldCheck, UserRound } from "lucide-react";
import { useLocale } from "@/contexts/LocaleContext";
import { identityLifecycleApi } from "@/api/endpoints";
import { classifyApiError } from "@/api/errorHandling";
import { Button, Input } from "@/components/ui";

type RequestStatus = "idle" | "pending" | "accepted" | "failed";

function idempotencyKey() {
  return globalThis.crypto?.randomUUID?.() ?? `gula-account-request-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export function RegisterPage() {
  const { t } = useTranslation();
  const { isRTL } = useLocale();
  const Arrow = isRTL ? ArrowLeft : ArrowRight;
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [status, setStatus] = useState<RequestStatus>("idle");
  const [message, setMessage] = useState("");

  const submitRequest = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setStatus("pending");
    setMessage("");
    try {
      const response = await identityLifecycleApi.submitAccountRequest(
        { display_name: displayName.trim() || undefined, email: email.trim() || undefined, phone: phone.trim() || undefined, requested_account_type: "human" },
        idempotencyKey(),
      );
      setMessage(response.message || "تم استلام الطلب للمراجعة.");
      setStatus("accepted");
    } catch (caught) {
      setMessage(classifyApiError(caught, "تعذر إرسال طلب الحساب.").message);
      setStatus("failed");
    }
  };

  return (
    <section className="mx-auto max-w-4xl overflow-hidden rounded-[1.75rem] border border-slate-200 bg-white shadow-[0_24px_70px_-40px_rgba(15,23,42,0.45)] dark:border-white/10 dark:bg-slate-950">
      <div className="border-b border-slate-200 bg-slate-50/80 p-7 dark:border-white/10 dark:bg-white/[0.03] sm:p-10">
        <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary"><ShieldCheck className="h-6 w-6" /></span>
        <p className="mt-5 text-xs font-bold uppercase tracking-[0.16em] text-primary">GULA · {t("loginPage.secureAccess")}</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">طلب إنشاء حساب</h1>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">التسجيل العام غير مفعّل. هذا النموذج يرسل طلب مراجعة فقط إلى الخادم ولا ينشئ حساباً ولا يفعّل أي صلاحية.</p>
      </div>

      <div className="p-7 sm:p-10">
        <div className="grid gap-4 md:grid-cols-2">
          <article className="rounded-2xl border border-slate-200 p-5 dark:border-white/10"><span className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary"><UserRound className="h-5 w-5" /></span><h2 className="mt-4 text-base font-bold">حساب شخصي</h2><p className="mt-2 text-sm leading-6 text-muted-foreground">طلب مواطن أو مستخدم بشري يخضع للتحقق والمراجعة قبل التفعيل.</p><p className="mt-5 flex gap-2 text-xs text-slate-600 dark:text-slate-300"><CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" /> لا يتم إصدار جلسة من هذا الطلب</p></article>
          <article className="rounded-2xl border border-slate-200 p-5 dark:border-white/10"><span className="flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-700 dark:text-cyan-300"><Building2 className="h-5 w-5" /></span><h2 className="mt-4 text-base font-bold">حساب مؤسسة</h2><p className="mt-2 text-sm leading-6 text-muted-foreground">طلبات المؤسسات والجهات الصحية لا تُنشأ من هذا النموذج؛ تمر عبر اعتماد مؤسسي منفصل بصلاحيات server-side.</p><p className="mt-5 flex gap-2 text-xs text-slate-600 dark:text-slate-300"><CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" /> لا يتم تفعيل Public Registration</p></article>
        </div>

        {status === "accepted" ? (
          <div className="mt-6 rounded-2xl border border-emerald-500/25 bg-emerald-50 p-5 text-sm leading-7 text-emerald-950 dark:bg-emerald-500/10 dark:text-emerald-100" role="status"><CheckCircle2 className="mb-2 h-5 w-5" /> تم استلام طلبك للمراجعة. الحالة الحالية: Pending Review. لا توجد جلسة أو صلاحيات قبل الاعتماد والتفعيل من الخادم.<p className="mt-2 text-xs opacity-80">{message}</p></div>
        ) : (
          <form className="mt-6 space-y-4" onSubmit={submitRequest} aria-busy={status === "pending"}>
            {status === "failed" && <div className="rounded-xl border border-destructive/20 bg-destructive/10 px-3.5 py-3 text-sm leading-6 text-destructive" role="alert">{message}</div>}
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2"><label className="text-sm font-semibold" htmlFor="request-name">الاسم المعروض</label><Input id="request-name" value={displayName} onChange={(event) => setDisplayName(event.target.value)} maxLength={200} /></div>
              <div className="space-y-2"><span className="text-sm font-semibold">نوع الطلب</span><div className="flex h-10 items-center rounded-md border border-input bg-muted/30 px-3 text-sm text-muted-foreground">طلب حساب بشري — يخضع للمراجعة</div></div>
              <div className="space-y-2"><label className="text-sm font-semibold" htmlFor="request-email"><Mail className="me-1 inline h-4 w-4" />البريد الإلكتروني</label><Input id="request-email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} /></div>
              <div className="space-y-2"><label className="text-sm font-semibold" htmlFor="request-phone"><Phone className="me-1 inline h-4 w-4" />رقم الهاتف</label><Input id="request-phone" type="tel" autoComplete="tel" value={phone} onChange={(event) => setPhone(event.target.value)} /></div>
            </div>
            <div className="flex gap-3 rounded-2xl border border-amber-500/20 bg-amber-50/70 p-4 text-sm leading-6 text-amber-950 dark:bg-amber-500/[0.07] dark:text-amber-100"><Landmark className="mt-0.5 h-5 w-5 shrink-0 text-amber-700 dark:text-amber-300" /><p>لن تُعرض نتيجة تكشف وجود حساب، ولن يتم إنشاء حساب أو إرسال token من هذه الواجهة. تتم المراجعة والتفعيل خارج هذا النموذج وبقرار خادمي.</p></div>
            <Button className="h-11 w-full" type="submit" loading={status === "pending"}>إرسال طلب للمراجعة</Button>
          </form>
        )}

        <div className="mt-7 flex flex-wrap items-center justify-between gap-4 border-t border-slate-200 pt-6 dark:border-white/10"><p className="text-xs text-muted-foreground">لديك حساب معتمد؟</p><Link className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-bold text-primary-foreground shadow-sm transition hover:bg-primary/90" to="/login">العودة إلى تسجيل الدخول <Arrow className="h-4 w-4" /></Link></div>
      </div>
    </section>
  );
}
