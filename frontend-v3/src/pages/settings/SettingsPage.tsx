import { Card, CardContent } from "@/components/ui";
import { Bell, CheckCircle2, Globe, Palette, Settings2, Shield, SlidersHorizontal } from "lucide-react";

const settingsSections = [
  { icon: Globe, title: "اللغة والمنطقة", desc: "إعدادات اللغة واتجاه العرض والمنطقة الزمنية.", tone: "teal" },
  { icon: Palette, title: "المظهر", desc: "نظام الألوان، الوضع الداكن، وكثافة العرض.", tone: "violet" },
  { icon: Bell, title: "الإشعارات", desc: "تفضيلات التنبيهات وقنوات الإشعار المعتمدة.", tone: "amber" },
  { icon: Shield, title: "الأمان", desc: "إدارة الجلسات وعوامل المصادقة وسياسات الوصول.", tone: "rose" },
  { icon: Settings2, title: "عام", desc: "تفضيلات المنصة العامة ضمن نطاق مؤسستك.", tone: "sky" },
] as const;

const toneClasses = {
  teal: "bg-teal-50 text-[#0D9488] dark:bg-teal-950/40 dark:text-teal-300",
  violet: "bg-violet-50 text-violet-600 dark:bg-violet-950/40 dark:text-violet-300",
  amber: "bg-amber-50 text-amber-600 dark:bg-amber-950/40 dark:text-amber-300",
  rose: "bg-rose-50 text-rose-600 dark:bg-rose-950/40 dark:text-rose-300",
  sky: "bg-sky-50 text-sky-600 dark:bg-sky-950/40 dark:text-sky-300",
};

export function SettingsPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <header className="flex flex-col gap-4 rounded-[1.5rem] border border-slate-200/80 bg-white p-5 shadow-[0_18px_44px_-36px_rgba(15,23,42,0.48)] dark:border-white/10 dark:bg-slate-900/70 sm:flex-row sm:items-end sm:justify-between sm:p-6"><div><div className="mb-3 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-bold text-slate-700 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-200"><SlidersHorizontal className="h-3.5 w-3.5 text-[#0D9488]" /> تفضيلات المنصة</div><h1 className="text-2xl font-bold tracking-tight text-[#0F172A] dark:text-white sm:text-3xl">الإعدادات</h1><p className="mt-2 text-sm leading-6 text-muted-foreground">إعدادات النظام والتفضيلات التي تظهر وفق دورك ومساحة العمل الحالية.</p></div><div className="inline-flex items-center gap-2 rounded-2xl border border-emerald-100 bg-emerald-50 px-3.5 py-2.5 text-xs text-emerald-700 dark:border-emerald-900/50 dark:bg-emerald-950/30 dark:text-emerald-200"><CheckCircle2 className="h-4 w-4" /> سياق الجلسة محكوم</div></header>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {settingsSections.map(({ icon: Icon, title, desc, tone }) => (
          <Card key={title} className="group border-slate-200/80 transition-all hover:-translate-y-0.5 hover:border-teal-200 hover:shadow-md dark:border-slate-800 dark:hover:border-teal-900/60"><CardContent className="p-5"><div className="flex items-start justify-between gap-4"><div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl ${toneClasses[tone]}`}><Icon className="h-5 w-5" /></div><span className="rounded-full border border-slate-200 px-2.5 py-1 text-[11px] font-semibold text-slate-500 dark:border-white/10 dark:text-slate-400">مسار محكوم</span></div><h2 className="mt-5 text-base font-bold text-[#0F172A] dark:text-white">{title}</h2><p className="mt-2 text-sm leading-6 text-muted-foreground">{desc}</p></CardContent></Card>
        ))}
      </div>

      <div className="flex items-start gap-3 rounded-2xl border border-sky-100 bg-sky-50/70 p-4 dark:border-sky-900/50 dark:bg-sky-950/20"><Shield className="mt-0.5 h-5 w-5 shrink-0 text-sky-600 dark:text-sky-300" /><div><p className="text-sm font-semibold text-sky-950 dark:text-sky-100">تغييرات الإعدادات تمر عبر مسار موثّق</p><p className="mt-1 text-xs leading-5 text-sky-900/70 dark:text-sky-100/70">لا يتم حفظ تغييرات مباشرة من هذه البطاقات. ستُفتح خيارات التعديل فقط عند توفر عقد وصلاحية وتسجيل تدقيق مناسبين.</p></div></div>
    </div>
  );
}
