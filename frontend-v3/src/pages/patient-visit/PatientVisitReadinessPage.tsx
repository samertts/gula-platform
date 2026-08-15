import {
  AlertTriangle,
  CheckCircle2,
  ClipboardList,
  Clock3,
  FileWarning,
  LockKeyhole,
  ShieldCheck,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { PageHeader } from "@/components/shared/PageComponents";

type ReadinessStatus = "READY" | "READY_FOR_REVIEW" | "BACKEND_DEPENDENCY" | "BLOCKED";

type Surface = {
  id: string;
  title: string;
  english: string;
  description: string;
  status: ReadinessStatus;
  reason: string;
};

const surfaces: Surface[] = [
  {
    id: "ia",
    title: "معمارية Patient Visit",
    english: "Patient Visit Information Architecture",
    description: "Appointment منفصل عن Encounter مع مسار Check-in وQueue واضح.",
    status: "READY",
    reason: "وثيقة تصميمية لا تنفذ عملية سريرية.",
  },
  {
    id: "check-in",
    title: "مسار Check-in",
    english: "Check-in flow",
    description: "عرض أقل قدر من البيانات مع organization وfacility وworkspace scope.",
    status: "BACKEND_DEPENDENCY",
    reason: "لا يوجد عقد typed يثبت قرار التحقق والقبول.",
  },
  {
    id: "queue",
    title: "قائمة الانتظار",
    english: "Work Queue",
    description: "بحث وتصفية وتقسيم صفحات دون رفع أولوية أو نقل حالة من الواجهة.",
    status: "BACKEND_DEPENDENCY",
    reason: "Queue contract وpermission وaudit غير مثبتة للواجهة.",
  },
  {
    id: "encounter",
    title: "مساحة Encounter الموحدة",
    english: "Unified Encounter workspace",
    description: "Patient Header وVisit Summary وTimeline وأقسام مقيدة بالصلاحيات.",
    status: "BACKEND_DEPENDENCY",
    reason: "النموذج الوطني موجود داخليًا، لكن UI request/response contract غير مثبت.",
  },
  {
    id: "triage",
    title: "Triage والعلامات الحيوية",
    english: "Triage and vitals",
    description: "تصميم حقول للمخولين فقط دون اختراع Clinical Scoring.",
    status: "BLOCKED",
    reason: "لا تفعيل قبل عقد موثق ونظام قياس معتمد وسياسة انتقال.",
  },
  {
    id: "results",
    title: "النتائج المرتبطة بالزيارة",
    english: "Encounter-linked results",
    description: "Pending وAvailable وReviewed ضمن scope المريض والمنشأة.",
    status: "BLOCKED",
    reason: "لا اعتماد نتيجة من الواجهة ونتائج route غير موثقة سياقيًا.",
  },
  {
    id: "close",
    title: "إغلاق Encounter",
    english: "Close Encounter",
    description: "مراجعة المتطلبات ثم تأكيد server-confirmed قبل Visit Summary.",
    status: "BLOCKED",
    reason: "المتطلبات الإلزامية وversion conflict وaudit contract غير مثبتة.",
  },
  {
    id: "patient-view",
    title: "عرض المريض المفلتر",
    english: "Policy-filtered patient view",
    description: "الموعد والزيارة والملخص والتعليمات والنتائج المتاحة فقط.",
    status: "BACKEND_DEPENDENCY",
    reason: "سياسة كشف البيانات المقيدة وعقد citizen visit غير مثبتين.",
  },
];

const statusMeta: Record<ReadinessStatus, { label: string; variant: "success" | "warning" | "destructive" | "outline"; icon: typeof CheckCircle2 }> = {
  READY: { label: "جاهز للتوثيق", variant: "success", icon: CheckCircle2 },
  READY_FOR_REVIEW: { label: "جاهز للمراجعة", variant: "outline", icon: ClipboardList },
  BACKEND_DEPENDENCY: { label: "يعتمد على Backend", variant: "warning", icon: Clock3 },
  BLOCKED: { label: "محجوب حاليًا", variant: "destructive", icon: LockKeyhole },
};

function StatusBadge({ status }: { status: ReadinessStatus }) {
  const meta = statusMeta[status];
  const Icon = meta.icon;
  return <Badge variant={meta.variant}><Icon className="ml-1 h-3.5 w-3.5" aria-hidden="true" />{meta.label}<span className="sr-only"> ({status})</span></Badge>;
}

export function PatientVisitReadinessPage() {
  return (
    <div className="space-y-6" dir="rtl">
      <PageHeader
        title="جاهزية نظام زيارة المريض"
        description="Patient Visit / Encounter readiness — سطح تصميم وContract Review فقط، دون تنفيذ سريري حقيقي."
      />

      <Card className="border-amber-200 bg-amber-50/70 dark:border-amber-900/50 dark:bg-amber-950/20">
        <CardContent className="flex items-start gap-3 p-5 text-sm leading-7">
          <ShieldCheck className="mt-1 h-5 w-5 shrink-0 text-amber-700 dark:text-amber-300" aria-hidden="true" />
          <div>
            <p className="font-bold text-amber-950 dark:text-amber-100">Prototype آمن وغير تشغيلي</p>
            <p className="mt-1 text-amber-900/80 dark:text-amber-100/75">
              لا توجد بيانات مرضى أو API أو كتابة سريرية في هذه الشاشة. قرارات Encounter وCheck-in والنتائج والإغلاق تبقى server-authoritative، وأي عنصر غير موثق مصنف BACKEND_DEPENDENCY أو BLOCKED.
            </p>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="ملخص الجاهزية">
        {(Object.keys(statusMeta) as ReadinessStatus[]).map((status) => {
          const MetaIcon = statusMeta[status].icon;
          const count = surfaces.filter((surface) => surface.status === status).length;
          return (
            <Card key={status} className="min-h-28">
              <CardContent className="flex h-full items-center justify-between gap-3 p-5">
                <div><p className="text-xs text-muted-foreground">{statusMeta[status].label}</p><p className="mt-1 text-2xl font-bold">{count}</p></div>
                <MetaIcon className="h-5 w-5 text-primary" aria-hidden="true" />
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2 text-base"><ClipboardList className="h-5 w-5 text-primary" aria-hidden="true" />خريطة الأسطح والعقود</CardTitle></CardHeader>
        <CardContent className="grid gap-4 lg:grid-cols-2">
          {surfaces.map((surface) => (
            <article key={surface.id} className="rounded-2xl border bg-card p-5 shadow-sm" aria-labelledby={`${surface.id}-title`}>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0"><h2 id={`${surface.id}-title`} className="font-bold">{surface.title}</h2><p className="mt-1 text-xs text-muted-foreground">{surface.english}</p></div>
                <StatusBadge status={surface.status} />
              </div>
              <p className="mt-4 text-sm leading-6 text-foreground/85">{surface.description}</p>
              <div className="mt-4 flex items-start gap-2 rounded-xl bg-muted/60 p-3 text-xs leading-5 text-muted-foreground"><FileWarning className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" /><span>{surface.reason}</span></div>
            </article>
          ))}
        </CardContent>
      </Card>

      <Card className="border-slate-200 dark:border-white/10">
        <CardContent className="flex items-start gap-3 p-5 text-sm leading-7 text-muted-foreground">
          <AlertTriangle className="mt-1 h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
          <p><strong className="text-foreground">حاجز التنفيذ:</strong> لا تتحول أي بطاقة إلى تشغيل فعلي إلا بعد عقد Request/Response typed، وصلاحية server-side، وعزل organization/facility/workspace، وversion conflict، وidempotency، وimmutable audit، واختبارات انتقالات الحالة.</p>
        </CardContent>
      </Card>
    </div>
  );
}

export default PatientVisitReadinessPage;
