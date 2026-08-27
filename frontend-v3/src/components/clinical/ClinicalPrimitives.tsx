import {
  AlertTriangle,
  CheckCircle2,
  CircleAlert,
  Clock3,
  CloudOff,
  GitCompareArrows,
  Inbox,
  Info,
  LockKeyhole,
  RefreshCw,
  ShieldAlert,
  Wrench,
  type LucideIcon,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { cn } from "@/lib/utils";

export type ClinicalSurfaceState =
  | "loading"
  | "loaded"
  | "empty"
  | "partial"
  | "offline"
  | "syncing"
  | "error"
  | "unauthorized"
  | "forbidden"
  | "expired"
  | "conflict"
  | "maintenance";

type StateMeta = {
  label: string;
  description: string;
  icon: LucideIcon;
  tone: string;
  role: "status" | "alert";
};

const STATE_META: Record<ClinicalSurfaceState, StateMeta> = {
  loading: { label: "جارٍ التحميل", description: "نجهز المعلومات المسموح بها لهذا السياق.", icon: RefreshCw, tone: "text-sky-700 dark:text-sky-300", role: "status" },
  loaded: { label: "محمّل", description: "المعلومات معروضة ضمن السياق الحالي.", icon: CheckCircle2, tone: "text-emerald-700 dark:text-emerald-300", role: "status" },
  empty: { label: "لا توجد بيانات", description: "لا توجد عناصر متاحة ضمن النطاق الحالي.", icon: Inbox, tone: "text-slate-600 dark:text-slate-300", role: "status" },
  partial: { label: "عرض جزئي", description: "بعض المعلومات غير متاحة أو ما تزال قيد المعالجة.", icon: Info, tone: "text-amber-700 dark:text-amber-300", role: "status" },
  offline: { label: "دون اتصال", description: "الاتصال غير متاح؛ لا نعرض البيانات على أنها محدثة.", icon: CloudOff, tone: "text-amber-700 dark:text-amber-300", role: "status" },
  syncing: { label: "جارٍ التزامن", description: "تتم مزامنة التغييرات وفق سياسة النظام.", icon: RefreshCw, tone: "text-sky-700 dark:text-sky-300", role: "status" },
  error: { label: "تعذر التحميل", description: "تعذر إكمال الطلب بأمان حاليًا.", icon: CircleAlert, tone: "text-rose-700 dark:text-rose-300", role: "alert" },
  unauthorized: { label: "تسجيل الدخول مطلوب", description: "انتهت أو لم تبدأ جلسة الدخول الحالية.", icon: LockKeyhole, tone: "text-slate-700 dark:text-slate-200", role: "alert" },
  forbidden: { label: "الوصول محجوب", description: "لا يعيد الخادم صلاحية لهذا الإجراء أو السياق.", icon: ShieldAlert, tone: "text-amber-800 dark:text-amber-200", role: "alert" },
  expired: { label: "انتهت الصلاحية", description: "يجب إعادة تحميل السياق قبل المتابعة.", icon: Clock3, tone: "text-amber-800 dark:text-amber-200", role: "alert" },
  conflict: { label: "تعارض يحتاج مراجعة", description: "لم نستخدم آخر كتابة تلقائياً؛ يجب حل التعارض صراحة.", icon: GitCompareArrows, tone: "text-rose-800 dark:text-rose-200", role: "alert" },
  maintenance: { label: "صيانة جارية", description: "هذه capability غير متاحة مؤقتًا ولا يوجد fallback سريري غير موثق.", icon: Wrench, tone: "text-slate-700 dark:text-slate-200", role: "status" },
};

export interface ClinicalStatePanelProps {
  state: ClinicalSurfaceState;
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export function ClinicalStatePanel({ state, title, description, actionLabel, onAction, className }: ClinicalStatePanelProps) {
  const meta = STATE_META[state];
  const Icon = meta.icon;
  const isLoading = state === "loading" || state === "syncing";
  return (
    <section className={cn("rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-slate-900/70", className)} role={meta.role} aria-label={title ?? meta.label} aria-live="polite" aria-busy={isLoading || undefined}>
      <div className="flex items-start gap-3">
        <span className={cn("flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-100 dark:bg-white/10", meta.tone)}>
          <Icon className={cn("h-5 w-5", isLoading && "motion-safe:animate-spin")} aria-hidden="true" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold">{title ?? meta.label}</h3>
            <ClinicalStatusBadge status={state} />
          </div>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">{description ?? meta.description}</p>
          {actionLabel && onAction && <Button type="button" variant="outline" size="sm" className="mt-4" onClick={onAction}>{actionLabel}</Button>}
        </div>
      </div>
    </section>
  );
}

const STATUS_LABELS: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" | "success" | "warning" }> = {
  loading: { label: "جارٍ التحميل", variant: "outline" },
  loaded: { label: "محمّل", variant: "success" },
  empty: { label: "فارغ", variant: "outline" },
  partial: { label: "جزئي", variant: "warning" },
  offline: { label: "دون اتصال", variant: "warning" },
  syncing: { label: "مزامنة", variant: "outline" },
  error: { label: "خطأ", variant: "destructive" },
  unauthorized: { label: "تسجيل الدخول", variant: "outline" },
  forbidden: { label: "محجوب", variant: "warning" },
  expired: { label: "منتهٍ", variant: "warning" },
  conflict: { label: "تعارض", variant: "destructive" },
  maintenance: { label: "صيانة", variant: "secondary" },
  critical: { label: "حرج", variant: "destructive" },
  urgent: { label: "عاجل", variant: "warning" },
  routine: { label: "اعتيادي", variant: "secondary" },
  safe: { label: "مستقر", variant: "success" },
  restricted: { label: "مقيد", variant: "warning" },
};

export function ClinicalStatusBadge({ status, label }: { status: ClinicalSurfaceState | string; label?: string }) {
  const meta = STATUS_LABELS[status] ?? { label: status, variant: "outline" as const };
  return <Badge variant={meta.variant}>{label ?? meta.label}</Badge>;
}

export interface PatientContextCardProps {
  name: string;
  healthId?: string | null;
  ageSex?: string | null;
  allergies?: string[];
  criticalAlert?: string | null;
  restricted?: boolean;
  className?: string;
}

export function PatientContextCard({ name, healthId, ageSex, allergies = [], criticalAlert, restricted = false, className }: PatientContextCardProps) {
  if (restricted) {
    return <ClinicalStatePanel state="forbidden" title="سياق المريض محجوب" description="أعاد الخادم نطاقاً لا يسمح بعرض تفاصيل هذا المريض في الشاشة الحالية." className={className} />;
  }
  return (
    <Card className={cn("rounded-2xl", className)}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between gap-3 text-base">
          <span>سياق المريض</span>
          <ClinicalStatusBadge status={criticalAlert ? "critical" : "loaded"} label={criticalAlert ? "تنبيه" : "ضمن السياق"} />
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-start gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary"><Info className="h-5 w-5" aria-hidden="true" /></span>
          <div className="min-w-0"><p className="truncate text-base font-bold">{name}</p><p className="mt-1 text-xs text-muted-foreground">{[healthId, ageSex].filter(Boolean).join(" · ") || "معرّف محدود ضمن السياق"}</p></div>
        </div>
        {allergies.length > 0 && <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-3 text-sm text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-100"><p className="font-semibold">الحساسيات</p><p className="mt-1 text-xs leading-5">{allergies.join("، ")}</p></div>}
        {criticalAlert && <CriticalAlertBanner title="تنبيه حرج ضمن السياق" description={criticalAlert} />}
      </CardContent>
    </Card>
  );
}

export function CriticalAlertBanner({ title, description, acknowledged = false, className }: { title: string; description: string; acknowledged?: boolean; className?: string }) {
  return <section className={cn("rounded-2xl border border-rose-300 bg-rose-50/80 p-4 text-rose-950 dark:border-rose-900/60 dark:bg-rose-950/25 dark:text-rose-100", className)} role="alert" aria-label={title} aria-live="assertive"><div className="flex items-start gap-3"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-rose-600 text-white"><AlertTriangle className="h-5 w-5" aria-hidden="true" /></span><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><h3 className="font-bold">{title}</h3><ClinicalStatusBadge status={acknowledged ? "loaded" : "critical"} label={acknowledged ? "تم الاستلام" : "يحتاج استلاماً"} /></div><p className="mt-1 text-sm leading-6 opacity-90">{description}</p><p className="mt-2 text-xs font-medium opacity-75">الاستلام لا يساوي الإجراء السريري.</p></div></div></section>;
}

export interface ClinicalTimelineEvent {
  id: string;
  date: string;
  label: string;
  description?: string;
  status?: ClinicalSurfaceState | "critical";
}

export function ClinicalTimeline({ events, emptyMessage = "لا توجد أحداث ضمن النطاق الحالي.", className }: { events: ClinicalTimelineEvent[]; emptyMessage?: string; className?: string }) {
  if (events.length === 0) return <ClinicalStatePanel state="empty" title="لا توجد أحداث" description={emptyMessage} className={className} />;
  return <Card className={cn("rounded-2xl", className)}><CardHeader><CardTitle className="text-base">التسلسل السريري</CardTitle></CardHeader><CardContent><ol className="relative space-y-5 border-s border-slate-200 ps-6 dark:border-white/10">{events.map((event) => <li key={event.id} className="relative"><span className="absolute -start-[1.72rem] top-0.5 flex h-6 w-6 items-center justify-center rounded-full border-4 border-white bg-primary text-[10px] text-white dark:border-slate-900"><span className="sr-only">حدث</span>•</span><div className="flex flex-wrap items-center gap-2"><p className="font-semibold">{event.label}</p>{event.status && <ClinicalStatusBadge status={event.status} />}</div><p className="mt-1 text-xs text-muted-foreground">{event.date}</p>{event.description && <p className="mt-2 text-sm leading-6 text-muted-foreground">{event.description}</p>}</li>)}</ol></CardContent></Card>;
}

export { STATE_META };
