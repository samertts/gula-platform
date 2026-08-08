export const APP_NAME = 'GULA صحي';
export const APP_NAME_EN = 'GULA Health';
export const APP_VERSION = '2.1.0';
export const COMPANY_NAME = 'GULA Health';

export const STORAGE_KEYS = {
  AUTH_TOKEN: 'gula_citizen_token',
  REFRESH_TOKEN: 'gula_citizen_refresh',
  USER_DATA: 'gula_citizen_user',
  OFFLINE_DATA: 'gula_offline_data',
  SYNC_TIMESTAMP: 'gula_sync_ts',
  THEME_MODE: 'gula_theme_mode',
  LOCALE: 'gula_locale',
  CONSENT_CACHE: 'gula_consent_cache',
  FAMILY_CACHE: 'gula_family_cache',
  NOTIFICATION_SETTINGS: 'gula_notif_settings',
  ONBOARDING_COMPLETE: 'gula_onboarding_done',
  EMERGENCY_CONTACTS: 'gula_emergency_contacts',
  LAST_KNOWN_LOCATION: 'gula_last_location',
} as const;

export const VERIFICATION_LEVELS = {
  LEVEL_1: { key: 'Level_1', label: 'مستوى 1 - أساسي', labelEn: 'Level 1 - Basic' },
  LEVEL_2: { key: 'Level_2', label: 'مستوى 2 - موثق', labelEn: 'Level 2 - Documented' },
  LEVEL_3: { key: 'Level_3', label: 'مستوى 3 - بيومتري', labelEn: 'Level 3 - Biometric' },
} as const;

export const CONSENT_DURATIONS = {
  ONE_DAY: { key: '1_day', label: 'يوم واحد', labelEn: '1 Day' },
  ONE_WEEK: { key: '1_week', label: 'أسبوع', labelEn: '1 Week' },
  ONE_MONTH: { key: '1_month', label: 'شهر', labelEn: '1 Month' },
  PERMANENT: { key: 'permanent', label: 'دائم', labelEn: 'Permanent' },
} as const;

export const CONSENT_SCOPES = {
  FULL: { key: 'full', label: 'كامل', labelEn: 'Full' },
  LIMITED: { key: 'limited', label: 'محدود', labelEn: 'Limited' },
  EMERGENCY: { key: 'emergency', label: 'طوارئ', labelEn: 'Emergency' },
} as const;

export const BLOOD_TYPES = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'] as const;

export const GENDERS = [
  { key: 'male', label: 'ذكر', labelEn: 'Male' },
  { key: 'female', label: 'أنثى', labelEn: 'Female' },
] as const;

export const APPOINTMENT_TYPES = [
  { key: 'checkup', label: 'فحص دوري', labelEn: 'Checkup' },
  { key: 'consultation', label: 'استشارة', labelEn: 'Consultation' },
  { key: 'followup', label: 'متابعة', labelEn: 'Follow-up' },
  { key: 'emergency', label: 'طوارئ', labelEn: 'Emergency' },
  { key: 'lab_test', label: 'تحليل', labelEn: 'Lab Test' },
  { key: 'vaccination', label: 'تطعيم', labelEn: 'Vaccination' },
] as const;

export const APPOINTMENT_STATUSES = {
  SCHEDULED: { key: 'scheduled', label: 'مجدول', labelEn: 'Scheduled' },
  CONFIRMED: { key: 'confirmed', label: 'مؤكد', labelEn: 'Confirmed' },
  IN_PROGRESS: { key: 'in_progress', label: 'قيد التنفيذ', labelEn: 'In Progress' },
  COMPLETED: { key: 'completed', label: 'مكتمل', labelEn: 'Completed' },
  CANCELLED: { key: 'cancelled', label: 'ملغي', labelEn: 'Cancelled' },
  NO_SHOW: { key: 'no_show', label: 'لم يحضر', labelEn: 'No Show' },
} as const;

export const RESULT_FLAGS = {
  H: { key: 'H', label: 'مرتفع', labelEn: 'High', color: 'danger' },
  L: { key: 'L', label: 'منخفض', labelEn: 'Low', color: 'warning' },
  N: { key: 'N', label: 'طبيعي', labelEn: 'Normal', color: 'success' },
  C: { key: 'C', label: 'حرج', labelEn: 'Critical', color: 'danger' },
} as const;

export const SYNC_INTERVALS = {
  PRIORITY: 30000,
  STANDARD: 120000,
  BACKGROUND: 300000,
} as const;

export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 10,
  PAGE_SIZE_OPTIONS: [5, 10, 20, 50],
} as const;

export const NATIONAL_ID_LENGTH = 14;
export const PHONE_LENGTH = 11;
export const OTP_LENGTH = 6;
export const MAX_APPOINTMENTS_PER_DAY = 3;
export const EMERGENCY_NUMBER = '122';
