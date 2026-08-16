import { useMemo } from "react";
import { Building2, CheckCircle2, Clock3, ShieldAlert, XCircle } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { Badge, Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { LoadingSpinner } from "@/components/shared/PageComponents";

const defaultStatusMeta = { label: "غير معروفة", icon: ShieldAlert, className: "text-slate-600 dark:text-slate-300" };
const statusMeta: Record<string, { label: string; icon: typeof CheckCircle2; className: string }> = {
  active: { label: "نشطة", icon: CheckCircle2, className: "text-emerald-700 dark:text-emerald-300" },
  pending: { label: "قيد المراجعة", icon: Clock3, className: "text-amber-700 dark:text-amber-300" },
  suspended: { label: "موقوفة", icon: ShieldAlert, className: "text-rose-700 dark:text-rose-300" },
  expired: { label: "منتهية", icon: XCircle, className: "text-slate-600 dark:text-slate-300" },
  revoked: { label: "ملغاة", icon: XCircle, className: "text-slate-600 dark:text-slate-300" },
};

export function MembershipsPage() {
  const { memberships, isLoading, refreshMemberships, error } = useAuth();
  const grouped = useMemo(() => memberships.reduce<Record<string, typeof memberships>>((acc, membership) => {
    const key = membership.status.toLowerCase();
    acc[key] = [...(acc[key] ?? []), membership];
    return acc;
  }, {}), [memberships]);

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <header className="rounded-[1.5rem] border border-teal-100 bg-white p-6 shadow-sm dark:border-teal-900/40 dark:bg-slate-900/70">
        <p className="text-xs font-bold uppercase tracking-[0.15em] text-teal-700 dark:text-teal-300">GULA · Identity Context</p>
        <h1 className="mt-2 text-2xl font-bold tracking-tight">العضويات والسياقات</h1>
        <p className="mt-2 max-w-3xl text-sm leading-7 text-muted-foreground">هذه القائمة انعكاس من الخادم للعضويات المسموح بها. لا تمنح الصفحة صلاحية ولا تسمح بتعديل العضويات من الواجهة.</p>
      </header>
      {error && <div className="rounded-2xl border border-amber-500/25 bg-amber-50 p-4 text-sm text-amber-950 dark:bg-amber-500/10 dark:text-amber-100" role="alert">{error.message}</div>}
      {memberships.length === 0 ? (
        <Card><CardContent className="p-8 text-center text-sm text-muted-foreground">لا توجد عضويات منعكسة من الخادم لهذا الحساب.</CardContent></Card>
      ) : (
        <div className="space-y-5">
          {Object.entries(grouped).map(([status, items]) => {
            const meta = statusMeta[status] ?? defaultStatusMeta;
            const Icon = meta.icon;
            return (
              <section key={status} aria-labelledby={`membership-${status}`}>
                <div className="mb-3 flex items-center gap-2"><Icon className={`h-5 w-5 ${meta.className}`} /><h2 id={`membership-${status}`} className="text-lg font-bold">{meta.label}</h2><Badge variant="secondary">{items.length}</Badge></div>
                <div className="grid gap-4 md:grid-cols-2">
                  {items.map((membership) => (
                    <Card key={membership.uuid || membership.id} className="border-slate-200 dark:border-white/10"><CardHeader className="border-b border-slate-100 p-5 dark:border-white/10"><CardTitle className="flex items-center gap-2 text-base"><Building2 className="h-4 w-4 text-teal-600" /> {membership.relationship_type || "عضوية"}</CardTitle></CardHeader><CardContent className="grid gap-3 p-5 text-sm sm:grid-cols-2"><div><p className="text-xs text-muted-foreground">Organization</p><p className="mt-1 break-all font-semibold">{membership.organization_id}</p></div><div><p className="text-xs text-muted-foreground">Facility</p><p className="mt-1 break-all font-semibold">{membership.facility_id || "غير محددة"}</p></div><div><p className="text-xs text-muted-foreground">Workspace</p><p className="mt-1 break-all font-semibold">{membership.workspace_id || "غير محددة"}</p></div><div><p className="text-xs text-muted-foreground">Role / Entitlement</p><p className="mt-1 font-semibold">{membership.scope_type} · {membership.source}</p></div><div><p className="text-xs text-muted-foreground">الحالة</p><p className={`mt-1 font-semibold ${meta.className}`}>{meta.label}</p></div><div><p className="text-xs text-muted-foreground">تنتهي في</p><p className="mt-1 font-semibold">{membership.expires_at ? new Date(membership.expires_at).toLocaleString("ar-IQ") : "غير محدد"}</p></div></CardContent></Card>
                  ))}
                </div>
              </section>
            );
          })}
        </div>
      )}
      <button type="button" className="text-sm font-semibold text-teal-700 underline dark:text-teal-300" onClick={() => void refreshMemberships(true)}>تحديث العضويات من الخادم</button>
    </div>
  );
}
