import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { apiClient, type ConsentSummary, type WorkspaceSummary } from "@/api/client";
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
  BadgeCheck,
  BriefcaseBusiness,
  CheckCircle2,
  ChevronLeft,
  CircleAlert,
  Clock3,
  FileCheck2,
  FileHeart,
  IdCard,
  KeyRound,
  LockKeyhole,
  ShieldCheck,
  Smartphone,
  UserRound,
  UsersRound,
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
  withdrawn: "ملغاة",
  expired: "منتهية",
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

function normalizedStatus(value: string | null | undefined): string {
  return String(value ?? "").trim().toLowerCase();
}

function isWorkspaceAvailable(status: string | null | undefined): boolean {
  return ["active", "restricted"].includes(normalizedStatus(status));
}

function statusVariant(status: string): "success" | "warning" | "destructive" | "default" {
  const normalized = normalizedStatus(status);
  if (["active", "verified", "approved"].includes(normalized)) return "success";
  if (["restricted", "pending", "provisional"].includes(normalized)) return "warning";
  if (["suspended", "archived", "deactivated", "withdrawn", "expired"].includes(normalized)) return "destructive";
  return "default";
}

function workspaceIcon(workspace: WorkspaceSummary) {
  return workspace.workspace_type === "citizen" ? UserRound : BriefcaseBusiness;
}

function formatDate(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleDateString("ar-IQ");
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
  const isAvailable = isWorkspaceAvailable(workspace.status);
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

function VerificationJourney({ verified, demoMode }: { verified: boolean; demoMode: boolean }) {
  const steps = [
    { label: "حساب GULA", description: verified ? "حالة الحساب منعكسة من الجلسة" : "لم تكتمل حالة التحقق في الجلسة", icon: BadgeCheck, state: verified ? "مكتمل" : "يتطلب تحقق" },
    { label: "وثيقة الهوية وOCR", description: "يتطلب خدمة تحقق خادمية مؤسسية؛ لا نقرأ وثيقة داخل الواجهة وحدها", icon: IdCard, state: "غير مفعّل" },
    { label: "NFC والوجه الحي", description: "NFC اختياري وliveness يحتاج SDK وسياسة وموافقة واضحة", icon: Smartphone, state: "غير مفعّل" },
    { label: "التحقق الحكومي", description: "لا يُعرض كحالة موثقة دون تكامل حكومي مفوض ونتيجة خادمية", icon: ShieldCheck, state: "غير مفعّل" },
  ];

  return (
    <Card className="border-slate-200/80 dark:border-white/10">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base"><FileCheck2 className="h-5 w-5 text-teal-600" aria-hidden="true" /> مسار التحقق والهوية</CardTitle>
        <p className="mt-1 text-xs font-normal leading-5 text-muted-foreground">{demoMode ? "المراحل التالية معروضة كسيناريو اصطناعي فقط." : "يظهر كل مستوى كما يثبته العقد الخادمي، ولا تتحول قراءة OCR إلى تحقق تلقائي."}</p>
      </CardHeader>
      <CardContent className="space-y-3">
        {steps.map(({ label, description, icon: Icon, state }) => {
          const complete = state === "مكتمل";
          return (
            <div key={label} className="flex items-start gap-3 rounded-2xl border border-slate-200/80 p-3.5 dark:border-white/10">
              <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${complete ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/35 dark:text-emerald-200" : "bg-slate-100 text-slate-500 dark:bg-white/[0.06] dark:text-slate-300"}`}>
                <Icon className="h-[18px] w-[18px]" aria-hidden="true" />
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2"><p className="text-sm font-bold">{label}</p><Badge variant={complete ? "success" : "default"}>{state}</Badge></div>
                <p className="mt-1 text-xs leading-5 text-muted-foreground">{description}</p>
              </div>
            </div>
          );
        })}
        <div role="note" className="flex items-start gap-2 rounded-xl bg-amber-50 px-3 py-2.5 text-xs leading-5 text-amber-900 dark:bg-amber-950/25 dark:text-amber-100"><CircleAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />لا يوجد زر يرفع مستوى الثقة محلياً؛ الانتقال يحتاج دليلاً وقراراً خادمياً قابلاً للتدقيق.</div>
      </CardContent>
    </Card>
  );
}

function ConsentPanel({ demoMode, consents, isLoading, isError, onRetry, onWithdraw, withdrawingId, actionError }: { demoMode: boolean; consents: ConsentSummary[]; isLoading: boolean; isError: boolean; onRetry: () => void; onWithdraw: (consent: ConsentSummary) => void; withdrawingId: string | null; actionError: string | null }) {
  const activeConsents = consents.filter((consent) => normalizedStatus(consent.status) === "active");
  return (
    <Card className="border-slate-200/80 dark:border-white/10">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base"><KeyRound className="h-5 w-5 text-indigo-600" aria-hidden="true" />المشاركة والموافقات</CardTitle>
        <p className="mt-1 text-xs font-normal leading-5 text-muted-foreground">النطاق والمدة يحددهما الخادم، والموافقة لا تتجاوز الدور أو السياسة أو القانون.</p>
      </CardHeader>
      <CardContent>
        {demoMode ? (
          <div className="flex items-start gap-3 rounded-2xl bg-amber-50 p-4 text-amber-900 dark:bg-amber-950/25 dark:text-amber-100"><Clock3 className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" /><div><p className="text-sm font-bold">سيناريو مشاركة اصطناعي</p><p className="mt-1 text-xs leading-5 text-amber-900/75 dark:text-amber-100/75">لا توجد موافقة حقيقية ولا جهة حقيقية في الوضع التجريبي.</p></div></div>
        ) : isLoading ? (
          <p className="text-sm text-muted-foreground">جارٍ تحميل حالة الموافقات من الخادم…</p>
        ) : isError ? (
          <div className="space-y-3"><p role="alert" className="text-sm text-destructive">تعذر تحميل الموافقات. لم يتم إنشاء بديل محلي.</p><Button type="button" variant="outline" onClick={onRetry}>إعادة المحاولة</Button></div>
        ) : activeConsents.length === 0 ? (
          <div className="flex items-start gap-3 rounded-2xl border border-dashed border-slate-300 p-4 dark:border-white/15"><LockKeyhole className="mt-0.5 h-5 w-5 shrink-0 text-muted-foreground" aria-hidden="true" /><div><p className="text-sm font-bold">لا توجد موافقات نشطة</p><p className="mt-1 text-xs leading-5 text-muted-foreground">لا تُمنح أي جهة وصولاً افتراضياً من هذه الصفحة.</p></div></div>
        ) : (
          <div className="space-y-2">
            {actionError && <p role="alert" className="text-sm text-destructive">{actionError}</p>}
            {activeConsents.slice(0, 3).map((consent) => (
              <div key={consent.uuid} className="flex flex-col gap-3 rounded-2xl bg-indigo-50/70 p-3.5 dark:bg-indigo-950/25 sm:flex-row sm:items-center"><CheckCircle2 className="hidden h-5 w-5 shrink-0 text-indigo-600 sm:block" aria-hidden="true" /><div className="min-w-0 flex-1"><p className="truncate text-sm font-bold">{consent.resource_domain}</p><p className="mt-1 text-xs text-muted-foreground">حتى {formatDate(consent.expires_at)} · نطاق محدد</p></div><div className="flex items-center justify-between gap-3 sm:justify-end"><Badge variant="success">نشطة</Badge><Button type="button" variant="outline" className="shrink-0" disabled={withdrawingId === consent.id} onClick={() => onWithdraw(consent)}>{withdrawingId === consent.id ? "جارٍ الإلغاء…" : "إلغاء الوصول"}</Button></div></div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ControlTile({ icon: Icon, title, description, href, disabled }: { icon: typeof FileHeart; title: string; description: string; href?: string; disabled?: boolean }) {
  const content = <div className={`flex h-full items-start gap-3 rounded-2xl border p-4 transition ${disabled ? "border-slate-200/70 bg-slate-50/70 dark:border-white/10 dark:bg-white/[0.03]" : "border-teal-100 bg-teal-50/45 hover:-translate-y-0.5 hover:border-teal-300 dark:border-teal-900/50 dark:bg-teal-950/20"}`}><span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${disabled ? "bg-slate-100 text-slate-500 dark:bg-white/[0.06]" : "bg-teal-100 text-teal-700 dark:bg-teal-900/50 dark:text-teal-200"}`}><Icon className="h-[18px] w-[18px]" aria-hidden="true" /></span><span className="min-w-0 flex-1"><span className="flex flex-wrap items-center gap-2"><span className="text-sm font-bold">{title}</span>{disabled && <Badge variant="default">يتطلب عقداً خادمياً</Badge>}</span><span className="mt-1 block text-xs leading-5 text-muted-foreground">{description}</span></span>{href && <ArrowLeft className="mt-1 h-4 w-4 shrink-0 text-teal-600" aria-hidden="true" />}</div>;
  return href && !disabled ? <Link to={href} className="block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 focus-visible:ring-offset-2">{content}</Link> : content;
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
  const consents = useQuery({
    queryKey: ["my-record", "consents"],
    queryFn: () => apiClient.listMyConsents(),
    enabled: !demoMode,
    retry: false,
  });
  const [switchingId, setSwitchingId] = useState<string | null>(null);
  const [switchError, setSwitchError] = useState<string | null>(null);
  const [withdrawingId, setWithdrawingId] = useState<string | null>(null);
  const [consentActionError, setConsentActionError] = useState<string | null>(null);

  const liveWorkspaces = useMemo(() => workspaces.data?.workspaces ?? [], [workspaces.data]);
  const liveConsents = useMemo(() => consents.data?.consents ?? [], [consents.data]);
  const verified = user?.is_verified === true;
  const canOpenCitizenHealth = demoMode ? user?.role === "citizen" : liveWorkspaces.some((workspace) => workspace.workspace_type === "citizen" && isWorkspaceAvailable(workspace.status));

  async function handleWithdraw(consent: ConsentSummary) {
    setConsentActionError(null);
    setWithdrawingId(consent.id);
    try {
      await apiClient.withdrawConsent(consent.id);
      await consents.refetch();
    } catch {
      setConsentActionError("تعذر إلغاء الوصول من الخادم. لم يتغير السجل محلياً.");
    } finally {
      setWithdrawingId(null);
    }
  }

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
    <div className="mx-auto max-w-7xl space-y-6 pb-4">
      <header className="relative overflow-hidden rounded-[1.75rem] border border-teal-100 bg-gradient-to-br from-[#0F172A] via-[#123B46] to-[#0D9488] p-5 text-white shadow-[0_24px_70px_-35px_rgba(15,23,42,0.75)] sm:p-7">
        <div className="absolute -left-16 -top-24 h-64 w-64 rounded-full bg-teal-300/20 blur-3xl" />
        <div className="absolute -bottom-36 right-8 h-72 w-72 rounded-full bg-sky-400/20 blur-3xl" />
        <div className="relative flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <div className="mb-4 flex flex-wrap items-center gap-2 text-xs font-semibold">
              <span className="inline-flex items-center gap-2 rounded-full border border-teal-100/20 bg-white/10 px-3 py-1.5 text-teal-50"><IdCard className="h-3.5 w-3.5" aria-hidden="true" /> مركز التحكم بهويتي</span>
              {demoMode && <span className="inline-flex items-center gap-2 rounded-full border border-amber-100/20 bg-amber-200/10 px-3 py-1.5 text-amber-50"><ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" /> معاينة معزولة</span>}
            </div>
            <p className="text-sm text-teal-100">هوية الشخص في GULA</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">هوية واحدة، وسياقات صحية واضحة</h1>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-200">هذه الشاشة تنظم الحساب والتحقق والموافقات ومساحات العمل دون نسخ السجل الصحي أو بيانات الدولة إلى مخزن شامل واحد.</p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/[0.08] p-4 backdrop-blur-sm">
            <p className="text-xs text-slate-300">حالة حساب GULA</p>
            <p className="mt-1 text-lg font-bold">{verified ? "موثق في الجلسة" : "يتطلب تحققاً"}</p>
            <p className="mt-1 text-xs text-slate-300">ليست دليلاً على تحقق حكومي</p>
          </div>
        </div>
      </header>

      <section className="grid gap-6 lg:grid-cols-[0.72fr_1.28fr]" aria-label="ملخص هوية الشخص">
        <Card className="overflow-hidden border-teal-100 dark:border-teal-900/40">
          <div className="h-20 bg-gradient-to-br from-teal-500 via-teal-700 to-slate-950" />
          <CardContent className="relative p-5 pt-0 text-center">
            <div className="mx-auto -mt-10 flex h-20 w-20 items-center justify-center rounded-3xl border-4 border-white bg-gradient-to-br from-teal-500 to-slate-800 text-2xl font-bold text-white shadow-lg dark:border-slate-900">{user?.name?.charAt(0) || "م"}</div>
            <h2 className="mt-4 text-xl font-bold">{user?.name || "مستخدم GULA"}</h2>
            <p dir="ltr" className="mt-1 break-all text-sm text-muted-foreground">{user?.email || "—"}</p>
            <Badge className="mt-3 rounded-full bg-teal-50 px-3 py-1 text-teal-700 hover:bg-teal-50 dark:bg-teal-950/40 dark:text-teal-200">{user?.role || "عضو"}</Badge>
            <div className="mt-5 flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-300"><LockKeyhole className="h-3.5 w-3.5 text-teal-600" aria-hidden="true" /> لا يظهر رقم وطني أو معرف صحي خام</div>
          </CardContent>
        </Card>

        <VerificationJourney verified={verified} demoMode={demoMode} />
      </section>

      <section className="grid gap-6 xl:grid-cols-2" aria-label="مركز التحكم بالمواطن">
        <ConsentPanel demoMode={demoMode} consents={liveConsents} isLoading={consents.isLoading} isError={consents.isError} onRetry={() => { void consents.refetch(); }} onWithdraw={(consent) => { void handleWithdraw(consent); }} withdrawingId={withdrawingId} actionError={consentActionError} />
        <Card className="border-slate-200/80 dark:border-white/10">
          <CardHeader><CardTitle className="flex items-center gap-2 text-base"><UsersRound className="h-5 w-5 text-teal-600" aria-hidden="true" /> خدمات هويتي الصحية</CardTitle><p className="mt-1 text-xs font-normal leading-5 text-muted-foreground">روابط إلى حدود منفصلة؛ لا تخلط بين الهوية والملف الطبي أو الأسرة أو التأمين.</p></CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            <ControlTile icon={FileHeart} title="السجل الصحي" description={canOpenCitizenHealth ? "افتح المساحة الصحية التي يسمح بها الخادم." : "تظهر بعد انعكاس علاقة المواطن والأهلية من الخادم."} href={canOpenCitizenHealth ? "/citizen" : undefined} disabled={!canOpenCitizenHealth} />
            <ControlTile icon={Smartphone} title="أجهزتي وجلساتي" description="يتطلب عقد قراءة ذاتي يعرض الحد الأدنى من metadata دون كشف الموقع أو الأسرار." disabled />
            <ControlTile icon={UsersRound} title="أفراد الأسرة" description="علاقة ولي الأمر ليست ملكية لهوية الطفل؛ يتطلب نطاقاً قانونياً ومراجعة خادمية." disabled />
            <ControlTile icon={FileCheck2} title="الوثائق والتأمين" description="مساحات منفصلة ستظهر عند توفر عقد قراءة مفوض ومحدود الغرض." disabled />
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
        <CardContent className="flex flex-col gap-3 p-5 sm:flex-row sm:items-start"><ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-teal-600" aria-hidden="true" /><div><p className="text-sm font-bold">قاعدة الوصول</p><p className="mt-1 text-xs leading-6 text-muted-foreground">تبديل السياق والموافقات يمران عبر الخادم ويُسجلان هناك. لا تمنح هذه الصفحة دوراً، ولا تتيح سجل مواطن آخر، ولا تتجاوز CitizenRelationship أو VerificationRecord أو قيود المؤسسة.</p></div><ArrowLeft className="hidden h-4 w-4 shrink-0 text-muted-foreground sm:mr-auto sm:block" aria-hidden="true" /></CardContent>
      </Card>
    </div>
  );
}
