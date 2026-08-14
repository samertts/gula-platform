import { BellRing, LockKeyhole, ShieldCheck } from "lucide-react";

/**
 * لا يوجد عقد "صندوق وارد" مؤهل في الواجهة الحالية. ويُمنع من هذا السطح إنشاء
 * إشعارات أو البحث برقم طلب، لأنهما قد يؤديان إلى إرسال غير مقصود أو كشف بيانات
 * اتصال/رسائل خارج سياق التفويض المثبت خادميًا.
 */
export function NotificationsPage() {
  return (
    <section
      dir="rtl"
      className="mx-auto max-w-5xl space-y-6"
      data-contract-status="unbound"
      data-governance-state="safe-empty"
      aria-labelledby="notifications-title"
    >
      <header className="rounded-[1.5rem] border border-violet-100 bg-white p-5 shadow-[0_18px_44px_-36px_rgba(15,23,42,0.48)] dark:border-violet-900/40 dark:bg-slate-900/70 sm:p-6">
        <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-violet-100 bg-violet-50 px-3 py-1.5 text-xs font-bold text-violet-700 dark:border-violet-900/60 dark:bg-violet-950/35 dark:text-violet-200"><BellRing className="h-3.5 w-3.5" /> مركز الإشعارات</div>
        <h1 id="notifications-title" className="text-2xl font-bold tracking-tight text-[#0F172A] dark:text-white sm:text-3xl">الإشعارات</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">واجهة آمنة لتجربة صندوق وارد مؤسسي. لا ترسل المنصة رسائل ولا تعرض أرقام اتصال أو معاينات لمحتوى الإشعارات من هذا السطح.</p>
      </header>

      <div className="overflow-hidden rounded-[1.5rem] border border-dashed border-violet-200 bg-gradient-to-b from-violet-50/70 to-white p-6 text-center dark:border-violet-900/55 dark:from-violet-950/20 dark:to-slate-900/70 sm:p-10">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-violet-600 shadow-sm dark:bg-slate-800 dark:text-violet-300"><LockKeyhole className="h-6 w-6" /></div>
        <h2 className="mt-5 text-lg font-bold text-[#0F172A] dark:text-white">صندوق الإشعارات غير مربوط بعد</h2>
        <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted-foreground">سيظهر السجل بعد اعتماد عقد بيانات مؤسسي يفرض هوية المستلم، نطاق المنشأة، قنوات الإرسال، وسجل التدقيق على الخادم.</p>
        <div className="mx-auto mt-6 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-600 dark:border-white/10 dark:bg-slate-800 dark:text-slate-300"><ShieldCheck className="h-3.5 w-3.5 text-[#0D9488]" /> وضع آمن — بلا إرسال أو كشف بيانات اتصال</div>
      </div>
    </section>
  );
}
