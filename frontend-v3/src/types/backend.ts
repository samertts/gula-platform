export type UserRole =
  | 'master_admin'
  | 'ministry_admin'
  | 'province_admin'
  | 'admin'
  | 'lab_admin'
  | 'doctor'
  | 'staff'
  | 'lab_staff'
  | 'technician'
  | 'citizen';

export const ROLE_LEVELS: Record<UserRole, number> = {
  master_admin: 100,
  ministry_admin: 90,
  province_admin: 80,
  admin: 50,
  lab_admin: 50,
  doctor: 40,
  staff: 20,
  lab_staff: 20,
  technician: 20,
  citizen: 10,
};

export type Permission =
  | 'patients:read'
  | 'patients:write'
  | 'patients:delete'
  | 'orders:read'
  | 'orders:write'
  | 'results:read'
  | 'results:write'
  | 'staff:manage'
  | 'lab:read'
  | 'lab:manage'
  | 'dashboard:read'
  | 'audit:read'
  | 'platform:manage_users'
  | 'platform:manage_labs'
  | 'platform:view_stats'
  | 'system:admin';

export interface JwtPayload {
  user_id: number;
  lab_id: number;
  role: UserRole;
  perm_ver: number;
  type: 'access' | 'refresh';
  jti: string;
  exp: number;
  iat: number;
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
  created_at: string;
}

export interface LabUser {
  id: number;
  lab_id: number;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  perm_version: number;
  province_id?: number;
  created_by?: number;
  created_at: string;
}

export interface Patient {
  id: number;
  lab_id: number;
  health_id?: string;
  national_id_hash?: string;
  family_id_hash?: string;
  guardian_id?: number;
  full_name: string;
  phone: string;
  birth_date?: string;
  gender?: string;
  email?: string;
  created_at: string;
}

export type OrderStatus = 'pending' | 'completed' | 'validated' | 'cancelled';
export type SampleStatus = 'collected' | 'received' | 'processing' | 'analyzed' | 'rejected';
export type SampleType = 'blood' | 'urine' | 'stool' | 'swab' | 'serum' | 'plasma' | 'csf' | 'sputum' | 'other';
export type ResultFlag = 'normal' | 'H' | 'L' | 'critical';
export type QCStatus = 'pass' | 'warning' | 'fail';

export interface LabOrder {
  id: number;
  patient_id: number;
  lab_id: number;
  doctor_name?: string;
  doctor_user_id?: number;
  status: OrderStatus;
  validated_by?: number;
  validated_at?: string;
  locked_at?: string;
  version: number;
  created_at: string;
  patient?: Patient;
  results?: LabResult[];
  samples?: Sample[];
}

export interface LabResult {
  id: number;
  order_id: number;
  test_type_id?: number;
  test_name: string;
  value?: number;
  value_text?: string;
  unit?: string;
  normal_range_low?: number;
  normal_range_high?: number;
  flag?: ResultFlag;
  token: string;
  expires_at: string;
  created_at: string;
  version: number;
}

export interface Sample {
  id: number;
  order_id: number;
  barcode: string;
  sample_type: string;
  collection_time: string;
  collected_by?: string;
  status: SampleStatus;
  rejection_reason?: string;
  notes?: string;
  storage_location?: string;
  created_at: string;
}

export interface TestType {
  id: number;
  code: string;
  name: string;
  name_ar?: string;
  category?: string;
  unit?: string;
  normal_low?: number;
  normal_high?: number;
}

export interface QualityControl {
  id: number;
  lab_id: number;
  test_code: string;
  instrument_name?: string;
  lot_number?: string;
  level: string;
  expected_value: number;
  measured_value: number;
  sd?: number;
  unit?: string;
  status: QCStatus;
  violation?: string;
  notes?: string;
  performed_by?: string;
  created_at: string;
}

export interface AuditLog {
  id: number;
  user_id?: number;
  user_role?: string;
  action: string;
  resource_type: string;
  resource_id?: number;
  details?: string;
  ip_address?: string;
  created_at: string;
  chain_hash?: string;
}

export interface Organization {
  id: number;
  name: string;
  name_ar?: string;
  org_type: string;
  license_number?: string;
  phone?: string;
  email?: string;
  address?: string;
  city?: string;
  province?: string;
  is_active: boolean;
  created_at: string;
}

export interface Facility {
  id: number;
  organization_id: number;
  name: string;
  name_ar?: string;
  facility_type: string;
  phone?: string;
  email?: string;
  address?: string;
  city?: string;
  province?: string;
  is_active: boolean;
  created_at: string;
}

export interface LabSubscription {
  id: number;
  lab_id: number;
  tier: 'starter' | 'growth' | 'enterprise';
  deployment_mode: string;
  security_level: string;
  is_active: boolean;
  max_patients: number;
  max_staff: number;
  max_orders_per_day: number;
  max_ai_calls_per_day: number;
  expires_at?: string;
}

export interface FeatureFlag {
  id: number;
  lab_id: number;
  feature_key: string;
  is_enabled: boolean;
  reason?: string;
  expires_at?: string;
}

export interface UpgradeRequest {
  id: number;
  lab_id: number;
  requester_id?: number;
  target_tier: string;
  status: 'pending' | 'approved' | 'rejected';
  reason?: string;
  created_at: string;
}

export interface CriticalAlert {
  id: number;
  lab_id: number;
  order_id: number;
  result_id: number;
  test_name: string;
  value: string;
  flag: string;
  acknowledged: boolean;
  acknowledged_by?: number;
  acknowledged_at?: string;
  created_at: string;
}

export interface EdgeDevice {
  id: number;
  device_id: string;
  lab_id: number;
  display_name?: string;
  status: string;
  trust_score: number;
  agent_version?: string;
  last_seen_at?: string;
  created_at: string;
}

export interface EdgeTask {
  id: number;
  task_uid: string;
  lab_id: number;
  device_id?: string;
  kind: string;
  priority: number;
  status: string;
  payload?: any;
  created_at: string;
}

export interface Claim {
  id: number;
  lab_id: number;
  patient_id: number;
  order_id?: number;
  status: 'draft' | 'validated' | 'submitted' | 'accepted' | 'rejected' | 'paid';
  total_amount?: number;
  currency: string;
  external_ref?: string;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: LabUser;
  lab: Lab;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface CreatePatientRequest {
  full_name: string;
  phone: string;
  birth_date?: string;
  gender?: string;
  email?: string;
  national_id?: string;
  family_id?: string;
}

export interface UpdatePatientRequest {
  full_name?: string;
  phone?: string;
  birth_date?: string;
  gender?: string;
  email?: string;
}

export interface CreateOrderRequest {
  patient_id: number;
  doctor_name?: string;
  tests: { test_code: string; test_name: string; }[];
}

export interface CreateSampleRequest {
  order_id: number;
  sample_type: string;
  collected_by?: string;
  notes?: string;
}

export interface CreateResultRequest {
  order_id: number;
  test_name: string;
  value?: number;
  value_text?: string;
  unit?: string;
}

export interface DashboardStats {
  orders_today: number;
  results_today: number;
  patients_today: number;
  pending_orders: number;
  critical_alerts: number;
  recent_activity: AuditLog[];
}

export interface StatsTrend {
  date: string;
  orders: number;
  results: number;
  patients: number;
}

export interface StatsSummary {
  total_orders: number;
  total_patients: number;
  total_results: number;
  today_orders: number;
  today_results: number;
  today_patients: number;
  this_week_orders: number;
  this_month_orders: number;
  avg_turnaround_hours?: number;
}

export interface TurnaroundTime {
  test_code: string;
  test_name: string;
  avg_minutes: number;
  count: number;
}

export interface QCSubmission {
  test_code: string;
  instrument_name?: string;
  lot_number?: string;
  level: string;
  expected_value: number;
  measured_value: number;
  sd?: number;
  unit?: string;
  notes?: string;
  performed_by?: string;
}

export interface AdminCreateUser {
  name: string;
  email: string;
  password: string;
  role: UserRole;
  lab_id?: number;
  is_active?: boolean;
}

export interface AdminUpdateUser {
  name?: string;
  email?: string;
  role?: UserRole;
  is_active?: boolean;
}

export interface AdminCreateLab {
  name: string;
  lab_type?: string;
  city?: string;
  address?: string;
  phone?: string;
  admin_email: string;
  admin_name: string;
  admin_password: string;
}

export interface AdminUpdateLab {
  name?: string;
  lab_type?: string;
  city?: string;
  address?: string;
  phone?: string;
  is_active?: boolean;
}

export interface EHRNote {
  id: number;
  patient_id: number;
  note_type: string;
  content: string;
  author_name: string;
  created_at: string;
}

export interface EHRCondition {
  id: number;
  patient_id: number;
  condition_code?: string;
  condition_name: string;
  onset_date?: string;
  status: string;
}

export interface EHRMedication {
  id: number;
  patient_id: number;
  medication_name: string;
  dosage?: string;
  frequency?: string;
  route?: string;
  start_date?: string;
  end_date?: string;
  status: string;
}

export interface EHRAllergy {
  id: number;
  patient_id: number;
  allergen: string;
  reaction?: string;
  severity?: string;
  status: string;
}

export interface EHRImmunization {
  id: number;
  patient_id: number;
  vaccine_name: string;
  administered_date: string;
  administered_by?: string;
  lot_number?: string;
}

export interface PatientCard {
  patient: Patient;
  card_token: string;
  qr_data: string;
  issued_at: string;
}

export interface ClinicalOrder {
  id: number;
  patient_id: number;
  order_type: string;
  status: string;
  priority: string;
  ordered_by?: string;
  created_at: string;
}

export interface ClinicalDocumentation {
  id: number;
  patient_id: number;
  encounter_id?: number;
  doc_type: string;
  content: any;
  author_name: string;
  created_at: string;
}

export interface Appointment {
  id: number;
  patient_id: number;
  provider_id?: number;
  facility_id?: number;
  lab_id: number;
  appointment_type: string;
  status: string;
  scheduled_date: string;
  duration_minutes: number;
  reason?: string;
  notes?: string;
}

export interface ConsentRecord {
  id: string;
  gpid: string;
  grantee_id: string;
  scope: string;
  status: 'active' | 'revoked' | 'expired';
  expires_at: string;
  created_at: string;
}

export interface IntegrationStatus {
  name: string;
  mode: string;
  status: 'ok' | 'error' | 'stub';
  last_check?: string;
}

export interface SecurityStatus {
  recent_logins: number;
  failed_attempts: number;
  mfa_enabled: boolean;
  active_sessions: number;
}

export interface FHIRResource {
  resourceType: string;
  id: string;
  [key: string]: any;
}
