import type { SidebarSection } from '@gula/ui-platform';

export const ROUTES = {
  LOGIN: '/login',
  DASHBOARD: '/dashboard',
  MEDICATIONS: '/medications',
  VITALS: '/vitals',
  WARD: '/ward',
  ADMISSIONS: '/admissions',
  DISCHARGE: '/discharge',
  BEDSIDE: '/bedside',
  BARCODE: '/barcode',
  QR_VERIFICATION: '/qr-verification',
  OFFLINE: '/offline',
  CARE_PLAN: '/care-plan',
  SHIFT_HANDOVER: '/shift-handover',
  TASKS: '/tasks',
  PATIENT_ROUND: '/patient-round',
  SETTINGS: '/settings',
} as const;

export const SIDEBAR_SECTIONS: SidebarSection[] = [
  {
    id: 'main',
    title: 'القائمة الرئيسية',
    items: [
      { id: 'dashboard', label: 'لوحة المعلومات', href: ROUTES.DASHBOARD, icon: 'LayoutDashboard' },
      { id: 'tasks', label: 'المهام التمريضية', href: ROUTES.TASKS, icon: 'ClipboardList' },
      { id: 'medications', label: 'الأدوية', href: ROUTES.MEDICATIONS, icon: 'Pill' },
      { id: 'vitals', label: 'العلامات الحيوية', href: ROUTES.VITALS, icon: 'Heart' },
    ],
  },
  {
    id: 'patients',
    title: 'إدارة المرضى',
    items: [
      { id: 'ward', label: 'الجناح', href: ROUTES.WARD, icon: 'Building' },
      { id: 'admissions', label: 'قبول المرضى', href: ROUTES.ADMISSIONS, icon: 'UserPlus' },
      { id: 'discharge', label: 'خروج المرضى', href: ROUTES.DISCHARGE, icon: 'UserMinus' },
      { id: 'care-plan', label: 'خطة الرعاية', href: ROUTES.CARE_PLAN, icon: 'FileText' },
    ],
  },
  {
    id: 'clinical-verification',
    title: 'التحقق السريري',
    items: [
      { id: 'bedside', label: 'التحقق بجانب السرير', href: ROUTES.BEDSIDE, icon: 'Scan' },
      { id: 'barcode', label: 'مسح الباركود', href: ROUTES.BARCODE, icon: 'Barcode' },
      { id: 'qr-verification', label: 'التحقق بـ QR', href: ROUTES.QR_VERIFICATION, icon: 'QrCode' },
      { id: 'patient-round', label: 'جولة المرضى', href: ROUTES.PATIENT_ROUND, icon: 'Stethoscope' },
    ],
  },
  {
    id: 'reports',
    title: 'التقارير',
    items: [
      { id: 'shift-handover', label: 'تسليم الوردية', href: ROUTES.SHIFT_HANDOVER, icon: 'ArrowRightLeft' },
      { id: 'offline', label: 'وضع عدم الاتصال', href: ROUTES.OFFLINE, icon: 'WifiOff' },
      { id: 'settings', label: 'الإعدادات', href: ROUTES.SETTINGS, icon: 'Settings' },
    ],
  },
];

export function getWardArabic(ward: string): string {
  const wards: Record<string, string> = {
    emergency: 'الطوارئ',
    icu: 'العناية المركزة',
    nicu: 'عناية الأطفال حديثي الولادة',
    cardiology: 'القلب',
    pediatrics: 'الأطفال',
    maternity: 'الولادة',
    surgery: 'الجراحة',
    orthopedics: 'العظام',
    neurology: 'الأعصاب',
    general: 'الداخلي العام',
  };
  return wards[ward] || ward;
}

export function getPriorityArabic(p: string): string {
  const map: Record<string, string> = { low: 'منخفض', medium: 'متوسط', high: 'عالٍ', urgent: 'عاجل', stat: 'فوري' };
  return map[p] || p;
}

export function getStatusArabic(s: string): string {
  const map: Record<string, string> = {
    pending: 'معلق', 'in-progress': 'قيد التنفيذ', completed: 'مكتمل',
    cancelled: 'ملغي', delayed: 'متأخر', verified: 'تم التحقق',
  };
  return map[s] || s;
}

export function getShiftArabic(s: string): string {
  const map: Record<string, string> = { morning: 'صباحية', evening: 'مسائية', night: 'ليلية' };
  return map[s] || s;
}
