export type LegacyRouteRule = {
  target?: string;
  title: string;
  rationale: string;
};

export type FrontendSurface = LegacyRouteRule & {
  id: string;
  sourcePath: string;
  entryPath: string;
  status: "unified" | "bridge" | "pending_contract";
};

/**
 * سجل المصادر الأمامية التي تدخل خطة التوحيد. لا يعني وجود تطبيق في السجل
 * أن تدفقه مفعل؛ فحالة pending_contract تبقيه في الجسر الانتقالي إلى أن
 * يثبت العقد والصلاحية والسياق المكافئ داخل frontend-v3.
 */
export const frontendSurfaceCatalog: readonly FrontendSurface[] = [
  {
    id: "frontend-v2",
    sourcePath: "frontend-v2",
    entryPath: "/legacy",
    status: "bridge",
    title: "واجهة الإصدار الثاني",
    rationale: "تُعالج مساراتها المثبتة عبر جسر التوافق داخل frontend-v3.",
  },
  {
    id: "gula-web-suite",
    sourcePath: "apps/gula-web-suite",
    entryPath: "/web-suite",
    status: "pending_contract",
    title: "حزمة الويب العامة",
    rationale: "تحتاج نقاط الدخول العامة إلى مكافئات عقود وتوجيه مثبتة قبل التحويل.",
  },
  {
    id: "citizen",
    sourcePath: "platform/apps/citizen",
    entryPath: "/citizen",
    status: "unified",
    target: "/citizen",
    title: "مساحة المواطن",
    rationale: "يوفر frontend-v3 مساحة المواطن مع حارس الدور المعتمد.",
  },
  {
    id: "doctor",
    sourcePath: "platform/apps/doctor",
    entryPath: "/doctor",
    status: "pending_contract",
    title: "مساحة الطبيب",
    rationale: "تحتاج تدفقات الطبيب السريرية إلى مكافئات عقود وصلاحيات مثبتة قبل التحويل داخل frontend-v3.",
  },
  {
    id: "hospital",
    sourcePath: "platform/apps/hospital",
    entryPath: "/hospital",
    status: "unified",
    target: "/hospital",
    title: "مساحة المستشفى",
    rationale: "يوفر frontend-v3 مساحة مستشفى محمية بالأدوار الإدارية المعتمدة.",
  },
  {
    id: "laboratory",
    sourcePath: "platform/apps/laboratory",
    entryPath: "/laboratory",
    status: "unified",
    target: "/dashboard",
    title: "مساحة المختبر",
    rationale: "تعرض لوحة المختبر الموحدة حالة الحوكمة ولا تفعّل قراءة نطاقية دون سياق منشأة مثبت.",
  },
  {
    id: "ministry",
    sourcePath: "platform/apps/ministry",
    entryPath: "/ministry",
    status: "unified",
    target: "/national-data",
    title: "مساحة الوزارة",
    rationale: "يوفر frontend-v3 سطح البيانات الوطنية بحارس الأدوار الوزارية.",
  },
  {
    id: "nurse",
    sourcePath: "platform/apps/nurse",
    entryPath: "/nurse",
    status: "pending_contract",
    title: "مساحة التمريض",
    rationale: "تحتاج تدفقات التمريض السريرية إلى مكافئات عقود وصلاحيات مثبتة قبل التحويل داخل frontend-v3.",
  },
  {
    id: "pharmacy",
    sourcePath: "platform/apps/pharmacy",
    entryPath: "/pharmacy",
    status: "unified",
    target: "/pharmacy",
    title: "مساحة الصيدلية",
    rationale: "يوفر frontend-v3 مساحة صيدلية محمية بالأدوار الإدارية المعتمدة.",
  },
  {
    id: "radiology",
    sourcePath: "platform/apps/radiology",
    entryPath: "/radiology",
    status: "pending_contract",
    title: "مساحة الأشعة",
    rationale: "تحتاج تدفقات الأشعة إلى عقود DICOM وصلاحيات مثبتة قبل التحويل داخل frontend-v3.",
  },
] as const;

export const specialtyEntrypoints = Object.fromEntries(
  frontendSurfaceCatalog
    .filter((surface) => surface.id !== "frontend-v2")
    .map((surface) => [surface.entryPath, surface]),
) as Record<string, FrontendSurface>;
