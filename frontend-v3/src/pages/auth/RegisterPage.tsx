import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ArrowLeft, ArrowRight, Building2, CheckCircle2, Clock3, KeyRound, Landmark, ShieldCheck, UserRound } from "lucide-react";
import { useLocale } from "@/contexts/LocaleContext";
import { apiClient } from "@/api/client";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

const genericError = "تعذر إكمال العملية حالياً. تحقق من البيانات أو أعد المحاولة لاحقاً.";

type PortalStage = "form" | "verification" | "pending_approval" | "activation" | "completed";

export function RegisterPage() {
  const { t } = useTranslation();
  const { isRTL } = useLocale();
  const Arrow = isRTL ? ArrowLeft : ArrowRight;
  const [stage, setStage] = useState<PortalStage>("form");
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [requestId, setRequestId] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const [activationToken, setActivationToken] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const submitRequest = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    if (!email.trim() && !phone.trim()) {
      setError("أدخل البريد الإلكتروني أو رقم الهاتف على الأقل.");
      return;
    }
    try {
      const key = typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
        ? crypto.randomUUID()
        : `request-${Date.now()}-${Math.random().toString(36).slice(2)}`;
      const result = await apiClient.submitAccountRequest(
        {
          display_name: displayName.trim() || undefined,
          email: email.trim() || undefined,
          phone: phone.trim() || undefined,
          requested_account_type: "human",
        },
        key,
      );
      setRequestId(result.request_id);
      setStage(result.request_id ? "verification" : "pending_approval");
    } catch {
      setError(genericError);
    }
  };

  const startVerification = async () => {
    if (!requestId) return;
    setError(null);
    try {
      await apiClient.startAccountRequestVerification(requestId);
      setStage("verification");
    } catch {
      setError("لم يكتمل إرسال رمز التحقق. سيبقى الطلب قيد الانتظار دون إنشاء حساب.");
    }
  };

  const confirmVerification = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!requestId) return;
    setError(null);
    try {
      await apiClient.confirmAccountRequestVerification(requestId, code);
      setStage("pending_approval");
    } catch {
      setError("رمز التحقق غير صالح أو منتهي. لا تتم إعادة استخدام الرمز بعد نجاحه.");
    }
  };

  const activateAccount = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!requestId) return;
    setError(null);
    try {
      await apiClient.activateAccountRequest(requestId, activationToken, password);
      setStage("completed");
    } catch {
      setError("لا يمكن تفعيل الحساب قبل اعتماد الطلب وإثبات الهوية عبر المسار الرسمي.");
    }
  };

  return (
    <section className="mx-auto max-w-4xl overflow-hidden rounded-[1.75rem] border border-slate-200 bg-white shadow-[0_24px_70px_-40px_rgba(15,23,42,0.45)] dark:border-white/10 dark:bg-slate-950">
      <div className="border-b border-slate-200 bg-slate-50/80 p-7 dark:border-white/10 dark:bg-white/[0.03] sm:p-10">
        <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary"><ShieldCheck className="h-6 w-6" aria-hidden="true" /></span>
        <p className="mt-5 text-xs font-bold uppercase tracking-[0.16em] text-primary">GULA · {t("loginPage.secureAccess")}</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">طلب إنشاء حساب مؤسسي أو مواطن</h1>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">هذا نموذج طلب يخضع للمراجعة والتحقق والاعتماد. لا ينشئ حساباً أو صلاحية مباشرة، ولا يفعّل التسجيل الذاتي العام.</p>
      </div>

      <div className="p-7 sm:p-10">
        <div className="grid gap-4 md:grid-cols-2">
          <article className="rounded-2xl border border-slate-200 p-5 dark:border-white/10">
            <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary"><UserRound className="h-5 w-5" aria-hidden="true" /></span>
            <h2 className="mt-4 text-base font-bold text-slate-900 dark:text-white">مسار المواطن</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">يتم التحقق من وسيلة الاتصال ثم تُراجع الهوية عبر الموفر الوطني المعتمد قبل التفعيل.</p>
            <ul className="mt-5 space-y-2.5 text-xs leading-5 text-slate-600 dark:text-slate-300">
              <li className="flex gap-2"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-600" aria-hidden="true" />لا يتم تجاوز التحقق الرسمي.</li>
              <li className="flex gap-2"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-600" aria-hidden="true" />الصلاحيات تُمنح منفصلة عبر نظام Authorization.</li>
            </ul>
          </article>
          <article className="rounded-2xl border border-slate-200 p-5 dark:border-white/10">
            <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-700 dark:text-cyan-300"><Building2 className="h-5 w-5" aria-hidden="true" /></span>
            <h2 className="mt-4 text-base font-bold text-slate-900 dark:text-white">مسار الموظف أو المؤسسة</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">تحتاج الحسابات الوظيفية إلى مراجعة الجهة والاعتماد التنظيمي قبل إضافة أي Membership أو Workspace.</p>
            <ul className="mt-5 space-y-2.5 text-xs leading-5 text-slate-600 dark:text-slate-300">
              <li className="flex gap-2"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-600" aria-hidden="true" />لا يمنح الاعتماد دوراً تلقائياً.</li>
              <li className="flex gap-2"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-600" aria-hidden="true" />كل تغيير يسجل في سجل التدقيق.</li>
            </ul>
          </article>
        </div>

        <div className="mt-5 flex gap-3 rounded-2xl border border-amber-500/20 bg-amber-50/70 p-4 text-sm leading-6 text-amber-950 dark:bg-amber-500/[0.07] dark:text-amber-100">
          <Landmark className="mt-0.5 h-5 w-5 shrink-0 text-amber-700 dark:text-amber-300" aria-hidden="true" />
          <p>التسجيل الذاتي العام لا يزال مغلقاً. هذا المسار يرسل Account Request فقط، ويظل الحساب Pending حتى اكتمال المراجعة والتحقق والاعتماد.</p>
        </div>

        {stage === "form" && (
          <form className="mt-8 space-y-5 rounded-2xl border border-slate-200 p-5 dark:border-white/10" onSubmit={submitRequest} noValidate>
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">إرسال طلب مراجعة</h2>
              <p className="mt-1 text-sm text-muted-foreground">أدخل وسيلة اتصال واحدة على الأقل. لن تظهر بيانات الاتصال في رسائل الحالة العامة.</p>
            </div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-200" htmlFor="account-display-name">الاسم المعروض<span className="text-muted-foreground"> (اختياري)</span></label>
            <Input id="account-display-name" value={displayName} onChange={(event) => setDisplayName(event.target.value)} autoComplete="name" />
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200" htmlFor="account-email">البريد الإلكتروني</label>
                <Input id="account-email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" inputMode="email" />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200" htmlFor="account-phone">رقم الهاتف</label>
                <Input id="account-phone" type="tel" value={phone} onChange={(event) => setPhone(event.target.value)} autoComplete="tel" inputMode="tel" />
              </div>
            </div>
            {error && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-800 dark:bg-red-950/30 dark:text-red-200" role="alert">{error}</p>}
            <Button type="submit">إرسال الطلب للمراجعة</Button>
          </form>
        )}

        {stage === "verification" && (
          <div className="mt-8 space-y-5 rounded-2xl border border-slate-200 p-5 dark:border-white/10">
            <div className="flex items-start gap-3"><Clock3 className="mt-1 h-5 w-5 text-primary" aria-hidden="true" /><div><h2 className="text-lg font-bold text-slate-900 dark:text-white">التحقق من وسيلة الاتصال</h2><p className="mt-1 text-sm text-muted-foreground">رقم الطلب محفوظ. اطلب الرمز ثم أدخله مرة واحدة خلال مدة صلاحيته.</p></div></div>
            <Button type="button" variant="outline" onClick={startVerification}>إرسال رمز تحقق</Button>
            <form className="space-y-3" onSubmit={confirmVerification} noValidate>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-200" htmlFor="verification-code">رمز التحقق المكوّن من 6 أرقام</label>
              <Input id="verification-code" value={code} onChange={(event) => setCode(event.target.value.replace(/\D/g, "").slice(0, 6))} inputMode="numeric" autoComplete="one-time-code" maxLength={6} />
              {error && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-800 dark:bg-red-950/30 dark:text-red-200" role="alert">{error}</p>}
              <Button type="submit" disabled={code.length !== 6}>تأكيد الرمز</Button>
            </form>
          </div>
        )}

        {stage === "pending_approval" && (
          <div className="mt-8 space-y-4 rounded-2xl border border-amber-200 bg-amber-50/70 p-5 dark:border-amber-500/20 dark:bg-amber-500/[0.07]">
            <div className="flex items-start gap-3"><Clock3 className="mt-1 h-5 w-5 text-amber-700 dark:text-amber-300" aria-hidden="true" /><div><h2 className="text-lg font-bold text-amber-950 dark:text-amber-100">الطلب بانتظار الاعتماد</h2><p className="mt-1 text-sm leading-6 text-amber-900/80 dark:text-amber-100/80">تم قبول التحقق الأولي. لا يمكن تسجيل الدخول أو استخدام أي Workspace حتى يعتمد الطلب ويثبت مسار الهوية الرسمي.</p></div></div>
            <Button type="button" variant="outline" onClick={() => setStage("activation")}><KeyRound aria-hidden="true" /> لدي رمز تفعيل</Button>
            {error && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-800 dark:bg-red-950/30 dark:text-red-200" role="alert">{error}</p>}
          </div>
        )}

        {stage === "activation" && (
          <form className="mt-8 space-y-4 rounded-2xl border border-slate-200 p-5 dark:border-white/10" onSubmit={activateAccount} noValidate>
            <div className="flex items-start gap-3"><KeyRound className="mt-1 h-5 w-5 text-primary" aria-hidden="true" /><div><h2 className="text-lg font-bold text-slate-900 dark:text-white">تفعيل الحساب المعتمد</h2><p className="mt-1 text-sm text-muted-foreground">لن ينجح التفعيل إلا بعد اعتماد الطلب وإثبات الهوية. الرمز أحادي الاستخدام.</p></div></div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-200" htmlFor="activation-token">رمز التفعيل</label>
            <Input id="activation-token" value={activationToken} onChange={(event) => setActivationToken(event.target.value)} autoComplete="one-time-code" />
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-200" htmlFor="activation-password">كلمة مرور جديدة</label>
            <Input id="activation-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="new-password" minLength={12} />
            {error && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-800 dark:bg-red-950/30 dark:text-red-200" role="alert">{error}</p>}
            <Button type="submit" disabled={!activationToken || password.length < 12}>تفعيل الحساب</Button>
          </form>
        )}

        {stage === "completed" && (
          <div className="mt-8 rounded-2xl border border-emerald-200 bg-emerald-50 p-5 text-emerald-900 dark:border-emerald-500/20 dark:bg-emerald-500/[0.08] dark:text-emerald-100" role="status">
            <div className="flex items-start gap-3"><CheckCircle2 className="mt-1 h-5 w-5" aria-hidden="true" /><div><h2 className="text-lg font-bold">تم تفعيل الحساب</h2><p className="mt-1 text-sm">يمكنك العودة إلى صفحة الدخول. ستبقى الصلاحيات خاضعة للـMembership وRole وPolicy.</p></div></div>
          </div>
        )}

        <div className="mt-7 flex flex-wrap items-center justify-between gap-4 border-t border-slate-200 pt-6 dark:border-white/10">
          <p className="text-xs text-muted-foreground">{t("onboarding.existingStaff")}</p>
          <Link className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-bold text-primary-foreground shadow-sm transition hover:bg-primary/90 gula-focus-ring" to="/login">{t("loginPage.backToChoice")} <Arrow className="h-4 w-4" aria-hidden="true" /></Link>
        </div>
      </div>
    </section>
  );
}
