export type LegacyRouteRule = {
  target?: string;
  title: string;
  rationale: string;
};

export type FrontendSurface = LegacyRouteRule & {
  id: string;
  sourcePath: string;
  entryPath: string;
  status: "unified" | "bridge";
};

/**
 * سجل المصادر الأمامية التي تدخل خطة التوحيد. لا يعني وجود تطبيق في السجل
 * أن تدفقه مفعل؛ فحالة bridge تنقله إلى جسر انتقال آمن داخل frontend-v3
 * إلى أن يثبت العقد والصلاحية والسياق المكافئ.
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
    status: "bridge",
    title: "حزمة الويب العامة",
    rationale: "يظهر مكافئ انتقال آمن داخل frontend-v3 إلى أن تثبت عقود نقاط الدخول العامة وتوجيهاتها.",
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
    status: "bridge",
    title: "مساحة الطبيب",
    rationale: "تظهر مساحة انتقالية آمنة داخل frontend-v3؛ لا تُفعّل تدفقات الطبيب قبل إثبات العقود والصلاحيات المكافئة.",
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
    status: "bridge",
    title: "مساحة التمريض",
    rationale: "تظهر مساحة انتقالية آمنة داخل frontend-v3؛ لا تُفعّل تدفقات التمريض قبل إثبات العقود والصلاحيات المكافئة.",
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
    status: "bridge",
    title: "مساحة الأشعة",
    rationale: "تظهر مساحة انتقالية آمنة داخل frontend-v3؛ لا تُفعّل تدفقات الأشعة قبل إثبات عقود DICOM والصلاحيات المكافئة.",
  },
] as const;

export const specialtyEntrypoints = Object.fromEntries(
  frontendSurfaceCatalog
    .filter((surface) => surface.id !== "frontend-v2")
    .map((surface) => [surface.entryPath, surface]),
) as Record<string, FrontendSurface>;
