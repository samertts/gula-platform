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
  "/acute-care-operations": [
    { ar: "الفرز يحدد الأولوية ولا يساوي التشخيص؛ أي إجراء حرج يحتاج عقدًا خادميًا.", en: "Triage sets priority; it is not a diagnosis. Critical actions require a server contract." },
    { ar: "في Demo كل البلاغات والهويات والإسعافات اصطناعية ومعزولة.", en: "In Demo, incidents, identities, and ambulance workflows are synthetic and isolated." },
  ],
  "/ems": [
    { ar: "هذا alias آمن لبوابة الرعاية الحادة؛ لا تستخدم الصفحة واجهات EMS الخام.", en: "This is a safe alias for Acute Care; raw EMS endpoints are not used here." },
    { ar: "لا يقرر المرشد الوجهة أو الإرسال أو العلاج.", en: "The guide does not decide destination, dispatch, or treatment." },
  ],
  "/critical-care": [
    { ar: "قراءات ICU والأجهزة والـtelemetry محجوبة حتى تتوفر عقود نطاقية موثقة.", en: "ICU, device, and telemetry reads remain gated until scoped contracts exist." },
    { ar: "لا يعني وجود دور سريري أن كل مرضى العناية متاحون.", en: "A clinical role does not grant access to every critical-care patient." },
  ],
  "/hospital": [
    { ar: "بوابة المستشفى تقرأ فقط ما يعكسه الخادم ضمن مساحة العمل الحالية.", en: "The hospital workspace reads only what the server reflects for the current workspace." },
    { ar: "الإدخال والأسرة والعمليات والعناية والدم والخروج تحتاج عقودًا مستقلة.", en: "Admissions, beds, OR, ICU, blood, and discharge require independent contracts." },
  ],
  "/hospital-operations": [
    { ar: "ابدأ بنظرة المستشفى ثم اختر نطاقًا؛ لا يمنح التبويب صلاحية تنفيذ.", en: "Start with the hospital overview, then choose a scope; tabs never grant execution rights." },
    { ar: "الوصول الحي يتطلب تفعيل مساحة عمل أعادها الخادم.", en: "Live access requires activating a workspace returned by the server." },
  ],
  "/clinic-operations": [
    { ar: "Appointment وEncounter مساران مختلفان؛ لا تنشئ الواجهة زيارة سريرية محليًا.", en: "Appointment and Encounter are distinct; the UI never creates a local clinical visit." },
    { ar: "اعرض فقط المرضى والأوامر ضمن السياق المعاد من الخادم.", en: "Show only patients and orders within the server-reflected context." },
  ],
  "/lab-operations": [
    { ar: "لا تعتمد نتيجة قبل اكتمال العينة والصلاحية والتدقيق.", en: "Never validate a result before specimen, authorization, and audit requirements are complete." },
    { ar: "الوضع التجريبي لا يستدعي LIS أو محللًا حقيقيًا.", en: "Demo mode never calls a real LIS or analyzer." },
  ],
  "/radiology-operations": [
    { ar: "لا تعرض DICOM أو PACS أو تقريرًا موقّعًا قبل العقد المناسب.", en: "Do not expose DICOM, PACS, or signed reports without the proper contract." },
    { ar: "المعرّفات السريرية تُعرض بأدنى قدر لازم للسياق.", en: "Clinical identifiers are minimized to what the context requires." },
  ],
  "/pharmacy-operations": [
    { ar: "الصرف والإعطاء عمليتان مختلفتان؛ لا تحولهما الواجهة إلى زر واحد.", en: "Dispensing and administration are distinct; the UI never collapses them into one action." },
    { ar: "الأدوية الخاضعة للرقابة تحتاج تحققًا وسياسة خادمية متخصصة.", en: "Controlled medicines require specialized server-side verification and policy." },
  ],
  "/screen-by-screen": [
    { ar: "هذا معرض تصميم وتفاعل اصطناعي؛ لا يمثل ملفاً صحياً أو صلاحية حقيقية.", en: "This is a synthetic design and interaction gallery; it is not a real health record or permission." },
    { ar: "اختر الدور ثم الشاشة لمراجعة حالات loading وempty وgated وresponsive.", en: "Choose a role and screen to review loading, empty, gated, and responsive states." },
  ],
  "/golden-path": [
    { ar: "هذه خريطة جاهزية؛ لا نعلن نجاح الرحلة الذهبية قبل اكتمال العقود والاختبارات عبر المجالات.", en: "This is a readiness map; the Golden Path is not passed until cross-domain contracts and tests are complete." },
    { ar: "ابدأ بالهوية ومساحة العمل ثم تحقق من Patient Access قبل أي عملية سريرية.", en: "Start with identity and workspace, then verify Patient Access before any clinical operation." },
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
    <aside className="fixed bottom-[calc(5.5rem+env(safe-area-inset-bottom))] end-3 z-50 sm:bottom-5 sm:end-5" dir={isArabic ? "rtl" : "ltr"} aria-live="polite" data-assistant-state={open ? "responding" : "idle"}>
      {open && (
        <section id="gula-guide-panel" className="mb-3 w-[min(22rem,calc(100vw-2rem))] rounded-2xl border border-primary/20 bg-card p-4 shadow-xl" aria-label={isArabic ? "المساعد الإرشادي" : "Guide assistant"}>
          <div className="mb-3 flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-foreground">{isArabic ? "مساعد GULA" : "GULA Guide"}</p>
              <p className="mt-1 text-xs text-muted-foreground">{isArabic ? "مرشد محلي؛ لا يملك وصولًا مستقلاً إلى قاعدة البيانات" : "Local guide; no independent database access"}</p>
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
          <div className="mb-3 flex items-center justify-between gap-2 rounded-xl border border-emerald-200/80 bg-emerald-50/70 px-3 py-2 text-xs text-emerald-900 dark:border-emerald-900/50 dark:bg-emerald-950/20 dark:text-emerald-100"><span>{isArabic ? "الحالة: جاهز للإرشاد" : "State: ready to guide"}</span><span>{isArabic ? "محلي" : "Local"}</span></div>
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
        className="gula-touch-target gula-focus-ring flex min-h-11 items-center gap-2 rounded-full bg-primary px-4 py-3 text-sm font-medium text-primary-foreground shadow-lg transition hover:opacity-90"
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
