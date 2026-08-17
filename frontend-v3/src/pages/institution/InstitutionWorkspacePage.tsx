import { Link } from "react-router-dom";
import { Activity, ArrowLeft, BarChart3, Boxes, Building2, ClipboardList, CreditCard, FlaskConical, HeartPulse, Package, PlugZap, ShieldCheck, Users, Wifi } from "lucide-react";
import { Badge, Card, CardContent, CardHeader, CardTitle } from "@/components/ui";

type Module = {
  title: string;
  description: string;
  path: string;
  icon: typeof Activity;
  status: "متاح" | "قراءة محكومة" | "يتطلب صلاحية" | "تجريبي";
  tone: "teal" | "sky" | "amber" | "slate";
};

const modules: Module[] = [
  { title: "المساحة السريرية", description: "المرضى والطلبات ضمن سياق المؤسسة الحالي.", path: "/clinical-workspace", icon: HeartPulse, status: "قراءة محكومة", tone: "teal" },
  { title: "تشغيل المختبر", description: "سير العمل المعزول ومراجعة حالة المحللات وضبط الجودة.", path: "/lab-operations", icon: FlaskConical, status: "تجريبي", tone: "amber" },
  { title: "إدارة المرضى", description: "قائمة المرضى المصرح بها ضمن نطاق مساحة العمل.", path: "/patient-management", icon: Users, status: "قراءة محكومة", tone: "teal" },
  { title: "طلبات الفحوصات", description: "تتبع الطلبات عبر العقد canonical دون REST legacy.", path: "/orders", icon: ClipboardList, status: "قراءة محكومة", tone: "sky" },
  { title: "الصيدلية والمخزون", description: "عمليات الصرف والمخزون تحت صلاحيات المؤسسة.", path: "/pharmacy-operations", icon: Package, status: "متاح", tone: "teal" },
  { title: "الفوترة والتأمين", description: "مساحات مالية منفصلة مع حدود صلاحيات واضحة.", path: "/billing-insurance", icon: CreditCard, status: "يتطلب صلاحية", tone: "slate" },
  { title: "ربط الأجهزة", description: "بوابة الأجهزة مملوكة لحساب المؤسسة لا للحساب الفردي.", path: "/device-integration", icon: Wifi, status: "يتطلب صلاحية", tone: "slate" },
  { title: "التقارير والتنبيهات", description: "مراقبة تشغيلية وتنبيهات دون كشف سجل صحي غير مطلوب.", path: "/reports", icon: BarChart3, status: "قراءة محكومة", tone: "sky" },
];

const toneClass: Record<Module["tone"], string> = {
  teal: "border-teal-200 bg-teal-50/70 dark:border-teal-900/50 dark:bg-teal-950/20",
  sky: "border-sky-200 bg-sky-50/70 dark:border-sky-900/50 dark:bg-sky-950/20",
  amber: "border-amber-200 bg-amber-50/70 dark:border-amber-900/50 dark:bg-amber-950/20",
  slate: "border-slate-200 bg-slate-50/80 dark:border-white/10 dark:bg-white/[0.04]",
};

export function InstitutionWorkspacePage() {
  return (
    <div className="mx-auto max-w-7xl space-y-6" dir="rtl">
      <section className="rounded-[1.5rem] border border-slate-200 bg-gradient-to-l from-teal-50 via-white to-sky-50 p-6 shadow-sm dark:border-white/10 dark:from-teal-950/30 dark:via-slate-900 dark:to-sky-950/25">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-3xl"><div className="mb-3 inline-flex items-center gap-2 rounded-full border border-teal-100 bg-white/80 px-3 py-1.5 text-xs font-bold text-teal-700 dark:border-teal-900/60 dark:bg-white/5 dark:text-teal-200"><Building2 className="h-3.5 w-3.5" /> مركز تشغيل المؤسسة الصحية</div><h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-3xl">من شاشة واحدة، مع بقاء كل صلاحية في مكانها</h1><p className="mt-2 text-sm leading-7 text-muted-foreground">هذه اللوحة لا تستبدل الوحدات المتخصصة ولا تمنح صلاحيات جديدة. إنها نقطة انطلاق للمؤسسة الصحية الحكومية أو الخاصة، وتعرض فقط المسارات المبنية فعلياً في GULA.</p></div>
          <div className="flex items-center gap-2 rounded-2xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-xs text-emerald-800 dark:border-emerald-900/50 dark:bg-emerald-950/25 dark:text-emerald-200"><ShieldCheck className="h-4 w-4" /> عزل المؤسسة مفروض خادمياً</div>
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-3"><Metric icon={Building2} label="نطاق المؤسسة" value="محدد بالخادم" /><Metric icon={Activity} label="عمليات القراءة" value="محكومة" /><Metric icon={PlugZap} label="عمليات الكتابة" value="خلف الصلاحية" /></div>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">{modules.map((module) => { const Icon = module.icon; return <Card key={module.path} className={`group border transition hover:-translate-y-0.5 hover:shadow-md ${toneClass[module.tone]}`}><CardHeader className="pb-3"><div className="flex items-start justify-between gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/80 text-teal-700 shadow-sm dark:bg-white/10 dark:text-teal-200"><Icon className="h-5 w-5" /></span><Badge variant={module.status === "متاح" ? "success" : module.status === "تجريبي" ? "warning" : "outline"}>{module.status}</Badge></div><CardTitle className="pt-2 text-base">{module.title}</CardTitle></CardHeader><CardContent className="flex h-full flex-col gap-4"><p className="min-h-12 text-sm leading-6 text-muted-foreground">{module.description}</p><Link to={module.path} className="mt-auto inline-flex items-center gap-2 text-sm font-semibold text-teal-700 underline-offset-4 hover:underline dark:text-teal-300">فتح الوحدة <ArrowLeft className="h-4 w-4" /></Link></CardContent></Card>; })}</section>

      <Card className="border-amber-200 bg-amber-50/60 dark:border-amber-900/50 dark:bg-amber-950/20"><CardContent className="flex items-start gap-3 p-5 text-sm leading-7 text-amber-900 dark:text-amber-200"><Boxes className="mt-1 h-5 w-5 shrink-0" /><p><strong>حدود التشغيل:</strong> ربط الأجهزة، الفوترة، التكاملات الحكومية، والعمليات السريرية الحساسة تبقى خاضعة للمؤسسة والحوكمة. هذه الصفحة لا تنفذ إنشاء حسابات أو صرفاً أو اعتماد نتائج أو إرسال بيانات إلى وزارة الصحة.</p></CardContent></Card>
    </div>
  );
}

function Metric({ icon: Icon, label, value }: { icon: typeof Building2; label: string; value: string }) { return <Card><CardContent className="flex items-center justify-between p-4"><div><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 font-bold">{value}</p></div><Icon className="h-5 w-5 text-teal-600" /></CardContent></Card>; }
