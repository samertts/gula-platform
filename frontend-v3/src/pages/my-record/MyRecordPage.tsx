import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { apiClient, type WorkspaceSummary } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui";
import {
  ArrowLeft,
  BriefcaseBusiness,
  CheckCircle2,
  ChevronLeft,
  CircleAlert,
  FileCheck2,
  IdCard,
  LockKeyhole,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { ErrorDisplay, PageLoadingSkeleton } from "@/components/shared/PageComponents";

const PROFESSIONAL_LABELS: Record<string, string> = {
  physician: "طبيب",
  doctor: "طبيب",
  dentist: "طبيب أسنان",
  pharmacist: "صيدلي",
  nurse: "ممرض",
  midwife: "قابلة",
  medical_laboratory_scientist: "اختصاصي مختبر طبي",
  laboratory_technician: "فني مختبر",
  technician: "فني مختبر",
  radiology_professional: "اختصاصي أشعة",
  other_healthcare_professional: "مهني صحي",
};

const WORKSPACE_TYPE_LABELS: Record<string, string> = {
  citizen: "مساحة المواطن",
  professional: "مساحة مهنية",
  organization: "مساحة مؤسسة",
  facility: "مساحة منشأة",
  department: "مساحة قسم",
  administrative: "مساحة إدارية",
  government: "مساحة حكومية",
};

const STATUS_LABELS: Record<string, string> = {
  active: "نشطة",
  restricted: "مقيدة",
  suspended: "موقوفة",
  archived: "مؤرشفة",
  deactivated: "معطلة",
};

function getProfessionalLabel(type?: string | null): string {
  return type ? PROFESSIONAL_LABELS[type] ?? "مهني صحي" : "مهنية";
}

function getWorkspaceLabel(workspace: WorkspaceSummary): string {
  if (workspace.workspace_type === "citizen") return "مساحة المواطن";
  if (workspace.professional_type) return `مساحة ${getProfessionalLabel(workspace.professional_type)}`;
  return WORKSPACE_TYPE_LABELS[workspace.workspace_type] ?? workspace.name_ar ?? workspace.name ?? "مساحة مصرح بها";
}

function getWorkspaceDescription(workspace: WorkspaceSummary): string {
  if (workspace.workspace_type === "citizen") {
    return "سجلك الشخصي والقراءات الصحية التي يعرضها عقد المواطن المصرح به فقط.";
  }
  if (workspace.professional_type) {
    return `السياق المهني المرتبط بإثبات ${getProfessionalLabel(workspace.professional_type)} الصالح.`;
  }
  if (workspace.is_personal) return "مساحة شخصية مرتبطة بحسابك الحالي.";
  return "سياق مؤسسي يظهر فقط عندما يسمح الخادم بهذه العضوية.";
}

function statusVariant(status: string): "success" | "warning" | "destructive" | "default" {
  if (status === "active") return "success";
  if (status === "restricted") return "warning";
  if (["suspended", "archived", "deactivated"].includes(status)) return "destructive";
  return "default";
}

function workspaceIcon(workspace: WorkspaceSummary) {
  return workspace.workspace_type === "citizen" ? UserRound : BriefcaseBusiness;
}

function DemoWorkspaceCard({ role }: { role: string }) {
  const professional = role === "citizen" ? null : getProfessionalLabel(role);
  return (
    <Card className="border-amber-200/80 bg-amber-50/45 shadow-sm dark:border-amber-900/50 dark:bg-amber-950/20">
      <CardContent className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-200">
            <BriefcaseBusiness className="h-5 w-5" aria-hidden="true" />
          </span>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="font-bold">{professional ? `مساحة ${professional} تجريبية` : "مساحة المواطن التجريبية"}</h3>
              <Badge variant="warning">اصطناعية</Badge>
            </div>
            <p className="mt-1 text-sm leading-6 text-muted-foreground">سياق للعرض فقط؛ لا يمثل مؤسسة أو مهنيًا أو مواطنًا حقيقيًا.</p>
          </div>
        </div>
        <span className="inline-flex items-center gap-2 rounded-xl border border-amber-300/60 bg-white/60 px-3 py-2 text-xs font-semibold text-amber-900 dark:border-amber-800/60 dark:bg-white/[0.04] dark:text-amber-100">
          <LockKeyhole className="h-3.5 w-3.5" aria-hidden="true" /> قراءة فقط
        </span>
      </CardContent>
    </Card>
  );
}

function WorkspaceCard({ workspace, onSwitch, switching }: { workspace: WorkspaceSummary; onSwitch: (workspace: WorkspaceSummary) => void; switching: boolean }) {
  const Icon = workspaceIcon(workspace);
  const isAvailable = ["active", "restricted"].includes(workspace.status);
  return (
    <Card className="border-slate-200/80 bg-white shadow-sm transition hover:-translate-y-0.5 hover:border-teal-200 dark:border-white/10 dark:bg-slate-900/70 dark:hover:border-teal-900">
      <CardContent className="flex flex-col gap-4 p-5">
        <div className="flex items-start gap-3">
          <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl ${workspace.workspace_type === "citizen" ? "bg-teal-50 text-teal-700 dark:bg-teal-950/40 dark:text-teal-200" : "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-200"}`}>
            <Icon className="h-5 w-5" aria-hidden="true" />
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="truncate font-bold">{getWorkspaceLabel(workspace)}</h3>
              <Badge variant={statusVariant(workspace.status)}>{STATUS_LABELS[workspace.status] ?? workspace.status}</Badge>
            </div>
            <p className="mt-1 text-sm leading-6 text-muted-foreground">{getWorkspaceDescription(workspace)}</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <span className="rounded-lg bg-slate-100 px-2.5 py-1.5 dark:bg-white/[0.06]">{WORKSPACE_TYPE_LABELS[workspace.workspace_type] ?? "سياق مصرح"}</span>
          {workspace.is_personal ? <span className="rounded-lg bg-slate-100 px-2.5 py-1.5 dark:bg-white/[0.06]">شخصية</span> : <span className="rounded-lg bg-slate-100 px-2.5 py-1.5 dark:bg-white/[0.06]">مرتبطة بعضوية</span>}
        </div>
        <Button type="button" variant="outline" className="w-full justify-between bg-white/60 dark:bg-white/[0.03]" disabled={!isAvailable || switching} onClick={() => onSwitch(workspace)}>
          <span>{isAvailable ? "تبديل السياق" : "غير متاحة حالياً"}</span>
          <ChevronLeft className="h-4 w-4" aria-hidden="true" />
        </Button>
      </CardContent>
    </Card>
  );
}

export default function MyRecordPage() {
  const { demoMode, user } = useAuth();
  const navigate = useNavigate();
  const workspaces = useQuery({
    queryKey: ["my-record", "workspaces"],
    queryFn: () => apiClient.listWorkspaces(),
    enabled: !demoMode,
    retry: false,
  });
  const [switchingId, setSwitchingId] = useState<string | null>(null);
  const [switchError, setSwitchError] = useState<string | null>(null);

  const liveWorkspaces = useMemo(() => workspaces.data?.workspaces ?? [], [workspaces.data]);
  const verified = user?.is_verified === true;

  async function handleSwitch(workspace: WorkspaceSummary) {
    setSwitchError(null);
    setSwitchingId(workspace.id);
    try {
      await apiClient.switchWorkspace(workspace.id);
      navigate("/dashboard");
    } catch {
      setSwitchError("رفض الخادم تبديل السياق أو انتهت صلاحية العضوية. لم يتم تغيير أي صلاحية محلياً.");
    } finally {
      setSwitchingId(null);
    }
  }

  if (workspaces.isLoading && !demoMode) return <PageLoadingSkeleton />;
  if (workspaces.isError && !demoMode) {
    return <ErrorDisplay error="تعذر تحميل المساحات المصرح بها من الخادم." onRetry={() => { void workspaces.refetch(); }} />;
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <header className="relative overflow-hidden rounded-[1.75rem] border border-teal-100 bg-gradient-to-br from-[#0F172A] via-[#123B46] to-[#0D9488] p-5 text-white shadow-[0_24px_70px_-35px_rgba(15,23,42,0.75)] sm:p-7">
        <div className="absolute -left-16 -top-24 h-64 w-64 rounded-full bg-teal-300/20 blur-3xl" />
        <div className="absolute -bottom-36 right-8 h-72 w-72 rounded-full bg-sky-400/20 blur-3xl" />
        <div className="relative flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <div className="mb-4 flex flex-wrap items-center gap-2 text-xs font-semibold">
              <span className="inline-flex items-center gap-2 rounded-full border border-teal-100/20 bg-white/10 px-3 py-1.5 text-teal-50"><IdCard className="h-3.5 w-3.5" aria-hidden="true" /> السجل الشخصي ومساحات العمل</span>
              {demoMode && <span className="inline-flex items-center gap-2 rounded-full border border-amber-100/20 bg-amber-200/10 px-3 py-1.5 text-amber-50"><ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" /> معاينة معزولة</span>}
            </div>
            <p className="text-sm text-teal-100">هوية GULA الحالية</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">سجلك يبدأ بهويتك، لا بكل بيانات الدولة</h1>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-200">تجمع هذه الشاشة ملخص الحساب ومساحات العمل التي أعادها الخادم فقط. الملف الصحي والبيانات المهنية تبقى في مساراتها المفوضة ولا تُنسخ إلى بطاقة واحدة.</p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/[0.08] p-4 backdrop-blur-sm">
            <p className="text-xs text-slate-300">حالة الحساب</p>
            <p className="mt-1 text-lg font-bold">{verified ? "موثق" : "يحتاج إلى تحقق"}</p>
            <p className="mt-1 text-xs text-slate-300">الصلاحيات مصدرها الخادم</p>
          </div>
        </div>
      </header>

      <section className="grid gap-6 lg:grid-cols-[0.72fr_1.28fr]" aria-label="ملخص سجل المواطن">
        <Card className="overflow-hidden border-teal-100 dark:border-teal-900/40">
          <div className="h-20 bg-gradient-to-br from-teal-500 via-teal-700 to-slate-950" />
          <CardContent className="relative p-5 pt-0 text-center">
            <div className="mx-auto -mt-10 flex h-20 w-20 items-center justify-center rounded-3xl border-4 border-white bg-gradient-to-br from-teal-500 to-slate-800 text-2xl font-bold text-white shadow-lg dark:border-slate-900">{user?.name?.charAt(0) || "م"}</div>
            <h2 className="mt-4 text-xl font-bold">{user?.name || "مستخدم GULA"}</h2>
            <p dir="ltr" className="mt-1 break-all text-sm text-muted-foreground">{user?.email || "—"}</p>
            <Badge className="mt-3 rounded-full bg-teal-50 px-3 py-1 text-teal-700 hover:bg-teal-50 dark:bg-teal-950/40 dark:text-teal-200">{user?.role || "عضو"}</Badge>
            <div className="mt-5 flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-300"><LockKeyhole className="h-3.5 w-3.5 text-teal-600" aria-hidden="true" /> لا يظهر رقم وطني أو سجل صحي خام</div>
          </CardContent>
        </Card>

        <Card className="border-slate-200/80 dark:border-white/10">
          <CardHeader><CardTitle className="flex items-center gap-2 text-base"><FileCheck2 className="h-5 w-5 text-teal-600" aria-hidden="true" /> ما الذي يظهر هنا؟</CardTitle><p className="mt-1 text-xs font-normal text-muted-foreground">حدود مصممة لمنع جمع بيانات أكثر من الغرض.</p></CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            <div className="flex items-start gap-3 rounded-2xl bg-emerald-50 p-4 dark:bg-emerald-950/25"><CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-600" aria-hidden="true" /><div><p className="text-sm font-bold text-emerald-900 dark:text-emerald-200">هوية الحساب</p><p className="mt-1 text-xs leading-5 text-emerald-800/75 dark:text-emerald-200/70">الاسم والبريد وحالة التحقق من جلسة GULA.</p></div></div>
            <div className="flex items-start gap-3 rounded-2xl bg-indigo-50 p-4 dark:bg-indigo-950/25"><BriefcaseBusiness className="mt-0.5 h-5 w-5 shrink-0 text-indigo-600" aria-hidden="true" /><div><p className="text-sm font-bold text-indigo-900 dark:text-indigo-200">مساحات الخادم</p><p className="mt-1 text-xs leading-5 text-indigo-800/75 dark:text-indigo-200/70">المواطن والطبيب والصيدلي وغيرهم يظهرون فقط كمساحات مؤهلة.</p></div></div>
            <div className="flex items-start gap-3 rounded-2xl bg-amber-50 p-4 dark:bg-amber-950/25 sm:col-span-2"><CircleAlert className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" aria-hidden="true" /><div><p className="text-sm font-bold text-amber-900 dark:text-amber-200">ما لا يظهر</p><p className="mt-1 text-xs leading-5 text-amber-800/75 dark:text-amber-200/70">لا تُعرض بيانات وطنية أو صحية أو مهنية خام هنا، ولا تنشئ هذه الصفحة حساباً أو ترخيصاً أو صلاحية.</p></div></div>
          </CardContent>
        </Card>
      </section>

      <section className="space-y-4" aria-labelledby="workspaces-heading">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div><h2 id="workspaces-heading" className="text-xl font-bold tracking-tight">مساحات العمل المصرح بها</h2><p className="mt-1 text-sm text-muted-foreground">المصدر الوحيد لهذه القائمة هو عقد NIAM في الخادم.</p></div>
          <span className="inline-flex w-fit items-center gap-2 rounded-full bg-slate-100 px-3 py-1.5 text-[10px] font-bold text-slate-600 dark:bg-white/10 dark:text-slate-300"><LockKeyhole className="h-3.5 w-3.5" aria-hidden="true" /> وصول سياقي</span>
        </div>
        {switchError && <div role="alert" className="rounded-2xl border border-destructive/20 bg-destructive/5 px-4 py-3 text-sm text-destructive">{switchError}</div>}
        {demoMode ? <DemoWorkspaceCard role={user?.role ?? "citizen"} /> : liveWorkspaces.length > 0 ? <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{liveWorkspaces.map((workspace) => <WorkspaceCard key={workspace.id} workspace={workspace} onSwitch={(item) => void handleSwitch(item)} switching={switchingId === workspace.id} />)}</div> : <Card className="border-dashed border-slate-300 dark:border-white/15"><CardContent className="flex flex-col items-center gap-3 p-8 text-center"><CircleAlert className="h-8 w-8 text-muted-foreground" aria-hidden="true" /><p className="font-semibold">لا توجد مساحات عمل مؤهلة حالياً</p><p className="max-w-xl text-sm leading-6 text-muted-foreground">لا يمكن للواجهة إنشاء مساحة مهنية محلياً. بعد اعتماد التحقق أو العضوية من الجهة المختصة ستظهر المساحة هنا من الخادم.</p></CardContent></Card>}
      </section>

      <Card className="border-slate-200/80 bg-slate-50/70 dark:border-white/10 dark:bg-white/[0.03]">
        <CardContent className="flex flex-col gap-3 p-5 sm:flex-row sm:items-start"><ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-teal-600" aria-hidden="true" /><div><p className="text-sm font-bold">قاعدة الوصول</p><p className="mt-1 text-xs leading-6 text-muted-foreground">تبديل السياق يمر عبر الخادم ويُسجل هناك. لا تمنح هذه الصفحة أي دور، ولا تسمح بمشاهدة بيانات مواطن آخر، ولا تتجاوز علاقة CitizenRelationship أو سجل التحقق المهني.</p></div><ArrowLeft className="hidden h-4 w-4 shrink-0 text-muted-foreground sm:mr-auto sm:block" aria-hidden="true" /></CardContent>
      </Card>
    </div>
  );
}
