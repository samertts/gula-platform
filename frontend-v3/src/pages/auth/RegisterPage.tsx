import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ArrowLeft, ArrowRight, Building2, CheckCircle2, Landmark, ShieldCheck, UserRound } from "lucide-react";
import { useLocale } from "@/contexts/LocaleContext";

export function RegisterPage() {
  const { t } = useTranslation();
  const { isRTL } = useLocale();
  const Arrow = isRTL ? ArrowLeft : ArrowRight;

  return (
    <section className="mx-auto max-w-3xl overflow-hidden rounded-[1.75rem] border border-slate-200 bg-white shadow-[0_24px_70px_-40px_rgba(15,23,42,0.45)] dark:border-white/10 dark:bg-slate-950">
      <div className="border-b border-slate-200 bg-slate-50/80 p-7 dark:border-white/10 dark:bg-white/[0.03] sm:p-10">
        <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary"><ShieldCheck className="h-6 w-6" /></span>
        <p className="mt-5 text-xs font-bold uppercase tracking-[0.16em] text-primary">GULA · {t("loginPage.secureAccess")}</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">{t("loginPage.requestAccount")}</h1>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">{t("loginPage.accountProcedure")}</p>
      </div>

      <div className="p-7 sm:p-10">
        <div className="grid gap-4 md:grid-cols-2">
          <article className="rounded-2xl border border-slate-200 p-5 dark:border-white/10">
            <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary"><UserRound className="h-5 w-5" /></span>
            <h2 className="mt-4 text-base font-bold text-slate-900 dark:text-white">{t("loginPage.citizenTitle")}</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">{t("loginPage.citizenDescription")}</p>
            <ul className="mt-5 space-y-2.5 text-xs leading-5 text-slate-600 dark:text-slate-300">
              <li className="flex gap-2"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-600" />{t("onboarding.citizenVerify")}</li>
              <li className="flex gap-2"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-600" />{t("onboarding.citizenAccess")}</li>
            </ul>
          </article>
          <article className="rounded-2xl border border-slate-200 p-5 dark:border-white/10">
            <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-700 dark:text-cyan-300"><Building2 className="h-5 w-5" /></span>
            <h2 className="mt-4 text-base font-bold text-slate-900 dark:text-white">{t("loginPage.institutionTitle")}</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">{t("loginPage.institutionDescription")}</p>
            <ul className="mt-5 space-y-2.5 text-xs leading-5 text-slate-600 dark:text-slate-300">
              <li className="flex gap-2"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-600" />{t("onboarding.institutionDocuments")}</li>
              <li className="flex gap-2"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-600" />{t("onboarding.institutionAccess")}</li>
            </ul>
          </article>
        </div>

        <div className="mt-5 flex gap-3 rounded-2xl border border-amber-500/20 bg-amber-50/70 p-4 text-sm leading-6 text-amber-950 dark:bg-amber-500/[0.07] dark:text-amber-100">
          <Landmark className="mt-0.5 h-5 w-5 shrink-0 text-amber-700 dark:text-amber-300" />
          <p>{t("onboarding.selfServiceUnavailable")}</p>
        </div>

        <div className="mt-7 flex flex-wrap items-center justify-between gap-4 border-t border-slate-200 pt-6 dark:border-white/10">
          <p className="text-xs text-muted-foreground">{t("onboarding.existingStaff")}</p>
          <Link className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-bold text-primary-foreground shadow-sm transition hover:bg-primary/90" to="/login">{t("loginPage.backToChoice")} <Arrow className="h-4 w-4" /></Link>
        </div>
      </div>
    </section>
  );
}
