export const ROUTES = {
  LOGIN: '/login',
  DASHBOARD: '/dashboard',
  SAMPLE_COLLECTION: '/sample-collection',
  RECEIVING: '/receiving',
  SAMPLE_TRACKING: '/sample-tracking',
  QUALITY_CONTROL: '/quality-control',
  RESULT_VALIDATION: '/result-validation',
  AUTOVERIFICATION: '/autoverification',
  MICROBIOLOGY: '/microbiology',
  MOLECULAR: '/molecular',
  BLOOD_BANK: '/blood-bank',
  HISTOPATHOLOGY: '/histopathology',
  ANALYZER_INTEGRATION: '/analyzer-integration',
  BARCODE_PRINTING: '/barcode-printing',
  REPORTS: '/reports',
  INVENTORY: '/inventory',
  WORKLIST: '/worklist',
  INSTRUMENT_MONITOR: '/instrument-monitor',
  OFFLINE_MODE: '/offline-mode',
  SETTINGS: '/settings',
  AUDIT_LOG: '/audit-log',
} as const;

export type RouteKey = keyof typeof ROUTES;

export const NAV_ITEMS = [
  { id: 'dashboard', label: 'لوحة المعلومات', path: ROUTES.DASHBOARD, icon: 'LayoutDashboard', section: 'main' },
  { id: 'worklist', label: 'قائمة العمل', path: ROUTES.WORKLIST, icon: 'ListChecks', section: 'workflow' },
  { id: 'sample-collection', label: 'جمع العينات', path: ROUTES.SAMPLE_COLLECTION, icon: 'Syringe', section: 'workflow' },
  { id: 'receiving', label: 'استلام العينات', path: ROUTES.RECEIVING, icon: 'Package', section: 'workflow' },
  { id: 'sample-tracking', label: 'تتبع العينات', path: ROUTES.SAMPLE_TRACKING, icon: 'Search', section: 'workflow' },
  { id: 'result-validation', label: 'التحقق من النتائج', path: ROUTES.RESULT_VALIDATION, icon: 'FileCheck', section: 'workflow' },
  { id: 'autoverification', label: 'التحقق الآلي', path: ROUTES.AUTOVERIFICATION, icon: 'Bot', section: 'workflow' },
  { id: 'quality-control', label: 'مراقبة الجودة', path: ROUTES.QUALITY_CONTROL, icon: 'ShieldCheck', section: 'quality' },
  { id: 'microbiology', label: 'الأحياء الدقيقة', path: ROUTES.MICROBIOLOGY, icon: 'FlaskConical', section: 'specialty' },
  { id: 'molecular', label: 'التشخيص الجزيئي', path: ROUTES.MOLECULAR, icon: 'Dna', section: 'specialty' },
  { id: 'blood-bank', label: 'بنك الدم', path: ROUTES.BLOOD_BANK, icon: 'Droplets', section: 'specialty' },
  { id: 'histopathology', label: 'الأنسجة المرضية', path: ROUTES.HISTOPATHOLOGY, icon: 'Microscope', section: 'specialty' },
  { id: 'analyzer-integration', label: 'ربط الأجهزة', path: ROUTES.ANALYZER_INTEGRATION, icon: 'Cpu', section: 'instruments' },
  { id: 'instrument-monitor', label: 'مراقبة الأجهزة', path: ROUTES.INSTRUMENT_MONITOR, icon: 'Activity', section: 'instruments' },
  { id: 'inventory', label: 'المخزون', path: ROUTES.INVENTORY, icon: 'Package', section: 'admin' },
  { id: 'reports', label: 'التقارير', path: ROUTES.REPORTS, icon: 'BarChart3', section: 'admin' },
  { id: 'barcode-printing', label: 'طباعة الباركود', path: ROUTES.BARCODE_PRINTING, icon: 'Printer', section: 'admin' },
  { id: 'offline-mode', label: 'الوضع غير المتصل', path: ROUTES.OFFLINE_MODE, icon: 'WifiOff', section: 'system' },
  { id: 'audit-log', label: 'سجل التدقيق', path: ROUTES.AUDIT_LOG, icon: 'ScrollText', section: 'system' },
  { id: 'settings', label: 'الإعدادات', path: ROUTES.SETTINGS, icon: 'Settings', section: 'system' },
] as const;

export const SIDEBAR_SECTIONS = [
  {
    id: 'main',
    title: 'الرئيسية',
    items: NAV_ITEMS.filter(i => i.section === 'main').map(i => ({ id: i.id, label: i.label, path: i.path })),
  },
  {
    id: 'workflow',
    title: 'سير العمل',
    items: NAV_ITEMS.filter(i => i.section === 'workflow').map(i => ({ id: i.id, label: i.label, path: i.path })),
  },
  {
    id: 'quality',
    title: 'الجودة',
    items: NAV_ITEMS.filter(i => i.section === 'quality').map(i => ({ id: i.id, label: i.label, path: i.path })),
  },
  {
    id: 'specialty',
    title: 'التخصصات',
    items: NAV_ITEMS.filter(i => i.section === 'specialty').map(i => ({ id: i.id, label: i.label, path: i.path })),
  },
  {
    id: 'instruments',
    title: 'الأجهزة',
    items: NAV_ITEMS.filter(i => i.section === 'instruments').map(i => ({ id: i.id, label: i.label, path: i.path })),
  },
  {
    id: 'admin',
    title: 'الإدارة',
    items: NAV_ITEMS.filter(i => i.section === 'admin').map(i => ({ id: i.id, label: i.label, path: i.path })),
  },
  {
    id: 'system',
    title: 'النظام',
    items: NAV_ITEMS.filter(i => i.section === 'system').map(i => ({ id: i.id, label: i.label, path: i.path })),
  },
];
