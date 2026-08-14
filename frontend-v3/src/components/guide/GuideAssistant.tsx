import { useMemo, useState } from "react";
import { HelpCircle, X, ChevronLeft, ChevronRight, ShieldCheck } from "lucide-react";
import { useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useLocale } from "@/contexts/LocaleContext";

const routeTips: Record<string, { ar: string; en: string }[]> = {
  "/dashboard": [
    { ar: "ابدأ من مؤشرات الحالة ثم افتح التنبيهات الحرجة.", en: "Start with the status indicators, then review critical alerts." },
    { ar: "الوضع التجريبي يعرض بيانات اصطناعية فقط ولا يتصل بمرضى حقيقيين.", en: "Demo mode shows synthetic data only and never connects to real patients." },
  ],
  "/patients": [
    { ar: "استخدم البحث قبل إنشاء سجل جديد لتقليل التكرار.", en: "Search before creating a record to reduce duplicates." },
    { ar: "لا تُدخل رقمًا وطنيًا حقيقيًا في وضع العرض التجريبي.", en: "Never enter a real national ID in demo mode." },
  ],
  "/results": [
    { ar: "لا يمكن اعتماد نتيجة قبل اكتمال دورة العينة والصلاحيات المطلوبة.", en: "A result cannot be validated before the sample workflow and permissions are complete." },
    { ar: "كل تغيير سريري يجب أن يترك أثرًا تدقيقيًا قابلًا للتتبع.", en: "Every clinical change must leave a traceable audit record." },
  ],
};

export function GuideAssistant() {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const { locale } = useLocale();
  const { demoMode } = useAuth();
  const isArabic = locale === "ar";
  const tips = useMemo(
    () => routeTips[location.pathname] ?? [
      { ar: "يمكنك التنقل من القائمة الجانبية، وسأعرض إرشادات مرتبطة بالصفحة عند توفرها.", en: "Use the sidebar to navigate; page-specific guidance appears when available." },
      { ar: "إذا احتجت مساعدة، ابدأ بقراءة حالة النظام والتنبيهات قبل تنفيذ أي كتابة.", en: "When unsure, review system status and alerts before performing a write." },
    ],
    [location.pathname],
  );

  return (
    <aside className="fixed bottom-[calc(5.5rem+env(safe-area-inset-bottom))] end-3 z-50 sm:bottom-5 sm:end-5" dir={isArabic ? "rtl" : "ltr"} aria-live="polite">
      {open && (
        <section id="gula-guide-panel" className="mb-3 w-[min(22rem,calc(100vw-2rem))] rounded-2xl border border-primary/20 bg-card p-4 shadow-xl" aria-label={isArabic ? "المساعد الإرشادي" : "Guide assistant"}>
          <div className="mb-3 flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-foreground">{isArabic ? "مساعد GULA" : "GULA Guide"}</p>
              <p className="mt-1 text-xs text-muted-foreground">{isArabic ? "إرشادات محلية لا ترسل بياناتك للخارج" : "Local guidance; your data is not sent anywhere"}</p>
            </div>
            <button className="rounded-lg p-1 text-muted-foreground hover:bg-muted" onClick={() => setOpen(false)} aria-label={isArabic ? "إغلاق" : "Close"}>
              <X className="h-4 w-4" />
            </button>
          </div>
          {demoMode && (
            <div className="mb-3 flex items-center gap-2 rounded-xl bg-amber-500/10 px-3 py-2 text-xs text-amber-700 dark:text-amber-300">
              <ShieldCheck className="h-4 w-4 shrink-0" />
              <span>{isArabic ? "وضع تجريبي: البيانات اصطناعية ومعزولة" : "Demo mode: synthetic, isolated data"}</span>
            </div>
          )}
          <ol className="space-y-3 text-sm leading-6 text-foreground">
            {tips.map((tip, index) => (
              <li key={`${location.pathname}-${index}`} className="flex gap-2">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">{index + 1}</span>
                <span>{isArabic ? tip.ar : tip.en}</span>
              </li>
            ))}
          </ol>
          <div className="mt-4 flex items-center justify-between border-t pt-3 text-xs text-muted-foreground">
            <span>{isArabic ? "المسار الحالي" : "Current route"}: {location.pathname}</span>
            {isArabic ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </div>
        </section>
      )}
      <button
        className="flex min-h-11 items-center gap-2 rounded-full bg-primary px-4 py-3 text-sm font-medium text-primary-foreground shadow-lg transition hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-controls="gula-guide-panel"
      >
        <HelpCircle className="h-5 w-5" />
        <span>{isArabic ? "المساعد" : "Guide"}</span>
      </button>
    </aside>
  );
}
