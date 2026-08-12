import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useLocale } from "@/contexts/LocaleContext";
import { Button, Input } from "@/components/ui";
import { Activity, ArrowLeft, Eye, EyeOff, FlaskConical, LockKeyhole, Mail, ShieldCheck, Sparkles } from "lucide-react";

function errorMessage(error: unknown) {
  const detail = (error as { response?: { data?: { detail?: string | { message?: string; message_ar?: string } } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (detail?.message_ar) return detail.message_ar;
  if (detail?.message) return detail.message;
  return "فشل تسجيل الدخول. تحقق من البيانات وحاول مرة أخرى.";
}

const signals = [
  { icon: ShieldCheck, label: "هوية وصلاحيات مؤسسية", detail: "وصول مرتبط بدور المستخدم ومؤسسته" },
  { icon: Activity, label: "تشغيل سريري متصل", detail: "لوحات عمل تتصل بخدمات GULA الفعلية" },
  { icon: FlaskConical, label: "عرض تجريبي معزول", detail: "بيانات اصطناعية للمعاينة الآمنة" },
];

export function LoginPage() {
  const { login, startDemo } = useAuth();
  const { locale } = useLocale();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login({ email, password });
      navigate("/dashboard");
    } catch (err: unknown) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleDemo = async () => {
    setError("");
    setDemoLoading(true);
    try {
      await startDemo();
      navigate("/dashboard");
    } catch (err: unknown) {
      setError(errorMessage(err) || "الوضع التجريبي غير متاح حاليًا");
    } finally {
      setDemoLoading(false);
    }
  };

  return (
    <section className="grid overflow-hidden rounded-[2rem] border border-white/60 bg-white/80 shadow-[0_24px_80px_-36px_rgba(15,23,42,0.55)] backdrop-blur-xl dark:border-white/10 dark:bg-slate-950/70 lg:grid-cols-[0.92fr_1.08fr]">
      <div className="relative hidden overflow-hidden bg-slate-950 p-8 text-white lg:flex lg:flex-col lg:justify-between xl:p-10">
        <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-cyan-400/20 blur-3xl" />
        <div className="absolute -bottom-32 -left-20 h-80 w-80 rounded-full bg-blue-600/30 blur-3xl" />
        <div className="relative">
          <div className="mb-12 flex items-center gap-3">
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-300 to-blue-600 shadow-lg shadow-cyan-500/20">
              <Activity className="h-6 w-6" strokeWidth={2.5} />
            </span>
            <div className="leading-tight">
              <p className="text-lg font-bold">جولا</p>
              <p className="font-mono text-[10px] tracking-[0.32em] text-cyan-200">GULA HEALTH</p>
            </div>
          </div>
          <div className="max-w-sm">
            <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1.5 text-xs font-semibold text-cyan-100">
              <Sparkles className="h-3.5 w-3.5" /> مركز العمليات الصحية
            </p>
            <h1 className="text-4xl font-bold leading-[1.2] tracking-tight xl:text-5xl">قرار صحي أوضح، من مكان واحد.</h1>
            <p className="mt-5 text-sm leading-7 text-slate-300">مساحة عمل موحّدة للكوادر الصحية، مع وصول مؤسسي آمن ووضع معاينة منفصل للعرض والتدريب.</p>
          </div>
        </div>
        <div className="relative mt-10 space-y-3">
          {signals.map(({ icon: Icon, label, detail }) => (
            <div key={label} className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.06] p-3.5">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/10 text-cyan-200"><Icon className="h-5 w-5" /></span>
              <div>
                <p className="text-sm font-semibold">{label}</p>
                <p className="mt-0.5 text-xs text-slate-400">{detail}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="p-6 sm:p-8 xl:p-10">
        <div className="mb-8 flex items-start justify-between gap-4">
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-primary">GULA · {locale === "ar" ? "وصول آمن" : "Secure access"}</p>
            <h2 className="text-3xl font-bold tracking-tight">مرحباً بعودتك</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">سجّل الدخول إلى مساحة العمل الصحية الخاصة بك.</p>
          </div>
          <span className="hidden h-11 w-11 items-center justify-center rounded-2xl bg-primary/10 text-primary sm:flex"><LockKeyhole className="h-5 w-5" /></span>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5" aria-busy={loading}>
          {error && <div className="rounded-2xl border border-destructive/20 bg-destructive/10 p-3.5 text-sm leading-6 text-destructive" role="alert">{error}</div>}
          <div className="space-y-2">
            <label className="text-sm font-semibold" htmlFor="email">البريد الإلكتروني أو رقم الهاتف</label>
            <div className="relative">
              <Mail className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input id="email" type="text" inputMode="email" autoComplete="username" placeholder="name@example.com" value={email} onChange={(event) => setEmail(event.target.value)} className="h-12 rounded-xl pr-10" required />
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between gap-3">
              <label className="text-sm font-semibold" htmlFor="password">كلمة المرور</label>
              <span className="text-xs text-muted-foreground">محمية بجلسة آمنة</span>
            </div>
            <div className="relative">
              <LockKeyhole className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input id="password" type={showPassword ? "text" : "password"} autoComplete="current-password" placeholder="••••••••" value={password} onChange={(event) => setPassword(event.target.value)} className="h-12 rounded-xl px-10" required />
              <button type="button" className="absolute left-3 top-1/2 -translate-y-1/2 rounded-md p-1 text-muted-foreground transition hover:bg-muted hover:text-foreground" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "إخفاء كلمة المرور" : "إظهار كلمة المرور"}>
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>
          <Button type="submit" className="h-12 w-full rounded-xl text-sm font-bold shadow-lg shadow-primary/20 transition-transform active:scale-[0.98]" loading={loading}>تسجيل الدخول <ArrowLeft className="mr-2 h-4 w-4" /></Button>
        </form>

        <div className="my-6 flex items-center gap-3 text-xs text-muted-foreground"><span className="h-px flex-1 bg-border" /><span>أو</span><span className="h-px flex-1 bg-border" /></div>
        <button type="button" className="group flex w-full items-center justify-center gap-2 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm font-bold text-amber-800 transition hover:-translate-y-0.5 hover:bg-amber-500/15 disabled:cursor-not-allowed disabled:opacity-60 dark:text-amber-200" onClick={handleDemo} disabled={demoLoading || loading}>
          <ShieldCheck className="h-4 w-4 transition-transform group-hover:scale-110" />
          {demoLoading ? "جاري فتح العرض التجريبي..." : "استكشف المنصة بالوضع التجريبي"}
        </button>
        <p className="mt-3 text-center text-xs leading-5 text-muted-foreground">بيانات اصطناعية معزولة بالكامل، ولا تمنح وصولاً إلى أي بيانات حقيقية.</p>
        <p className="mt-7 text-center text-sm text-muted-foreground">ليس لديك حساب؟ <a className="font-bold text-primary transition hover:underline" href="/register">إنشاء حساب جديد</a></p>
      </div>
    </section>
  );
}
