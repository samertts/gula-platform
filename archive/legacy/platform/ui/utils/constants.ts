export const APP_NAME = 'GULA Platform';
export const APP_VERSION = '2.1.0';
export const COMPANY_NAME = 'GULA Health';

export const WINGS = [
  'citizen',
  'doctor',
  'lab',
  'admin',
  'ministry',
  'researcher',
  'regulator',
  'system',
] as const;
export type Wing = typeof WINGS[number];

export const ROLES = [
  'physician',
  'technician',
  'admin',
  'master_admin',
  'citizen',
  'regulator',
  'researcher',
  'lab_admin',
  'pathologist',
  'ministry_admin',
  'ministry_analyst',
  'ministry_inspector',
  'auditor',
  'integration_service',
] as const;
export type Role = typeof ROLES[number];

export const ORDER_STATUSES = [
  'pending',
  'received',
  'processing',
  'completed',
  'released',
] as const;
export type OrderStatus = typeof ORDER_STATUSES[number];

export const PRIORITIES = ['routine', 'urgent', 'stat'] as const;
export type Priority = typeof PRIORITIES[number];

export const SAMPLE_STATUSES = [
  'collected',
  'in_lab',
  'processing',
  'verified',
  'delivered',
] as const;
export type SampleStatus = typeof SAMPLE_STATUSES[number];

export const BLOOD_TYPES = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'] as const;
export type BloodType = typeof BLOOD_TYPES[number];

export const GENDERS = ['male', 'female'] as const;
export type Gender = typeof GENDERS[number];

export const CONSENT_DURATIONS = ['1_day', '1_week', '1_month', 'permanent'] as const;
export type ConsentDuration = typeof CONSENT_DURATIONS[number];

export const CONSENT_SCOPES = ['full', 'limited', 'emergency'] as const;
export type ConsentScope = typeof CONSENT_SCOPES[number];

export const VERIFICATION_LEVELS = ['Level_1', 'Level_2', 'Level_3'] as const;
export type VerificationLevel = typeof VERIFICATION_LEVELS[number];

export const EVENT_TYPES = [
  'critical_alert',
  'expiring_reagent',
  'consent_granted',
  'consent_revoked',
  'lab_result_ready',
  'inventory_low',
  'system_update',
] as const;
export type EventType = typeof EVENT_TYPES[number];

export const LANGUAGES = ['EN', 'AR', 'KU', 'TR', 'SY'] as const;
export type LanguageCode = typeof LANGUAGES[number];

export const RTL_LANGUAGES: LanguageCode[] = ['AR', 'KU'];

export const ROUTES = {
  CITIZEN: {
    DASHBOARD: '/citizen/dashboard',
    PROFILE: '/citizen/profile',
    RESULTS: '/citizen/results',
    MEDICATIONS: '/citizen/medications',
    APPOINTMENTS: '/citizen/appointments',
    FAMILY: '/citizen/family',
    SECURITY: '/citizen/security',
  },
  LAB: {
    DASHBOARD: '/lab/dashboard',
    QUEUE: '/lab/queue',
    SAMPLES: '/lab/samples',
    QC: '/lab/qc',
    DEVICES: '/lab/devices',
  },
  DOCTOR: {
    DASHBOARD: '/',
    PATIENTS: '/patients',
    APPOINTMENTS: '/appointments',
    INTELLIGENCE: '/intelligence',
  },
  MINISTRY: {
    DASHBOARD: '/ministry/dashboard',
    ANALYTICS: '/ministry/analytics',
    INSPECTIONS: '/ministry/inspections',
    REGISTRY: '/ministry/registry',
  },
  ADMIN: {
    AUDIT: '/admin/audit',
    ARCHITECTURE: '/admin/architecture',
    INTEGRATIONS: '/admin/integrations',
    INFRASTRUCTURE: '/admin/infrastructure',
  },
  RESEARCH: {
    ANALYTICS: '/research/analytics',
    POPULATION: '/research/population',
  },
  SETTINGS: '/settings',
} as const;

export const STORAGE_KEYS = {
  THEME_MODE: 'gula-theme-mode',
  DIRECTION: 'gula-direction',
  LOCALE: 'gula-locale',
  PINNED_NAV: 'gula_pinned_nav',
  LOW_BANDWIDTH: 'gula_low_bandwidth',
  CLINICAL_MODE: 'clinical_mode',
} as const;

export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 10,
  PAGE_SIZE_OPTIONS: [10, 25, 50, 100],
} as const;

export const DEBOUNCE = {
  SEARCH: 300,
  SAVE: 500,
  RESIZE: 150,
} as const;
