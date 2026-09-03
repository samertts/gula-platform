import { ArrowLeft, FileCode2, LockKeyhole } from "lucide-react";
import { Link } from "react-router-dom";
import { ClinicalStatePanel } from "@/components/clinical";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

type DomainRouteContractGatePageProps = {
  title: string;
  description: string;
  contract: string;
};

export default function DomainRouteContractGatePage({ title, description, contract }: DomainRouteContractGatePageProps) {
  return (
    <div className="mx-auto max-w-4xl space-y-5" dir="rtl">
      <Card className="gula-interactive-surface overflow-hidden">
        <CardHeader className="bg-gradient-to-l from-slate-950 to-[#0f766e] text-white">
          <div className="flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/10"><FileCode2 className="h-5 w-5" /></span>
            <div><p className="gula-section-label text-teal-200">Domain route</p><CardTitle className="mt-1 text-2xl">{title}</CardTitle></div>
          </div>
          <p className="max-w-2xl text-sm leading-7 text-slate-200">{description}</p>
        </CardHeader>
        <CardContent className="space-y-4 p-6">
          <ClinicalStatePanel state="maintenance" title="العقد غير مربوط بالواجهة بعد" description="لا نعرض بيانات أو نموذج كتابة أو fallback غير موثق. سيظهر هذا المسار عند اكتمال العقد والتفويض والاختبارات المطلوبة." />
          <div className="grid gap-3 sm:grid-cols-3"><Requirement label="Contract" value={contract} /><Requirement label="Authorization" value="RBAC + context" /><Requirement label="Audit" value="Required before write" /></div>
          <div className="flex flex-wrap items-center gap-3 rounded-xl border border-amber-200 bg-amber-50/60 p-4 text-sm leading-6 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-100"><LockKeyhole className="h-4 w-4 shrink-0" />هذا المسار لا يقرر الصلاحية ولا ينشئ بيانات سريرية محلياً.</div>
          <Link className="gula-focus-ring inline-flex min-h-11 items-center rounded-xl border border-border bg-background px-4 text-sm font-semibold text-foreground transition hover:bg-muted" to="/screen-by-screen">مشاهدة شاشة المعاينة <ArrowLeft className="ms-2 h-4 w-4" /></Link>
        </CardContent>
      </Card>
    </div>
  );
}

function Requirement({ label, value }: { label: string; value: string }) {
  return <div className="rounded-xl border bg-muted/20 p-4"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 text-sm font-bold">{value}</p></div>;
}
