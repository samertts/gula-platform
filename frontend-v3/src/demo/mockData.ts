import type { DemoProfileId } from "./profiles";

export interface DemoRow {
  label: string;
  labelEn: string;
  value: string;
  valueEn?: string;
}

export interface DemoCard {
  title: string;
  titleEn: string;
  rows: DemoRow[];
}

export interface DemoStat {
  label: string;
  labelEn: string;
  value: string;
}

export interface DemoProfileView {
  profile: DemoProfileId;
  title: string;
  titleEn: string;
  subtitle: string;
  subtitleEn: string;
  stats: DemoStat[];
  cards: DemoCard[];
}

/**
 * Synthetic, clearly-marked demo data only. No real patients, national IDs,
 * phone numbers, medical records or laboratory results are used.
 */
export const DEMO_VIEWS: Record<DemoProfileId, DemoProfileView> = {
  citizen: {
    profile: "citizen",
    title: "لوحة المواطن التجريبية",
    titleEn: "Citizen Demo Dashboard",
    subtitle: "عرض تجريبي للخدمات المتاحة للمواطن",
    subtitleEn: "Preview of citizen-facing services",
    stats: [
      { label: "مواعيد قادمة", labelEn: "Upcoming appointments", value: "2" },
      { label: "سجلات صحية", labelEn: "Health records", value: "4" },
      { label: "خدمات متاحة", labelEn: "Available services", value: "6" },
    ],
    cards: [
      {
        title: "المواعيد القادمة (بيانات تجريبية)",
        titleEn: "Upcoming appointments (demo)",
        rows: [
          { label: "DEMO-APT-101", labelEn: "Demo appointment 1", value: "2026-08-12 10:00" },
          { label: "DEMO-APT-102", labelEn: "Demo appointment 2", value: "2026-08-15 12:30" },
        ],
      },
      {
        title: "المعلومات الصحية (بيانات تجريبية)",
        titleEn: "Health information (demo)",
        rows: [
          { label: "فصيلة الدم", labelEn: "Blood group", value: "O+ (تجريبي)" },
          { label: "الحساسية", labelEn: "Allergies", value: "لا توجد (تجريبي)" },
          { label: "الأمراض المزمنة", labelEn: "Chronic conditions", value: "لا توجد (تجريبي)" },
        ],
      },
      {
        title: "الخدمات (عرض تجريبي)",
        titleEn: "Services preview",
        rows: [
          { label: "نتائج المختبر", labelEn: "Laboratory results", value: "متاح" },
          { label: "حجز المواعيد", labelEn: "Appointment booking", value: "متاح" },
          { label: "التوعية الصحية", labelEn: "Health education", value: "متاح" },
        ],
      },
    ],
  },
  doctor: {
    profile: "doctor",
    title: "لوحة الطبيب التجريبية",
    titleEn: "Doctor Demo Dashboard",
    subtitle: "عرض تجريبي لرحلة المريض والمواعيد والنظرة السريرية",
    subtitleEn: "Preview of patient journey, appointments and clinical overview",
    stats: [
      { label: "مرضى اليوم (تجريبي)", labelEn: "Demo patients today", value: "8" },
      { label: "مواعيد (تجريبي)", labelEn: "Demo appointments", value: "12" },
      { label: "نتائج بانتظار المراجعة", labelEn: "Results awaiting review", value: "3" },
    ],
    cards: [
      {
        title: "رحلة المريض (بيانات تجريبية)",
        titleEn: "Patient journey (demo)",
        rows: [
          { label: "مريض تجريبي 001", labelEn: "Demo Patient 001", value: "متابعة — Dr. Demo Physician" },
          { label: "مريض تجريبي 002", labelEn: "Demo Patient 002", value: "زيارة أولى" },
        ],
      },
      {
        title: "المواعيد (بيانات تجريبية)",
        titleEn: "Appointments (demo)",
        rows: [
          { label: "DEMO-APT-201", labelEn: "Demo appointment 1", value: "العيادة أ — 09:00" },
          { label: "DEMO-APT-202", labelEn: "Demo appointment 2", value: "العيادة أ — 10:30" },
        ],
      },
      {
        title: "النظرة السريرية (قيم تجريبية)",
        titleEn: "Clinical overview (demo values)",
        rows: [
          { label: "غلوكوز الدم", labelEn: "Blood glucose", value: "5.4 mmol/L", valueEn: "5.4 mmol/L (demo)" },
          { label: "هيموغلوبين", labelEn: "Hemoglobin", value: "13.2 g/dL", valueEn: "13.2 g/dL (demo)" },
          { label: "ضغط الدم", labelEn: "Blood pressure", value: "120/80 mmHg", valueEn: "120/80 mmHg (demo)" },
        ],
      },
    ],
  },
  lab_staff: {
    profile: "lab_staff",
    title: "لوحة المختبر التجريبية",
    titleEn: "Laboratory Demo Dashboard",
    subtitle: "عرض تجريبي للطلبات والعينات والنتائج",
    subtitleEn: "Preview of orders, specimens and results",
    stats: [
      { label: "طلبات اليوم (تجريبي)", labelEn: "Demo orders today", value: "24" },
      { label: "عينات (تجريبي)", labelEn: "Demo specimens", value: "18" },
      { label: "نتائج مدققة (تجريبي)", labelEn: "Demo validated results", value: "22" },
      { label: "تنبيهات حرجة (تجريبي)", labelEn: "Demo critical alerts", value: "1" },
    ],
    cards: [
      {
        title: "الطلبات (بيانات تجريبية)",
        titleEn: "Orders (demo)",
        rows: [
          { label: "DEMO-ORD-001", labelEn: "Demo order 1", value: "مريض تجريبي 001 — CBC" },
          { label: "DEMO-ORD-002", labelEn: "Demo order 2", value: "مريض تجريبي 002 — Glucose" },
          { label: "DEMO-ORD-003", labelEn: "Demo order 3", value: "مريض تجريبي 003 — Lipid" },
        ],
      },
      {
        title: "سير عمل العينات (بيانات تجريبية)",
        titleEn: "Specimen workflow (demo)",
        rows: [
          { label: "DEMO-SPL-001", labelEn: "Demo specimen 1", value: "تم التحصيل" },
          { label: "DEMO-SPL-002", labelEn: "Demo specimen 2", value: "قيد التحليل" },
          { label: "DEMO-SPL-003", labelEn: "Demo specimen 3", value: "تم التحليل" },
        ],
      },
      {
        title: "النتائج (قيم تجريبية)",
        titleEn: "Results (demo values)",
        rows: [
          { label: "WBC", labelEn: "WBC", value: "6.1 ×10⁹/L", valueEn: "6.1 x10^9/L (demo)" },
          { label: "Hb", labelEn: "Hb", value: "13.2 g/dL", valueEn: "13.2 g/dL (demo)" },
          { label: "Glucose", labelEn: "Glucose", value: "5.4 mmol/L", valueEn: "5.4 mmol/L (demo)" },
        ],
      },
    ],
  },
  nurse: {
    profile: "nurse",
    title: "لوحة التمريض التجريبية",
    titleEn: "Nursing Demo Dashboard",
    subtitle: "عرض تجريبي لتدفق المرضى والعلامات الحيوية",
    subtitleEn: "Preview of patient flow and vitals",
    stats: [
      { label: "مرضى مقيمون (تجريبي)", labelEn: "Demo admitted patients", value: "6" },
      { label: "علامات حيوية مستحقة", labelEn: "Vitals due", value: "4" },
      { label: "أدوية (تجريبي)", labelEn: "Demo medications", value: "9" },
    ],
    cards: [
      {
        title: "تدفق المرضى (بيانات تجريبية)",
        titleEn: "Patient flow (demo)",
        rows: [
          { label: "جناح 1 — سرير 1", labelEn: "Ward 1 — Bed 1", value: "مستقر" },
          { label: "جناح 1 — سرير 2", labelEn: "Ward 1 — Bed 2", value: "تحت الملاحظة" },
          { label: "جناح 2 — سرير 1", labelEn: "Ward 2 — Bed 1", value: "جاهز للخروج" },
        ],
      },
      {
        title: "العلامات الحيوية (قيم تجريبية)",
        titleEn: "Vitals (demo values)",
        rows: [
          { label: "نبض", labelEn: "Pulse", value: "72 /min", valueEn: "72 /min (demo)" },
          { label: "حرارة", labelEn: "Temperature", value: "36.8 °C", valueEn: "36.8 °C (demo)" },
          { label: "تشبع الأكسجين", labelEn: "SpO2", value: "98%", valueEn: "98% (demo)" },
        ],
      },
    ],
  },
  health_admin: {
    profile: "health_admin",
    title: "لوحة الإدارة الصحية التجريبية",
    titleEn: "Health Administration Demo Dashboard",
    subtitle: "عرض تجريبي للوحة التنظيمية والإحصائيات",
    subtitleEn: "Preview of organizational dashboard and statistics",
    stats: [
      { label: "منشآت (تجريبي)", labelEn: "Demo facilities", value: "3" },
      { label: "موظفون (تجريبي)", labelEn: "Demo staff", value: "12" },
      { label: "فحوصات شهرية (تجريبي)", labelEn: "Demo monthly tests", value: "180" },
      { label: "الامتثال", labelEn: "Compliance", value: "100%" },
    ],
    cards: [
      {
        title: "المنشآت (بيانات تجريبية)",
        titleEn: "Facilities (demo)",
        rows: [
          { label: "GULA Demo Hospital", labelEn: "GULA Demo Hospital", value: "نشطة" },
          { label: "Demo Central Laboratory", labelEn: "Demo Central Laboratory", value: "نشطة" },
          { label: "GULA Demo PHC", labelEn: "GULA Demo PHC", value: "نشطة" },
        ],
      },
      {
        title: "الإحصائيات (قيم تجريبية)",
        titleEn: "Statistics (demo values)",
        rows: [
          { label: "متوسط زمن الإنجاز", labelEn: "Avg turnaround", value: "3.2 ساعة", valueEn: "3.2 hours (demo)" },
          { label: "فحوصات اليوم", labelEn: "Tests today", value: "12 (تجريبي)" },
          { label: "الأشغال", labelEn: "Occupancy", value: "71% (تجريبي)" },
        ],
      },
    ],
  },
};
