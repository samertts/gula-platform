import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  Activity,
  ArrowLeft,
  ArrowRight,
  Building2,
  CheckCircle2,
  ChevronDown,
  Eye,
  EyeOff,
  FlaskConical,
  Globe2,
  LockKeyhole,
  Mail,
  ShieldCheck,
  Stethoscope,
  UserRound,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useLocale } from "@/contexts/LocaleContext";
import { localeOptions, type Locale } from "@/i18n/locales";
import { Button, Input } from "@/components/ui";

type AccessPath = "citizen" | "institution";

function errorMessage(error: unknown, fallback: string) {
  const detail = (error as { response?: { data?: { detail?: string | { message?: string; message_ar?: string } } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (detail?.message_ar) return detail.message_ar;
  if (detail?.message) return detail.message;
  return fallback;
}

export function LoginPage() {
  const { login, startDemo } = useAuth();
  const { locale, setLocale, isRTL } = useLocale();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [accessPath, setAccessPath] = useState<AccessPath>("citizen");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [error, setError] = useState("");

  const copy = {
    citizen: {
      title: t("loginPage.citizenTitle"),
      description: t("loginPage.citizenDescription"),
      action: t("loginPage.loginCitizen"),
      icon: UserRound,
    },
    institution: {
      title: t("loginPage.institutionTitle"),
      description: t("loginPage.institutionDescription"),
      action: t("loginPage.loginInstitution"),
      icon: Building2,
    },
  } as const;

  const activePath = copy[accessPath];
  const ActiveIcon = activePath.icon;
  const Arrow = isRTL ? ArrowLeft : ArrowRight;

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login({ email: email.trim(), password });
      navigate("/dashboard");
    } catch (err: unknown) {
      setError(errorMessage(err, t("auth.invalidCredentials")));
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
      setError(errorMessage(err, t("common.error")));
    } finally {
      setDemoLoading(false);
    }
  };

  return (
    <section className="overflow-hidden rounded-[1.75rem] border border-slate-200/80 bg-white shadow-[0_24px_70px_-40px_rgba(15,23,42,0.45)] dark:border-white/10 dark:bg-slate-950">
      <div className="grid lg:grid-cols-[0.92fr_1.08fr]">
        <aside className="relative overflow-hidden bg-[#10344a] p-7 text-white sm:p-10 lg:min-h-[650px]">
          <div className="absolute inset-0 opacity-40" aria-hidden="true" style={{ backgroundImage: "radial-gradient(circle at 12% 10%, rgba(104, 211, 214, 0.28), transparent 28%), radial-gradient(circle at 85% 85%, rgba(38, 132, 180, 0.36), transparent 34%)" }} />
          <div className="absolute -left-24 bottom-4 h-64 w-64 rounded-full border border-white/10" aria-hidden="true" />
          <div className="absolute -right-16 top-28 h-40 w-40 rounded-full border border-cyan-100/20" aria-hidden="true" />

          <div className="relative flex h-full flex-col">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/12 shadow-lg shadow-slate-950/20 ring-1 ring-white/15">
                  <Activity className="h-5 w-5 text-cyan-100" strokeWidth={2.4} />
                </span>
                <div className="leading-tight">
                  <p className="text-lg font-extrabold tracking-tight">GULA</p>
                  <p className="mt-0.5 text-[10px] font-semibold uppercase tracking-[0.18em] text-cyan-100/75">Health platform</p>
                </div>
              </div>
              <label className="relative flex items-center gap-2 rounded-xl border border-white/15 bg-white/[0.08] px-2.5 py-2 text-xs font-semibold text-white/90 backdrop-blur-sm">
                <Globe2 className="h-3.5 w-3.5 text-cyan-100" aria-hidden="true" />
                <span className="sr-only">{t("common.language")}</span>
                <select
                  value={locale}
                  onChange={(event) => setLocale(event.target.value as Locale)}
                  className="appearance-none bg-transparent pe-5 text-xs font-semibold outline-none"
                  aria-label={t("common.language")}
                >
                  {localeOptions.map((option) => <option className="text-slate-900" key={option.code} value={option.code}>{option.nativeName}</option>)}
                </select>
                <ChevronDown className="pointer-events-none absolute end-2.5 h-3.5 w-3.5" aria-hidden="true" />
              </label>
            </div>

            <div className="mt-14 max-w-md lg:mt-20">
              <p className="inline-flex items-center gap-2 rounded-full border border-cyan-100/15 bg-cyan-100/10 px-3 py-1.5 text-xs font-semibold text-cyan-50">
                <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" /> {t("loginPage.secureAccess")}
              </p>
              <h1 className="mt-5 text-3xl font-bold leading-[1.28] tracking-tight sm:text-4xl">{t("loginPage.welcome")}</h1>
              <p className="mt-4 max-w-sm text-sm leading-7 text-slate-200/85">{t("loginPage.headline")}</p>
            </div>

            <div className="mt-12 space-y-3 lg:mt-auto">
              <div className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/[0.07] p-4 backdrop-blur-sm">
                <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-cyan-200/15 text-cyan-100"><Stethoscope className="h-4.5 w-4.5" /></span>
                <div>
                  <p className="text-sm font-bold">{t("loginPage.citizenTitle")}</p>
                  <p className="mt-1 text-xs leading-5 text-slate-200/75">{t("loginPage.citizenDescription")}</p>
                </div>
              </div>
              <div className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/[0.07] p-4 backdrop-blur-sm">
                <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-cyan-200/15"><Building2 className="h-4.5 w-4.5" /></span>
                <div>
                  <p className="text-sm font-bold">{t("loginPage.institutionTitle")}</p>
                  <p className="mt-1 text-xs leading-5 text-slate-200/75">{t("loginPage.institutionDescription")}</p>
                </div>
              </div>
            </div>
          </div>
        </aside>

        <div className="p-6 sm:p-9 lg:p-12">
          <div className="mx-auto max-w-md">
            <div className="mb-7">
              <p className="text-xs font-bold uppercase tracking-[0.15em] text-primary">GULA · {t("loginPage.secureAccess")}</p>
              <h2 className="mt-3 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">{t("loginPage.chooseAccess")}</h2>
            </div>

            <div className="space-y-3" role="group" aria-label={t("loginPage.chooseAccess")}>
              {(Object.keys(copy) as AccessPath[]).map((path) => {
                const option = copy[path];
                const Icon = option.icon;
                const active = accessPath === path;
                return (
                  <button
                    type="button"
                    key={path}
                    onClick={() => { setAccessPath(path); setError(""); }}
                    aria-pressed={active}
                    className={`group flex w-full items-start gap-4 rounded-2xl border p-4 text-start transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 ${active ? "border-primary/45 bg-primary/[0.06] shadow-sm" : "border-slate-200 bg-white hover:border-primary/30 hover:bg-slate-50 dark:border-white/10 dark:bg-white/[0.02] dark:hover:bg-white/[0.05]"}`}
                  >
                    <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl transition-colors ${active ? "bg-primary text-primary-foreground" : "bg-slate-100 text-slate-600 dark:bg-white/10 dark:text-slate-200"}`}><Icon className="h-5 w-5" /></span>
                    <span className="min-w-0 flex-1">
                      <span className="flex items-center justify-between gap-3 text-sm font-bold text-slate-900 dark:text-white">
                        {option.title}
                        {active && <CheckCircle2 className="h-4.5 w-4.5 shrink-0 text-primary" aria-label="Selected" />}
                      </span>
                      <span className="mt-1 block text-xs leading-5 text-muted-foreground">{option.description}</span>
                    </span>
                  </button>
                );
              })}
            </div>

            <div className="my-7 h-px bg-slate-200 dark:bg-white/10" />

            <div className="mb-5 flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary"><ActiveIcon className="h-5 w-5" /></span>
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">{activePath.action}</h3>
                <p className="mt-0.5 text-xs text-muted-foreground">{accessPath === "institution" ? t("loginPage.institutionDescription") : t("loginPage.citizenDescription")}</p>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4" aria-busy={loading}>
              {error && <div className="rounded-xl border border-destructive/20 bg-destructive/10 px-3.5 py-3 text-sm leading-6 text-destructive" role="alert">{error}</div>}
              <div className="space-y-2">
                <label className="text-sm font-semibold" htmlFor="email">{t("loginPage.emailOrPhone")}</label>
                <div className="relative">
                  <Mail className="pointer-events-none absolute end-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input id="email" type="text" inputMode="email" autoComplete="username" placeholder={accessPath === "citizen" ? "+964 7XX XXX XXXX" : "name@institution.iq"} value={email} onChange={(event) => setEmail(event.target.value)} className="h-12 rounded-xl pe-10" required />
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between gap-3"><label className="text-sm font-semibold" htmlFor="password">{t("auth.password")}</label><span className="text-xs text-muted-foreground">{t("loginPage.secureAccess")}</span></div>
                <div className="relative">
                  <LockKeyhole className="pointer-events-none absolute end-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input id="password" type={showPassword ? "text" : "password"} autoComplete="current-password" placeholder="••••••••" value={password} onChange={(event) => setPassword(event.target.value)} className="h-12 rounded-xl px-10" required />
                  <button type="button" className="absolute start-3 top-1/2 -translate-y-1/2 rounded-md p-1 text-muted-foreground transition hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "Hide password" : "Show password"}>
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <Button type="submit" className="h-12 w-full rounded-xl text-sm font-bold shadow-lg shadow-primary/15 transition-transform active:scale-[0.99]" loading={loading}>
                {activePath.action} <Arrow className="ms-2 h-4 w-4" />
              </Button>
            </form>

            <div className="my-6 flex items-center gap-3 text-xs text-muted-foreground"><span className="h-px flex-1 bg-border" /><span>GULA</span><span className="h-px flex-1 bg-border" /></div>

            <section className="rounded-2xl border border-amber-500/20 bg-amber-50/70 p-4 dark:bg-amber-500/[0.07]" aria-labelledby="demo-title">
              <div className="flex gap-3">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-500/15 text-amber-700 dark:text-amber-300"><FlaskConical className="h-5 w-5" /></span>
                <div>
                  <h3 id="demo-title" className="text-sm font-bold text-amber-950 dark:text-amber-100">{t("loginPage.demoTitle")}</h3>
                  <p className="mt-1 text-xs leading-5 text-amber-900/75 dark:text-amber-100/70">{t("loginPage.demoDescription")}</p>
                </div>
              </div>
              <button type="button" className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl border border-amber-500/25 bg-white px-4 py-2.5 text-sm font-bold text-amber-900 shadow-sm transition hover:-translate-y-0.5 hover:border-amber-500/45 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-slate-950/40 dark:text-amber-100" onClick={handleDemo} disabled={demoLoading || loading}>
                <ShieldCheck className="h-4 w-4" /> {demoLoading ? t("loginPage.demoLoading") : t("loginPage.startDemo")}
              </button>
            </section>

            <div className="mt-6 border-t border-slate-200 pt-5 text-center dark:border-white/10">
              <p className="text-xs leading-5 text-muted-foreground">{t("loginPage.accountProcedure")}</p>
              <Link className="mt-2 inline-flex items-center gap-1 text-sm font-bold text-primary transition hover:underline" to="/register">{t("loginPage.requestAccount")} <Arrow className="h-3.5 w-3.5" /></Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
