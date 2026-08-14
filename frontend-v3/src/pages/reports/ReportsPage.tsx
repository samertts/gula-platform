import { FileText, LockKeyhole, ShieldCheck } from "lucide-react";

export function ReportsPage() {
  return (
    <section
      dir="rtl"
      className="mx-auto max-w-5xl space-y-6"
      data-contract-status="unbound"
      data-governance-state="safe-empty"
      aria-labelledby="reports-title"
    >
      <header className="rounded-[1.5rem] border border-sky-100 bg-white p-5 shadow-[0_18px_44px_-36px_rgba(15,23,42,0.48)] dark:border-sky-900/40 dark:bg-slate-900/70 sm:p-6">
        <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-sky-100 bg-sky-50 px-3 py-1.5 text-xs font-bold text-sky-700 dark:border-sky-900/60 dark:bg-sky-950/35 dark:text-sky-200"><FileText className="h-3.5 w-3.5" /> تقارير تشغيلية</div>
        <h1 id="reports-title" className="text-2xl font-bold tracking-tight text-[#0F172A] dark:text-white sm:text-3xl">التقارير</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">سطح محكوم للتقارير التشغيلية. لا تُعرض أي بيانات حتى تُربط قناة قراءة موثقة وتُثبت سياقات المنشأة والتفويض على الخادم.</p>
      </header>

      <div className="overflow-hidden rounded-[1.5rem] border border-dashed border-sky-200 bg-gradient-to-b from-sky-50/70 to-white p-6 text-center dark:border-sky-900/55 dark:from-sky-950/20 dark:to-slate-900/70 sm:p-10">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-[#0D9488] shadow-sm dark:bg-slate-800"><LockKeyhole className="h-6 w-6" /></div>
        <h2 className="mt-5 text-lg font-bold text-[#0F172A] dark:text-white">لا توجد تقارير تشغيلية معروضة</h2>
        <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted-foreground">ستظهر التقارير بعد ربط مصدر البيانات المعتمد والتحقق من حدود القراءة والسياق المؤسسي.</p>
        <div className="mx-auto mt-6 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-600 dark:border-white/10 dark:bg-slate-800 dark:text-slate-300"><ShieldCheck className="h-3.5 w-3.5 text-[#0D9488]" /> حالة آمنة — لا بيانات غير محكومة</div>
      </div>
    </section>
  );
}

export default ReportsPage;
