export interface User {
  id: number;
  name: string;
  email: string;
  role: string;
  role_level?: number;
  lab_id: number;
  lab_name?: string;
  province_id?: number | null;
  is_active: boolean;
  created_at?: string;
  created_by?: number | null;
}

export interface Lab {
  id: number;
  name: string;
  license_number?: string;
  lab_type?: string;
  director_name?: string;
  website?: string;
  city?: string;
  address?: string;
  phone?: string;
  is_active: boolean;
  created_at?: string;
  admin_email?: string;
  admin_name?: string;
  staff_count?: number;
  patient_count?: number;
  user_count?: number;
}

export interface Patient {
  id: number;
  health_id?: string;
  full_name: string;
  phone: string;
  birth_date?: string;
  gender?: string;
  email?: string;
  national_id_hash?: string;
  family_id_hash?: string;
  guardian_id?: number | null;
  lab_id: number;
  created_at?: string;
  updated_at?: string;
}

export interface LabOrder {
  id: number;
  patient_id: number;
  patient_name?: string;
  lab_id: number;
  doctor_name?: string;
  doctor_user_id?: number | null;
  status: string;
  validated_by?: number | null;
  validated_at?: string;
  locked_at?: string;
  created_at?: string;
  updated_at?: string;
  results_count?: number;
  results?: LabResult[];
  patient?: Patient;
  samples?: Sample[];
}

export interface LabResult {
  id: number;
  order_id: number;
  test_type_id?: number | null;
  test_name: string;
  test_code?: string;
  category?: string;
  value?: number | null;
  value_text?: string | null;
  unit?: string;
  normal_range_low?: number | null;
  normal_range_high?: number | null;
  flag?: string;
  is_critical?: boolean;
  is_abnormal?: boolean;
  status?: string;
  token?: string;
  result_token?: string;
  interpretation?: string | null;
  verified_by?: number | null;
  verified_at?: string;
  sample_barcode?: string;
  created_at?: string;
  order?: LabOrder;
  test_type?: TestType;
}

export interface Sample {
  id: number;
  barcode: string;
  order_id: number;
  sample_type: string;
  status: string;
  collected_by?: string;
  collection_time?: string;
  rejection_reason?: string;
  notes?: string;
  storage_location?: string;
  created_at?: string;
}

export interface TestType {
  id: number;
  code: string;
  name: string;
  name_ar: string;
  category: string;
  unit: string;
  normal_low?: number;
  normal_high?: number;
  normal_range_low?: number;
  normal_range_high?: number;
}

export interface TestProfile {
  test_name: string;
  unit?: string;
  normal_range_low?: number;
  normal_range_high?: number;
}

export interface AuditLog {
  id: number;
  action: string;
  resource_type: string;
  resource_id?: number | null;
  user_id?: number | null;
  user_role?: string;
  details?: string;
  ip_address?: string;
  created_at: string;
}

export interface NotificationRecord {
  order_id: number;
  total_views: number;
  first_viewed?: string;
  last_viewed?: string;
}

export interface CriticalAlert {
  id?: number;
  order_id: number;
  critical_tests: string[];
  token_prefix?: string;
  created_at?: string;
}

export interface QualityControl {
  id: number;
  test_code: string;
  level: string;
  expected_value: number;
  measured_value: number;
  sd?: number;
  unit?: string;
  instrument_name?: string;
  lot_number?: string;
  status: string;
  violation?: string;
  notes?: string;
  performed_by?: string;
  created_at?: string;
}

export interface DashboardData {
  greeting: string;
  patients: number;
  orders: number;
  tests: number;
  critical: number;
  today: { patients: number; orders: number; tests: number };
  this_week: { patients: number; orders: number; tests: number };
  abnormal_results: AbnormalResult[];
  recent_orders: RecentOrder[];
  lab_name?: string;
}

export interface AbnormalResult {
  patient_name: string;
  test_name: string;
  value: number;
  unit?: string;
  normal_range_low?: number;
  normal_range_high?: number;
  flag: string;
  date?: string;
  token?: string;
}

export interface RecentOrder {
  id: number;
  patient_name: string;
  status: string;
  test_count: number;
  date?: string;
}

export interface SubscriptionTier {
  id: string;
  name: string;
  name_ar: string;
  monthly_price_usd: number;
  limits: Record<string, number>;
  features: string[];
}

export interface SubscriptionInfo {
  lab_id: number;
  tier: string;
  deployment_mode?: string;
  security_level?: string;
  features: string[];
  limits: Record<string, number>;
}

export interface TrendData {
  days: number;
  series?: TrendPoint[];
  data_points?: number;
}

export interface TrendPoint {
  date?: string;
  orders?: number;
  tests?: number;
  critical_tests?: number;
  abnormal_tests?: number;
}

export interface FlagDistribution {
  days: number;
  total_results: number;
  distribution: Record<string, { count: number; percentage: number }>;
}

export interface StatsSummary {
  totals: {
    patients: number;
    orders: number;
    tests: number;
    critical_results: number;
    critical_rate_pct: number;
  };
  today: { orders: number; critical_results: number };
  this_week: { orders: number };
  this_month: { orders: number };
}

export interface HealthStatus {
  status: string;
  platform: string;
  platform_ar: string;
  version: string;
  environment: string;
  system_ready: boolean;
  database: string;
  degraded_mode: boolean;
  degradation_level: string;
}

export interface DeepHealth {
  grade: string;
  issues: string[];
  components: {
    database: { ok: boolean; latency_ms: number; error?: string };
    redis: { ok: boolean; latency_ms: number; error?: string };
    queue: { backlog: number; error?: string };
  };
  process: {
    memory_rss_mb: number;
    uptime_s: number;
    uptime_h: number;
    active_requests: number;
    degraded_mode: boolean;
  };
}

export interface AIInterpretation {
  interpretation: string;
  provider: string;
  severity: string;
  critical_flags: string[];
  results_severity: { test: string; severity: string }[];
  conflicts: string[];
  confidence: { score: number; level: string };
  action_guidance: { ar: string; urgency: string; within_hours?: number };
  cached?: boolean;
}

export interface AIChatResponse {
  reply: string;
  provider: string;
  display_only: boolean;
}

export interface AIProviderStatus {
  providers: {
    name: string;
    type: string;
    configured: boolean;
    reachable?: boolean;
    model?: string;
  }[];
  active_provider: string;
  fallback_chain: string[];
}

export interface TurnaroundTime {
  days: number;
  avg_minutes?: number;
  min_minutes?: number;
  max_minutes?: number;
  median_minutes?: number;
  completed_orders_sampled: number;
}

export interface PatientCard {
  card: {
    patient: {
      id: number;
      full_name: string;
      health_id: string;
      phone: string;
      birth_date?: string;
      gender?: string;
    };
    lab_name?: string;
  };
  token: string;
  qr_url: string;
}

export interface LabEmployee {
  id: number;
  name: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at?: string;
}

export interface FhirPatient {
  resourceType: string;
  id: string;
  name: { use: string; text: string }[];
  gender?: string;
  birthDate?: string;
  telecom: { system: string; value: string; use?: string }[];
}


export interface PopularClinic {
  id: number;
  lab_id: number;
  province_id: number;
  administrative_unit_code: string;
  name: string;
  operating_hours?: string | null;
  is_active: boolean;
}

export interface PopularClinicPatient {
  id: number;
  full_name: string;
  birth_date?: string | null;
  phone: string;
  health_id?: string | null;
}

export interface PopularClinicMedication {
  medication_name: string;
  quantity: number;
  dosage: string;
}

export interface PopularClinicBookletMonth {
  month: number;
  dispensation?: {
    id: number;
    approved_by?: number | null;
    dispensed_at?: string | null;
    medication_name: string;
    quantity: number;
    dosage: string;
    pharmacist_user_id?: number | null;
  } | null;
}

export interface PopularClinicPatientCard {
  patient: PopularClinicPatient;
  clinic_id: number;
  attending_doctor_id?: number | null;
  conditions: string[];
  treatment_plan?: PopularClinicMedication | null;
  latest_vitals?: Record<string, unknown> | null;
}

export interface PopularClinicTicket {
  id: number;
  clinic_id: number;
  patient_id: number;
  service_code: string;
  payment_method: "cash" | "electronic";
  amount: string | number;
  status: "issued" | "paid" | "cancelled" | string;
  payment_intent_id?: string | null;
  issued_at?: string | null;
  paid_at?: string | null;
}

export interface PopularClinicDailyReport {
  clinic_id: number;
  report_date: string;
  tickets_issued: number;
  tickets_paid: number;
  cash_total: string | number;
  electronic_total: string | number;
  pending_total: string | number;
}

export interface PopularClinicMonthlyReport {
  clinic_id: number;
  year: number;
  month: number;
  enrolled_patients: number;
  dispensed_patients: number;
  missed_patients: number;
  dispensing_rate: string | number;
  most_requested_medications: { medication_name: string; quantity: number }[];
}
