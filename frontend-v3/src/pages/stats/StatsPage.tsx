import { useQuery } from "@tanstack/react-query";
import { statsApi } from "@/api/endpoints";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { LoadingSpinner, ErrorDisplay } from "@/components/shared/PageComponents";
import { Activity, BarChart3, CircleAlert, ClipboardList, FileBarChart, ShieldCheck, Users } from "lucide-react";

const numberFormatter = new Intl.NumberFormat("ar-IQ");

export function StatsPage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["stats"],
    queryFn: () => statsApi.summary(),
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  const totals = data?.totals;
  const cards = [
    { label: "إجمالي المرضى", value: totals?.patients ?? 0, icon: Users, iconClass: "bg-teal-50 text-[#0D9488] dark:bg-teal-950/40 dark:text-teal-300" },
    { label: "إجمالي الطلبات", value: totals?.orders ?? 0, icon: ClipboardList, iconClass: "bg-sky-50 text-sky-600 dark:bg-sky-950/40 dark:text-sky-300" },
    { label: "إجمالي الفحوصات", value: totals?.tests ?? 0, icon: Activity, iconClass: "bg-violet-50 text-violet-600 dark:bg-violet-950/40 dark:text-violet-300" },
    { label: "نتائج حرجة", value: totals?.critical_results ?? 0, icon: CircleAlert, iconClass: "bg-rose-50 text-rose-600 dark:bg-rose-950/40 dark:text-rose-300" },
  ];

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <section className="flex flex-col gap-4 rounded-[1.5rem] border border-teal-100 bg-white p-5 shadow-[0_18px_44px_-36px_rgba(15,23,42,0.48)] dark:border-teal-900/40 dark:bg-slate-900/70 sm:flex-row sm:items-end sm:justify-between sm:p-6">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-teal-100 bg-teal-50 px-3 py-1.5 text-xs font-bold text-[#0D9488] dark:border-teal-900/60 dark:bg-teal-950/35 dark:text-teal-200"><BarChart3 className="h-3.5 w-3.5" /> ملخص أداء</div>
          <h1 className="text-2xl font-bold tracking-tight text-[#0F172A] dark:text-white sm:text-3xl">الإحصاءات</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">ملخص إحصائي متاح ضمن نطاق العمل الحالي. القيم أدناه لا تمنح صلاحيات جديدة ولا تحل محل التقارير المؤسسية المعتمدة.</p>
        </div>
        <div className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-700 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-200"><ShieldCheck className="h-4 w-4 shrink-0 text-[#0D9488]" /><span><strong>قراءة محكومة</strong><br /><span className="text-slate-500 dark:text-slate-400">البيانات تُفرض وفق نطاق العمل</span></span></div>
      </section>

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map(({ label, value, icon: Icon, iconClass }) => (
          <Card key={label} className="border-slate-200/80 transition-shadow hover:shadow-md dark:border-slate-800">
            <CardContent className="flex items-center gap-4 p-4 sm:p-5"><div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl ${iconClass}`}><Icon className="h-5 w-5" /></div><div><p className="text-xs font-medium text-muted-foreground">{label}</p><p className="mt-1 text-2xl font-bold tracking-tight text-[#0F172A] dark:text-white">{numberFormatter.format(value)}</p></div></CardContent>
          </Card>
        ))}
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.15fr_.85fr]">
        <Card className="border-sky-100 dark:border-sky-900/40">
          <CardHeader className="border-b border-sky-100/80 p-5 dark:border-sky-900/40"><CardTitle className="flex items-center gap-2 text-base"><FileBarChart className="h-5 w-5 text-sky-600" /> نشاط الفترة</CardTitle><p className="mt-1 text-xs font-normal text-muted-foreground">مؤشرات الفترات المجمعة المتاحة في الملخص الحالي.</p></CardHeader>
          <CardContent className="grid gap-3 p-5 sm:grid-cols-3"><div className="rounded-2xl bg-slate-50 p-4 dark:bg-slate-800/60"><p className="text-xs text-muted-foreground">طلبات اليوم</p><p className="mt-2 text-xl font-bold">{numberFormatter.format(data?.today.orders ?? 0)}</p></div><div className="rounded-2xl bg-slate-50 p-4 dark:bg-slate-800/60"><p className="text-xs text-muted-foreground">طلبات الأسبوع</p><p className="mt-2 text-xl font-bold">{numberFormatter.format(data?.this_week.orders ?? 0)}</p></div><div className="rounded-2xl bg-slate-50 p-4 dark:bg-slate-800/60"><p className="text-xs text-muted-foreground">طلبات الشهر</p><p className="mt-2 text-xl font-bold">{numberFormatter.format(data?.this_month.orders ?? 0)}</p></div></CardContent>
        </Card>
        <Card className="border-rose-100 dark:border-rose-900/40"><CardHeader className="border-b border-rose-100/80 p-5 dark:border-rose-900/40"><CardTitle className="flex items-center gap-2 text-base"><CircleAlert className="h-5 w-5 text-rose-600" /> مؤشر النتائج الحرجة</CardTitle></CardHeader><CardContent className="p-5"><p className="text-3xl font-bold text-rose-700 dark:text-rose-300">{(totals?.critical_rate_pct ?? 0).toFixed(1)}%</p><p className="mt-2 text-sm leading-6 text-muted-foreground">معدل إجمالي ضمن النطاق المتاح. استخدم مسار التنبيهات المحكوم لمتابعة التفاصيل التي تظهر بصلاحيتك.</p></CardContent></Card>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <Card className="border-dashed border-slate-200 dark:border-slate-700"><CardContent className="p-5"><h2 className="font-semibold text-[#0F172A] dark:text-white">الاتجاهات اليومية</h2><p className="mt-2 text-sm leading-6 text-muted-foreground">ستظهر الرسوم بعد ربط مصدر اتجاهات موثق ومقيّد بالسياق.</p></CardContent></Card>
        <Card className="border-dashed border-slate-200 dark:border-slate-700"><CardContent className="p-5"><h2 className="font-semibold text-[#0F172A] dark:text-white">توزيع الفحوصات</h2><p className="mt-2 text-sm leading-6 text-muted-foreground">يظل هذا الموضع آمنًا إلى حين اعتماد مصدر توزيع الفحوصات.</p></CardContent></Card>
      </section>
    </div>
  );
}
