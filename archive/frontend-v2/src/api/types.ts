export type UserRole =
  | 'master_admin' | 'admin' | 'lab_admin' | 'technician'
  | 'pathologist' | 'physician' | 'citizen'
  | 'ministry_admin' | 'ministry_analyst' | 'ministry_inspector'
  | 'regulator' | 'auditor' | 'researcher' | 'integration_service';

export type OrderStatus = 'pending' | 'received' | 'processing' | 'completed' | 'released' | 'cancelled';
export type Priority = 'routine' | 'urgent' | 'stat';
export type SampleStatus = 'collected' | 'in_transit' | 'received' | 'processing' | 'completed' | 'rejected';

export interface LoginResponse {
  token: string;
  refresh_token: string;
  token_type: string;
  user: UserInfo;
}

export interface UserInfo {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  lab_id: string | null;
  lab_name: string | null;
}

export interface Patient {
  id: string;
  full_name: string;
  phone: string;
  gender: 'male' | 'female';
  birth_date: string;
  age?: number;
  national_id?: string;
  guardian_id?: string;
  address?: string;
  city?: string;
  blood_type?: string;
  created_at?: string;
  updated_at?: string;
}

export interface CreatePatientRequest {
  full_name: string;
  phone: string;
  birth_date: string;
  gender: 'male' | 'female';
  national_id?: string;
  guardian_id?: string;
  address?: string;
  city?: string;
  blood_type?: string;
}

export interface LabOrder {
  id: string;
  patient_id: string;
  doctor_name?: string;
  status: OrderStatus;
  priority: Priority;
  test_count?: number;
  results?: LabResult[];
  created_at: string;
  updated_at?: string;
  validated_at?: string;
  cancelled_at?: string;
  cancel_reason?: string;
}

export interface CreateOrderRequest {
  patient_id: string;
  doctor_name?: string;
  results: CreateResultItem[];
}

export interface CreateResultItem {
  test_code: string;
  value: string;
  unit?: string;
  reference_range?: string;
  flag?: 'H' | 'L' | 'N' | 'C';
  notes?: string;
}

export interface LabResult {
  id: string;
  order_id: string;
  test_code: string;
  test_name: string;
  test_name_ar?: string;
  value: string;
  unit: string;
  reference_range: string;
  flag?: 'H' | 'L' | 'N' | 'C';
  status: string;
  verified_by?: string;
  verified_at?: string;
  notes?: string;
}

export interface Sample {
  id: string;
  order_id: string;
  patient_id: string;
  sample_type: string;
  sample_type_ar?: string;
  barcode: string;
  status: SampleStatus;
  collected_at: string;
  received_at?: string;
  collected_by?: string;
  rejection_reason?: string;
  notes?: string;
}

export interface QCResult {
  id: string;
  test_code: string;
  level: string;
  expected_value: string;
  measured_value: string;
  sd: number;
  status: 'pass' | 'warning' | 'fail';
  rule_violated?: string;
  created_at: string;
}

export interface DashboardStats {
  patients_today: number;
  orders_today: number;
  results_today: number;
  abnormal_results: number;
  pending_samples: number;
  qc_alerts: number;
  recent_orders: LabOrder[];
}

export interface DailyTrend {
  date: string;
  orders: number;
  results: number;
}

export interface TestTrend {
  test_name: string;
  count: number;
}

export interface LabStats {
  daily_trends: DailyTrend[];
  top_tests: TestTrend[];
  flag_distribution: { flag: string; count: number }[];
  weekly_patients: { week: string; count: number }[];
  summary: {
    today: number;
    this_week: number;
    this_month: number;
    all_time: number;
  };
  turnaround_minutes: number;
}

export interface NotificationRecord {
  id: string;
  order_id: string;
  channel: 'whatsapp' | 'sms';
  sent_at: string;
  viewed: boolean;
  viewed_at?: string;
}

export interface Permission {
  id: string;
  resource: string;
  action: string;
  scope: string;
  domain?: string;
}

export interface Role {
  id: string;
  name: string;
  level: number;
  permissions?: Permission[];
}

export interface MenuItem {
  path: string;
  label: string;
  icon: string;
  children?: MenuItem[];
}

export interface AdminStats {
  total_labs: number;
  active_labs: number;
  total_users: number;
  total_patients: number;
  total_orders: number;
  pending_activations: number;
}

export interface Lab {
  id: string;
  name: string;
  name_ar?: string;
  code: string;
  city: string;
  city_ar?: string;
  address?: string;
  phone?: string;
  email?: string;
  status: 'active' | 'inactive' | 'pending';
  is_active?: boolean;
  capacity?: number;
  created_at?: string;
}

export interface Employee {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at?: string;
}

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  user_id: string;
  user_name?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details?: string;
  ip_address?: string;
  severity?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page?: number;
  limit?: number;
  skip?: number;
}

export interface ClinicalNote {
  id: string;
  patient_id: string;
  note_type: string;
  title: string;
  content: string;
  created_at: string;
  updated_at?: string;
}

export interface Allergy {
  id: string;
  patient_id: string;
  code_display: string;
  severity: 'mild' | 'moderate' | 'severe';
  status: string;
}

export interface Diagnosis {
  id: string;
  patient_id: string;
  diagnosis_text: string;
  icd10_code?: string;
  clinical_status?: string;
}
