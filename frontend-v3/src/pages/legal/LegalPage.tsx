import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { FileText, ShieldCheck } from "lucide-react";

export type LegalDocument = "privacy" | "terms";

export function LegalPage({ document }: { document: LegalDocument }) {
  const { t } = useTranslation();
  const titleKey = document === "privacy" ? "legal.privacyTitle" : "legal.termsTitle";
  const summaryKey = document === "privacy" ? "legal.privacySummary" : "legal.termsSummary";
  const sections = document === "privacy" ? ["collection", "use", "sharing", "rights"] : ["access", "acceptableUse", "clinicalBoundary", "changes"];

  return (
    <article className="mx-auto w-full max-w-4xl rounded-[1.75rem] border border-slate-200 bg-white p-7 shadow-sm dark:border-white/10 dark:bg-slate-950 sm:p-10" aria-labelledby="legal-title">
      <header className="border-b border-slate-200 pb-7 dark:border-white/10">
        <div className="flex items-center gap-3 text-primary">
          {document === "privacy" ? <ShieldCheck className="h-6 w-6" aria-hidden="true" /> : <FileText className="h-6 w-6" aria-hidden="true" />}
          <span className="text-xs font-bold uppercase tracking-[0.16em]">GULA Platform</span>
        </div>
        <h1 id="legal-title" className="mt-4 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">{t(titleKey)}</h1>
        <p className="mt-3 leading-7 text-muted-foreground">{t(summaryKey)}</p>
        <p className="mt-4 rounded-xl border border-amber-500/30 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-950 dark:bg-amber-500/10 dark:text-amber-100">{t("legal.reviewNotice")}</p>
      </header>

      <div className="mt-8 space-y-7">
        {sections.map((section) => (
          <section key={section} aria-labelledby={`legal-${section}`}>
            <h2 id={`legal-${section}`} className="text-lg font-bold text-slate-900 dark:text-white">{t(`legal.${document}.${section}.title`)}</h2>
            <p className="mt-2 leading-7 text-muted-foreground">{t(`legal.${document}.${section}.body`)}</p>
          </section>
        ))}
      </div>

      <footer className="mt-10 flex flex-wrap gap-3 border-t border-slate-200 pt-6 text-sm dark:border-white/10">
        <Link className="rounded-xl bg-primary px-4 py-2.5 font-semibold text-primary-foreground" to="/login">{t("legal.backToLogin")}</Link>
        <Link className="rounded-xl border border-slate-300 px-4 py-2.5 font-semibold text-foreground" to={document === "privacy" ? "/terms-of-service" : "/privacy-policy"}>{t("legal.otherDocument")}</Link>
      </footer>
    </article>
  );
}
