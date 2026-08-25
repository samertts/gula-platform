import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { dashboardApi } from "@/api/endpoints";
import { useAuth } from "@/contexts/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowUpLeft,
  CheckCircle2,
  ClipboardCheck,
  ClipboardList,
  Clock3,
  Database,
  FileText,
  FlaskConical,
  HeartPulse,
  LockKeyhole,
  Plus,
  ShieldCheck,
  Users,
  type LucideIcon,
} from "lucide-react";

type DashboardStat = { label: string; key: string; icon: LucideIcon; accent: string };
type DashboardQuickLink = { label: string; description: string; path: string; icon: LucideIcon; tone: string };
type DashboardExperience = {
  heroTitle: string;
  heroDescription: string;
  workspaceLabel: string;
  workspaceDescription: string;
  priorityTitle: string;
  priorityDescription: string;
  activityTitle: string;
  activityDescription: string;
  stats: DashboardStat[];
  quickLinks: DashboardQuickLink[];
};

const DEFAULT_STATS: DashboardStat[] = [
  { label: "إجمالي المرضى", key: "total_patients", icon: Users, accent: "border-teal-200 bg-teal-50/70 text-teal-700 dark:border-teal-900/60 dark:bg-teal-950/30 dark:text-teal-200" },
  { label: "الطلبات اليوم", key: "today_orders", icon: ClipboardList, accent: "border-sky-200 bg-sky-50/70 text-sky-700 dark:border-sky-900/60 dark:bg-sky-950/30 dark:text-sky-200" },
  { label: "النتائج اليوم", key: "today_results", icon: FlaskConical, accent: "border-indigo-200 bg-indigo-50/70 text-indigo-700 dark:border-indigo-900/60 dark:bg-indigo-950/30 dark:text-indigo-200" },
  { label: "التنبيهات الحرجة", key: "critical_alerts", icon: AlertTriangle, accent: "border-rose-200 bg-rose-50/80 text-rose-700 dark:border-rose-900/60 dark:bg-rose-950/30 dark:text-rose-200" },
];

const DEFAULT_QUICK_LINKS: DashboardQuickLink[] = [
  { label: "إضافة مريض", description: "استعرض مساحة المرضى المصرح بها", path: "/patients", icon: Users, tone: "bg-teal-50 text-teal-700 dark:bg-teal-950/40 dark:text-teal-200" },
  { label: "طلب جديد", description: "تابع مسار الطلبات والعينات", path: "/orders", icon: Plus, tone: "bg-sky-50 text-sky-700 dark:bg-sky-950/40 dark:text-sky-200" },
  { label: "مراجعة النتائج", description: "تحقق من النتائج حسب صلاحيتك", path: "/results", icon: ClipboardCheck, tone: "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-200" },
  { label: "التنبيهات الحرجة", description: "راقب الحالات ذات الأولوية", path: "/alerts", icon: AlertTriangle, tone: "bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-200" },
];

const DOCTOR_EXPERIENCE: DashboardExperience = {
  heroTitle: "مركز عمل الطبيب",
  heroDescription: "نظرة عملية على المرضى والطلبات والنتائج والمهام ذات الأولوية ضمن سياق الطبيب الحالي.",
  workspaceLabel: "سياق الطبيب",
  workspaceDescription: "RBAC · نطاق المؤسسة · سجل التدقيق",
  priorityTitle: "ما يحتاج انتباه الطبيب",
  priorityDescription: "تنبيهات وقراءات اصطناعية للعرض فقط، ولا تمثل مرضى حقيقيين.",
  activityTitle: "نشاط الطبيب الأخير",
  activityDescription: "سجل عرض اصطناعي للمتابعة دون أي أثر تشغيلي.",
  stats: [
    { label: "مرضى تحت المتابعة", key: "total_patients", icon: Users, accent: "border-teal-200 bg-teal-50/70 text-teal-700 dark:border-teal-900/60 dark:bg-teal-950/30 dark:text-teal-200" },
    { label: "طلبات اليوم", key: "today_orders", icon: ClipboardList, accent: "border-sky-200 bg-sky-50/70 text-sky-700 dark:border-sky-900/60 dark:bg-sky-950/30 dark:text-sky-200" },
    { label: "نتائج تحتاج مراجعة", key: "today_results", icon: FlaskConical, accent: "border-indigo-200 bg-indigo-50/70 text-indigo-700 dark:border-indigo-900/60 dark:bg-indigo-950/30 dark:text-indigo-200" },
    { label: "تنبيهات حرجة", key: "critical_alerts", icon: AlertTriangle, accent: "border-rose-200 bg-rose-50/80 text-rose-700 dark:border-rose-900/60 dark:bg-rose-950/30 dark:text-rose-200" },
  ],
  quickLinks: [
    { label: "مساحة المرضى", description: "ابحث وافتح ملخص المريض المصرح به", path: "/patient-management", icon: Users, tone: "bg-teal-50 text-teal-700 dark:bg-teal-950/40 dark:text-teal-200" },
    { label: "الطلبات والعينات", description: "تابع الطلبات ومسار العينة", path: "/orders", icon: ClipboardList, tone: "bg-sky-50 text-sky-700 dark:bg-sky-950/40 dark:text-sky-200" },
    { label: "مراجعة النتائج", description: "افتح النتائج ضمن صلاحيتك", path: "/results", icon: ClipboardCheck, tone: "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-200" },
    { label: "التقارير", description: "استعرض التقارير المصرح بها", path: "/reports", icon: FileText, tone: "bg-violet-50 text-violet-700 dark:bg-violet-950/40 dark:text-violet-200" },
  ],
};

const CLINIC_EXPERIENCE: DashboardExperience = {
  heroTitle: "مركز تشغيل العيادة",
  heroDescription: "لوحة موحدة للأطباء والمرضى والخدمات والعمليات، مع إبقاء كل تغيير خلف تفويض GULA ومراجعة المؤسسة.",
  workspaceLabel: "سياق المؤسسة",
  workspaceDescription: "Workspace · المنشأة · الدور الحالي",
  priorityTitle: "أولويات العيادة",
  priorityDescription: "مؤشرات اصطناعية للعرض؛ لا تُنشئ حجوزات أو تعدّل سجلات حقيقية.",
  activityTitle: "النشاط التشغيلي",
  activityDescription: "ملخص قراءة فقط لا يمثل سجلاً إنتاجياً.",
  stats: [
    { label: "المرضى النشطون", key: "total_patients", icon: Users, accent: "border-teal-200 bg-teal-50/70 text-teal-700 dark:border-teal-900/60 dark:bg-teal-950/30 dark:text-teal-200" },
    { label: "العمليات اليوم", key: "today_orders", icon: ClipboardList, accent: "border-sky-200 bg-sky-50/70 text-sky-700 dark:border-sky-900/60 dark:bg-sky-950/30 dark:text-sky-200" },
    { label: "التقارير اليوم", key: "today_results", icon: FileText, accent: "border-indigo-200 bg-indigo-50/70 text-indigo-700 dark:border-indigo-900/60 dark:bg-indigo-950/30 dark:text-indigo-200" },
    { label: "تنبيهات تحتاج تصعيداً", key: "critical_alerts", icon: AlertTriangle, accent: "border-rose-200 bg-rose-50/80 text-rose-700 dark:border-rose-900/60 dark:bg-rose-950/30 dark:text-rose-200" },
  ],
  quickLinks: [
    { label: "دليل المرضى", description: "استعرض المسار والملخص المصرح به", path: "/patient-management", icon: Users, tone: "bg-teal-50 text-teal-700 dark:bg-teal-950/40 dark:text-teal-200" },
    { label: "المستشفى والأقسام", description: "راجع الهيكل المؤسسي المصرح به", path: "/hospital", icon: Database, tone: "bg-sky-50 text-sky-700 dark:bg-sky-950/40 dark:text-sky-200" },
    { label: "عمليات المختبر", description: "تابع العينات والنتائج وضبط الجودة", path: "/lab-operations", icon: FlaskConical, tone: "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-200" },
    { label: "التقارير", description: "استعرض مؤشرات وتقارير المؤسسة", path: "/reports", icon: FileText, tone: "bg-violet-50 text-violet-700 dark:bg-violet-950/40 dark:text-violet-200" },
  ],
};

const CITIZEN_EXPERIENCE: DashboardExperience = {
  heroTitle: "مساحة المواطن الصحية",
  heroDescription: "مدخل بسيط وآمن إلى ملفك ونتائجك ومواعيدك ضمن حساب GULA الشخصي.",
  workspaceLabel: "مساحة المواطن",
  workspaceDescription: "هوية شخصية · قراءة مصرح بها · خصوصية",
  priorityTitle: "ما يهمك الآن",
  priorityDescription: "لا تمثل هذه الشاشة تشخيصاً أو وصفة علاجية.",
  activityTitle: "آخر التحديثات",
  activityDescription: "قراءات شخصية فقط، مع إبقاء القرارات السريرية خارج هذه المساحة.",
  stats: [
    { label: "العناصر الصحية", key: "total_patients", icon: HeartPulse, accent: "border-teal-200 bg-teal-50/70 text-teal-700 dark:border-teal-900/60 dark:bg-teal-950/30 dark:text-teal-200" },
    { label: "المواعيد", key: "today_orders", icon: ClipboardList, accent: "border-sky-200 bg-sky-50/70 text-sky-700 dark:border-sky-900/60 dark:bg-sky-950/30 dark:text-sky-200" },
    { label: "النتائج", key: "today_results", icon: FlaskConical, accent: "border-indigo-200 bg-indigo-50/70 text-indigo-700 dark:border-indigo-900/60 dark:bg-indigo-950/30 dark:text-indigo-200" },
    { label: "تنبيهات الحساب", key: "critical_alerts", icon: AlertCircle, accent: "border-rose-200 bg-rose-50/80 text-rose-700 dark:border-rose-900/60 dark:bg-rose-950/30 dark:text-rose-200" },
  ],
  quickLinks: [
    { label: "مساحتي الصحية", description: "افتح الملف والنتائج والمواعيد", path: "/citizen", icon: HeartPulse, tone: "bg-teal-50 text-teal-700 dark:bg-teal-950/40 dark:text-teal-200" },
    { label: "الإشعارات", description: "راجع التنبيهات المعتمدة", path: "/notifications", icon: AlertCircle, tone: "bg-sky-50 text-sky-700 dark:bg-sky-950/40 dark:text-sky-200" },
    { label: "الملف الشخصي", description: "تحقق من إعدادات حسابك", path: "/profile", icon: Users, tone: "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-200" },
    { label: "إمكانية الوصول", description: "خصّص العرض واللغة", path: "/settings/accessibility", icon: ShieldCheck, tone: "bg-violet-50 text-violet-700 dark:bg-violet-950/40 dark:text-violet-200" },
  ],
};

const LAB_EXPERIENCE: DashboardExperience = {
  heroTitle: "مركز عمليات المختبر",
  heroDescription: "نظرة عملية وهادئة على سير العمل، مؤشرات الأداء، والتنبيهات ذات الأولوية ضمن مساحة العمل الحالية.",
  workspaceLabel: "مساحة آمنة",
  workspaceDescription: "RBAC · عزل المؤسسة · سجل التدقيق",
  priorityTitle: "التنبيهات ذات الأولوية",
  priorityDescription: "تنبيهات اصطناعية للعرض، لا تمثل مرضى حقيقيين.",
  activityTitle: "النشاط الأخير",
  activityDescription: "سجل عرض اصطناعي للمتابعة دون أي أثر تشغيلي.",
  stats: DEFAULT_STATS,
  quickLinks: DEFAULT_QUICK_LINKS,
};

function dashboardExperienceFor(role?: string): DashboardExperience {
  if (role === "doctor") return DOCTOR_EXPERIENCE;
  if (role === "citizen") return CITIZEN_EXPERIENCE;
  if (["admin", "master_admin", "ministry_admin", "province_admin", "staff"].includes(role ?? "")) return CLINIC_EXPERIENCE;
  return LAB_EXPERIENCE;
}

const DEMO_ROLE_SUMMARIES: Record<string, { label: string; summary: string }> = {
  doctor: { label: "طبيب تجريبي", summary: "قراءة المرضى والطلبات والنتائج الاصطناعية ضمن نطاق العرض." },
  technician: { label: "فني مختبر تجريبي", summary: "استعراض مسار العينات والنتائج المختبرية الاصطناعية." },
  lab_admin: { label: "مدير مختبر تجريبي", summary: "استعراض مؤشرات المختبر والموظفين والتقارير دون عمليات كتابة." },
  citizen: { label: "مواطن تجريبي", summary: "استعراض مساحة المواطن ببيانات اصطناعية ومعزولة بالكامل." },
};


const demoActivity = [
  { title: "تمت مزامنة قائمة العينات", detail: "مساحة العرض التجريبي · منذ 8 دقائق", icon: Database, tone: "text-teal-600" },
  { title: "تمت مراجعة نتيجة اصطناعية", detail: "سجل قراءة فقط · منذ 21 دقيقة", icon: CheckCircle2, tone: "text-emerald-600" },
  { title: "تحديث حالة التشغيل", detail: "الفحوصات الأساسية تعمل · منذ 34 دقيقة", icon: Activity, tone: "text-sky-600" },
];

export function DashboardPage() {
  const { demoMode, user } = useAuth();
  const experience = dashboardExperienceFor(user?.role);
  const demoRole = DEMO_ROLE_SUMMARIES[user?.role ?? ""] ?? DEMO_ROLE_SUMMARIES.doctor!;
  const { data, isLoading, isError } = useQuery<Record<string, unknown>>({
    queryKey: ["dashboard", demoMode ? "demo" : "institution", user?.role],
    queryFn: async () => {
      if (demoMode) return dashboardApi.demo(user?.role as "doctor" | "technician" | "lab_admin" | "citizen") as unknown as Record<string, unknown>;
      return {};
    },
    enabled: demoMode,
  });

  const readValue = (key: string) => demoMode ? (isLoading ? "…" : isError ? "—" : String(data?.[key] ?? 0)) : "—";

  return (
    <div className="mx-auto max-w-7xl space-y-6 pb-2">
      <section className="relative overflow-hidden rounded-[1.75rem] border border-slate-200/80 bg-[#0F172A] p-5 text-white shadow-[0_24px_70px_-35px_rgba(15,23,42,0.75)] dark:border-white/10 sm:p-7">
        <div className="absolute -left-12 -top-24 h-64 w-64 rounded-full bg-[#0D9488]/25 blur-3xl" />
        <div className="absolute -bottom-32 right-8 h-72 w-72 rounded-full bg-sky-500/20 blur-3xl" />
        <div className="relative grid gap-7 lg:grid-cols-[1fr_auto] lg:items-end">
          <div className="max-w-3xl">
            <div className="mb-4 flex flex-wrap items-center gap-2 text-xs font-semibold">
              <span className="inline-flex items-center gap-2 rounded-full border border-teal-200/20 bg-teal-200/10 px-3 py-1.5 text-teal-100">
                <span className="h-2 w-2 rounded-full bg-teal-300 shadow-[0_0_0_4px_rgba(45,212,191,0.12)]" />
                حالة التشغيل مستقرة
              </span>
              {demoMode && <span className="inline-flex items-center gap-2 rounded-full border border-amber-300/20 bg-amber-300/10 px-3 py-1.5 text-amber-100"><ShieldCheck className="h-3.5 w-3.5" /> عرض تجريبي معزول</span>}
            </div>
            <p className="text-sm text-teal-200">صباح الخير{user?.name ? `، ${user.name}` : ""}</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">{experience.heroTitle}</h1>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-300">{experience.heroDescription}</p>
            {demoMode && <div className="mt-5 inline-flex max-w-2xl flex-wrap items-center gap-2 rounded-2xl border border-amber-200/20 bg-amber-200/10 px-3.5 py-2.5 text-xs text-amber-100"><LockKeyhole className="h-3.5 w-3.5" /><strong>{demoRole.label}</strong><span className="text-amber-100/70">— {demoRole.summary}</span></div>}
          </div>
          <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.07] p-4 text-sm text-slate-200 backdrop-blur-sm">
            <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-400/15 text-teal-200"><HeartPulse className="h-6 w-6" /></span>
            <div><p className="font-bold">{experience.workspaceLabel}</p><p className="mt-1 text-xs text-slate-400">{experience.workspaceDescription}</p></div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label={`مؤشرات ${experience.workspaceLabel}`}>
        {experience.stats.map(({ label, key, icon: Icon, accent }) => (
          <Card key={key} className="group overflow-hidden rounded-2xl border-slate-200/80 bg-white shadow-sm transition duration-200 hover:-translate-y-0.5 hover:shadow-lg dark:border-white/10 dark:bg-slate-900/70">
            <CardContent className="relative p-5">
              <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-l from-[#0D9488] to-sky-400 opacity-80" />
              <div className="flex items-start justify-between gap-3">
                <span className={`flex h-11 w-11 items-center justify-center rounded-2xl border ${accent}`}><Icon className="h-5 w-5" /></span>
                <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[10px] font-bold text-slate-500 dark:bg-white/10 dark:text-slate-300">{demoMode ? "تجريبي" : "غير مهيأ"}</span>
              </div>
              <p className="mt-5 text-sm text-muted-foreground">{label}</p>
              <p className="mt-1 text-3xl font-bold tracking-tight text-[#0F172A] dark:text-white">{readValue(key)}</p>
              <div className="mt-4 flex items-center gap-1.5 text-[11px] text-muted-foreground"><Clock3 className="h-3.5 w-3.5" /> تحديث آمن للقراءة</div>
            </CardContent>
          </Card>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70">
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <div><CardTitle className="flex items-center gap-2 text-base"><Activity className="h-5 w-5 text-[#0D9488]" /> مسارات العمل السريعة</CardTitle><p className="mt-1 text-xs text-muted-foreground">{experience.heroDescription}</p></div>
            <span className="rounded-full bg-teal-50 px-2.5 py-1 text-[10px] font-bold text-teal-700 dark:bg-teal-950/40 dark:text-teal-200">وصول سريع</span>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            {experience.quickLinks.map(({ label, description, path, icon: Icon, tone }) => (
              <Link key={path} to={path} className="group flex items-center gap-3 rounded-2xl border border-slate-200/80 p-3.5 transition hover:-translate-y-0.5 hover:border-teal-300 hover:bg-teal-50/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 dark:border-white/10 dark:hover:border-teal-800 dark:hover:bg-teal-950/20">
                <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${tone}`}><Icon className="h-[18px] w-[18px]" /></span>
                <span className="min-w-0 flex-1"><span className="block text-sm font-bold">{label}</span><span className="mt-1 block truncate text-xs text-muted-foreground">{description}</span></span>
                <ArrowUpLeft className="h-4 w-4 text-muted-foreground transition group-hover:-translate-y-0.5 group-hover:text-teal-600" />
              </Link>
            ))}
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70">
          <CardHeader><CardTitle className="flex items-center gap-2 text-base"><ShieldCheck className="h-5 w-5 text-emerald-600" /> حالة التشغيل</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className={`flex items-center justify-between rounded-2xl p-4 ${demoMode ? "bg-emerald-50 dark:bg-emerald-950/30" : "bg-amber-50 dark:bg-amber-950/30"}`}>
              <div><p className={`text-sm font-bold ${demoMode ? "text-emerald-800 dark:text-emerald-200" : "text-amber-800 dark:text-amber-200"}`}>{demoMode ? "العرض التجريبي" : "التكامل المؤسسي غير مهيأ"}</p><p className={`mt-1 text-xs ${demoMode ? "text-emerald-700/70 dark:text-emerald-300/70" : "text-amber-700/70 dark:text-amber-300/70"}`}>{demoMode ? "بيانات اصطناعية معزولة للعرض" : "لن تُعرض مؤشرات أو بيانات حتى اعتماد عقد القراءة والسياق."}</p></div>
              <span className={`rounded-full px-2.5 py-1 text-[10px] font-bold text-white ${demoMode ? "bg-emerald-500" : "bg-amber-600"}`}>{demoMode ? "معزول" : "محمي"}</span>
            </div>
            <div className="space-y-3"><div className="flex items-center justify-between text-xs"><span className="text-muted-foreground">حماية الجلسة</span><span className="font-bold text-emerald-600">مفعلة</span></div><div className="h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-white/10"><div className="h-full w-full rounded-full bg-gradient-to-l from-emerald-400 to-teal-500" /></div><div className="flex items-center justify-between text-xs"><span className="text-muted-foreground">قراءة مؤسسية</span><span className={`font-bold ${demoMode ? "text-emerald-600" : "text-amber-700"}`}>{demoMode ? "معزولة" : "معلقة حتى التوثيق"}</span></div><div className="h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-white/10"><div className={`h-full rounded-full bg-gradient-to-l ${demoMode ? "w-full from-cyan-400 to-blue-500" : "w-1/4 from-amber-300 to-amber-500"}`} /></div></div>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <Card className="rounded-2xl border-rose-200/80 bg-white shadow-sm dark:border-rose-900/50 dark:bg-slate-900/70">
          <CardHeader className="flex flex-row items-center justify-between space-y-0"><div><CardTitle className="flex items-center gap-2 text-base"><AlertCircle className="h-5 w-5 text-rose-600" /> {experience.priorityTitle}</CardTitle><p className="mt-1 text-xs text-muted-foreground">{experience.priorityDescription}</p></div><Link to="/alerts" className="text-xs font-bold text-rose-700 hover:underline dark:text-rose-300">عرض الكل</Link></CardHeader>
          <CardContent className="space-y-3"><div className="flex items-start gap-3 rounded-xl border border-rose-100 bg-rose-50/70 p-3 text-sm dark:border-rose-900/50 dark:bg-rose-950/20"><AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600" /><div><p className="font-bold text-rose-900 dark:text-rose-200">يتطلب مراجعة المشرف</p><p className="mt-1 text-xs text-rose-800/70 dark:text-rose-200/70">تنبيه اصطناعي ضمن بيئة القراءة فقط.</p></div></div><div className="flex items-center justify-between rounded-xl border border-slate-200/80 p-3 text-xs dark:border-white/10"><span className="text-muted-foreground">حالة التنبيهات</span><span className="inline-flex items-center gap-1.5 font-bold text-emerald-600"><CheckCircle2 className="h-3.5 w-3.5" /> لا توجد كتابة تلقائية</span></div></CardContent>
        </Card>

        <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/70">
          <CardHeader className="flex flex-row items-center justify-between space-y-0"><div><CardTitle className="flex items-center gap-2 text-base"><Clock3 className="h-5 w-5 text-[#0D9488]" /> {experience.activityTitle}</CardTitle><p className="mt-1 text-xs text-muted-foreground">{experience.activityDescription}</p></div><span className="rounded-full bg-slate-100 px-2.5 py-1 text-[10px] font-bold text-slate-600 dark:bg-white/10 dark:text-slate-300">قراءة فقط</span></CardHeader>
          <CardContent className="space-y-1">{demoActivity.map(({ title, detail, icon: Icon, tone }) => <div key={title} className="flex items-start gap-3 rounded-xl p-3 transition hover:bg-slate-50 dark:hover:bg-white/[0.04]"><span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-100 dark:bg-white/10"><Icon className={`h-4 w-4 ${tone}`} /></span><div className="min-w-0"><p className="text-sm font-semibold">{title}</p><p className="mt-1 text-xs text-muted-foreground">{detail}</p></div></div>)}</CardContent>
        </Card>
      </section>
    </div>
  );
}
