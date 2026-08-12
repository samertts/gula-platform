import {
  LabType, LabRole, Gender, SampleStatus, ResultStatus,
  ClaimStatus, EdgeRoleMode, TaskStatus, PrivacyLevel,
  ModelStatus, ModelRuntime, MpiMatchMethod, FeedbackSignal,
  SubscriptionTier, OrderPriority, QcLevel, AbnormalityDirection,
  GovernanceNodeType, HealthGrade, PlatformRole,
  EdgeDeviceStatus,
} from './enums';

export interface PaginationMeta {
  total: number;
  page: number;
  limit: number;
  pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ListResponse<T> {
  items: T[];
  pagination: PaginationMeta;
}

// ── Auth ────────────────────────────────────────────────────────
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserBrief;
}

export interface RefreshRequest {
  refresh_token?: string;
}

export interface RefreshResponse {
  access_token: string;
  expires_in: number;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface LabRegisterRequest {
  lab_name: string;
  license_number?: string;
  lab_type?: LabType;
  director_name?: string;
  city?: string;
  address?: string;
  phone?: string;
  website?: string;
  admin_name: string;
  email: string;
  password: string;
}

export interface CitizenRegisterRequest {
  full_name: string;
  phone: string;
  email?: string;
  password: string;
  gender?: Gender;
  birth_date?: string;
  national_id?: string;
}

export interface StaffRegisterRequest {
  name: string;
  email: string;
  password: string;
  role?: LabRole;
}

export interface DoctorRegisterRequest {
  full_name: string;
  email: string;
  phone: string;
  password: string;
  license_number: string;
  specialty?: string;
  workplace?: string;
  national_id?: string;
}

export interface DeviceTokenRequest {
  device_token: string;
  platform: 'android' | 'ios';
  app_version?: string;
}

export interface CitizenLoginRequest {
  identifier: string;
  email?: string;
  password: string;
}

export interface NationalIdRequest {
  national_id: string;
}

export interface CreateLabRequest {
  name: string;
  city?: string;
  phone?: string;
  admin_email: string;
  admin_password: string;
  admin_name: string;
  province_id?: number;
}

export interface CreateUserRequest {
  name: string;
  email: string;
  password: string;
  role: string;
  lab_id?: number;
  province_id?: number;
  national_id?: string;
}

export interface ChangeRoleRequest {
  role: string;
  province_id?: number;
}

export interface LinkIdentityRequest {
  patient_id: number;
  national_id: string;
  confirm_name?: string;
}

export interface KillSwitchRequest {
  reason?: string;
}

export interface UserBrief {
  id: number;
  email: string;
  name: string;
  role: PlatformRole;
  lab_id?: number;
  is_active: boolean;
}

// ── Patients ─────────────────────────────────────────────────────
export interface PatientCreate {
  full_name: string;
  phone: string;
  birth_date?: string;
  gender?: Gender;
  email?: string;
  national_id?: string;
  family_id?: string;
  force_create?: boolean;
  guardian_id?: number;
}

export interface PatientUpdate {
  full_name?: string;
  phone?: string;
  birth_date?: string;
  gender?: Gender;
  email?: string;
  family_id?: string;
}

export interface PatientResponse {
  id: number;
  full_name: string;
  phone: string;
  birth_date?: string;
  gender?: Gender;
  email?: string;
  lab_id: number;
  citizen_ulid?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface PatientHistory {
  orders: OrderResponse[];
  results: TestResultBrief[];
  samples: SampleResponse[];
}

export interface ScanRequest {
  token: string;
}

export interface ConvertGuestRequest {
  patient_id: number;
  full_name: string;
  phone: string;
  birth_date?: string;
  gender?: Gender;
}

// ── Labs ─────────────────────────────────────────────────────────
export interface LabUpdate {
  name?: string;
  city?: string;
  address?: string;
  phone?: string;
  license_number?: string;
  lab_type?: LabType;
  director_name?: string;
  website?: string;
}

export interface LabResponse {
  id: number;
  name: string;
  city?: string;
  address?: string;
  phone?: string;
  license_number?: string;
  lab_type?: LabType;
  director_name?: string;
  website?: string;
  status: string;
  tier?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateEmployeeRequest {
  name: string;
  email: string;
  password: string;
  role?: LabRole;
}

export interface UpdateEmployeeRequest {
  is_active?: boolean;
  role?: LabRole;
}

export interface LabUserResponse {
  id: number;
  name: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface LabWorkHours {
  day: string;
  open: string;
  close: string;
  is_open: boolean;
}

export interface LabHoliday {
  id: number;
  date: string;
  description: string;
}

export interface LabSettings {
  [key: string]: unknown;
}

export interface LabDepartment {
  id: number;
  name: string;
  code?: string;
}

// ── Orders & Results ─────────────────────────────────────────────
export interface ResultItem {
  test_name: string;
  value?: number;
  value_text?: string;
  unit?: string;
  normal_range_low?: number;
  normal_range_high?: number;
}

export interface CreateOrderRequest {
  patient_id: number;
  doctor_name?: string;
  doctor_user_id?: number;
  results: ResultItem[];
}

export interface OrderResponse {
  id: number;
  patient_id: number;
  lab_id: number;
  doctor_name?: string;
  doctor_user_id?: number;
  status: string;
  created_at: string;
  updated_at: string;
  results: ResultItemResponse[];
}

export interface ResultItemResponse {
  id: number;
  order_id: number;
  test_name: string;
  value?: number;
  value_text?: string;
  unit?: string;
  normal_range_low?: number;
  normal_range_high?: number;
  status: string;
  is_critical: boolean;
  is_abnormal: boolean;
  created_at: string;
}

export interface AnalyzeRequest {
  results: ResultItem[];
}

export interface AnalyzeResponse {
  interpretations: InterpretationResult[];
  critical_flags: CriticalFlag[];
}

export interface InterpretationResult {
  test_name: string;
  interpretation: string;
  is_abnormal: boolean;
  direction?: AbnormalityDirection;
}

export interface CriticalFlag {
  test_name: string;
  value: string;
  message: string;
}

export interface BatchOrderItem {
  patient_id: number;
  doctor_name?: string;
  results: BatchResultItem[];
}

export interface BatchResultItem {
  test_name: string;
  value?: number;
  value_text?: string;
  unit?: string;
  normal_range_low?: number;
  normal_range_high?: number;
}

export interface BatchOrderRequest {
  orders: BatchOrderItem[];
}

export interface BatchOrderResponse {
  created: number;
  failed: number;
  errors?: string[];
}

export interface TestResultCreate {
  citizen_id: number;
  lab_id: number;
  device_id?: number;
  test_code: string;
  test_name_en: string;
  test_name_ar: string;
  category?: string;
  result_value?: number;
  result_text?: string;
  unit?: string;
  reference_min?: number;
  reference_max?: number;
  status?: ResultStatus;
  is_critical?: boolean;
  is_abnormal?: boolean;
  abnormality_direction?: AbnormalityDirection;
  sample_collected_at: string;
  sample_barcode: string;
  ordering_physician?: string;
  clinical_notes?: string;
}

export interface TestResultRead {
  id: number;
  citizen_id: number;
  lab_id: number;
  device_id?: number;
  test_code: string;
  test_name_en: string;
  test_name_ar: string;
  category?: string;
  result_value?: number;
  result_text?: string;
  unit?: string;
  reference_min?: number;
  reference_max?: number;
  status: ResultStatus;
  is_critical: boolean;
  is_abnormal: boolean;
  abnormality_direction?: AbnormalityDirection;
  sample_collected_at: string;
  result_completed_at?: string;
  verified_at?: string;
  verified_by?: string;
  sample_barcode: string;
  ordering_physician?: string;
  clinical_notes?: string;
  created_at: string;
  updated_at: string;
}

export interface TestResultBrief {
  id: number;
  test_code: string;
  test_name_en: string;
  test_name_ar: string;
  result_value?: number;
  result_text?: string;
  unit?: string;
  status: ResultStatus;
  is_abnormal: boolean;
  is_critical: boolean;
  sample_collected_at: string;
}

export interface TestResultForCitizen {
  id: number;
  test_name_ar: string;
  result_value?: number;
  result_text?: string;
  unit?: string;
  reference_min?: number;
  reference_max?: number;
  status: ResultStatus;
  is_abnormal: boolean;
  is_critical: boolean;
  abnormality_direction?: AbnormalityDirection;
  sample_collected_at: string;
  result_completed_at?: string;
}

export interface TestResultValidateRequest {
  test_name: string;
  test_code?: string;
  value?: number;
  unit?: string;
  normal_range_low?: number;
  normal_range_high?: number;
}

export interface DeviceResult {
  test_name: string;
  value?: number;
  value_text?: string;
  unit?: string;
  normal_range_low?: number;
  normal_range_high?: number;
}

export interface DeviceSubmission {
  barcode: string;
  device_id?: string;
  results: DeviceResult[];
}

export interface DeviceSubmissionResponse {
  matched_order_id: number;
  results_created: number;
  errors?: string[];
}

export interface SuggestRequest {
  operation: string;
  payload?: Record<string, unknown>;
  entity_type?: string;
  entity_id?: number;
  confidence?: number;
  rationale?: string;
}

export interface RejectRequest {
  reason?: string;
}

export interface ChatRequest {
  message: string;
  context?: string;
}

export interface ChatResponse {
  reply: string;
  sources?: string[];
}

export interface ResultAmendment {
  id: number;
  result_id: number;
  previous_value?: string;
  new_value?: string;
  reason: string;
  amended_by: string;
  created_at: string;
}

// ── Samples ──────────────────────────────────────────────────────
export interface SampleCreate {
  order_id: number;
  sample_type: string;
  collected_by?: string;
  notes?: string;
  storage_location?: string;
}

export interface SampleUpdate {
  status?: SampleStatus;
  rejection_reason?: string;
  notes?: string;
  storage_location?: string;
}

export interface SampleResponse {
  id: number;
  barcode: string;
  order_id: number;
  sample_type: string;
  status: SampleStatus;
  collected_by?: string;
  rejection_reason?: string;
  notes?: string;
  storage_location?: string;
  collected_at: string;
  updated_at: string;
}

export interface SampleTransferRequest {
  target_lab_id: number;
  notes?: string;
}

// ── Consent ──────────────────────────────────────────────────────
export interface GrantRequest {
  gpid: string;
  grantee_id: string;
  scope: string;
  expires_in_hours: number;
}

export interface GrantResponse {
  consent_id: string;
  gpid: string;
  grantee_id: string;
  scope: string;
  expires_at: string;
}

export interface RevokeRequest {
  gpid: string;
  grantee_id: string;
  scope: string;
}

export interface RevokeResponse {
  revoked: boolean;
}

export interface CheckResponse {
  allowed: boolean;
  scope: string;
  expires_at?: string;
}

export interface ConsentRecord {
  id: string;
  gpid: string;
  grantee_id: string;
  scope: string;
  status: string;
  expires_at: string;
  created_at: string;
}

// ── Claims ───────────────────────────────────────────────────────
export interface ClaimItemCreate {
  test_code: string;
  description?: string;
  quantity?: number;
  unit_price: number;
  amount: number;
}

export interface ClaimCreate {
  patient_id: number;
  order_id?: number;
  items: ClaimItemCreate[];
  idempotency_key?: string;
}

export interface ClaimItemResponse {
  id: number;
  claim_id: number;
  test_code: string;
  description?: string;
  quantity: number;
  unit_price: number;
  amount: number;
}

export interface ClaimResponse {
  id: number;
  lab_id: number;
  patient_id: number;
  order_id?: number;
  status: ClaimStatus;
  total_amount?: number;
  currency: string;
  idempotency_key?: string;
  external_ref?: string;
  submitted_at?: string;
  created_at?: string;
  updated_at?: string;
  items: ClaimItemResponse[];
}

// ── Edge ─────────────────────────────────────────────────────────
export interface RegisterDeviceRequest {
  public_key_pem: string;
  role_mode?: EdgeRoleMode;
  display_name?: string;
  agent_version?: string;
  os_platform?: string;
  capabilities?: Record<string, unknown>;
  attestation_blob?: string;
}

export interface RegisterDeviceResponse {
  device_id: string;
  status: string;
  role_mode: EdgeRoleMode;
  trust_score: number;
  cert_fingerprint: string;
  agent_token: string;
  nonce: string;
}

export interface DeviceSummary {
  device_id: string;
  display_name?: string;
  role_mode: EdgeRoleMode;
  status: EdgeDeviceStatus;
  trust_score: number;
  last_seen_at?: string;
  agent_version?: string;
}

export interface DeviceDetail {
  device_id: string;
  display_name?: string;
  role_mode: EdgeRoleMode;
  status: EdgeDeviceStatus;
  trust_score: number;
  last_seen_at?: string;
  agent_version?: string;
  capabilities?: Record<string, unknown>;
  registered_at: string;
  revoked_at?: string;
  quarantined_at?: string;
  kill_switched: boolean;
  latest_telemetry?: Record<string, unknown>;
}

export interface TaskSubmitRequest {
  kind: string;
  payload?: Record<string, unknown>;
  priority?: number;
  privacy_level?: PrivacyLevel;
  required_caps?: string[];
  min_trust?: number;
  timeout_s?: number;
  max_attempts?: number;
  idempotency_key?: string;
  expires_in_s?: number;
}

export interface TaskSummary {
  task_uid: string;
  kind: string;
  status: TaskStatus;
  priority: number;
  privacy_level: PrivacyLevel;
  device_id?: string;
  attempts: number;
  created_at: string;
  completed_at?: string;
}

export interface TaskDetail {
  task_uid: string;
  kind: string;
  status: TaskStatus;
  priority: number;
  privacy_level: PrivacyLevel;
  device_id?: string;
  attempts: number;
  created_at: string;
  completed_at?: string;
  payload?: Record<string, unknown>;
  result?: Record<string, unknown>;
  error?: string;
  timeout_s: number;
  max_attempts: number;
}

export interface PolicyView {
  max_concurrent_per_device: number;
  max_devices_per_lab: number;
  idle_only: boolean;
  battery_floor_pct: number;
  cpu_cap_pct: number;
  ram_cap_mb: number;
  allow_kinds?: string[];
  deny_kinds?: string[];
  min_trust_score: number;
  offline_queue_max: number;
  kill_switch: boolean;
}

export interface PolicyUpdate {
  max_concurrent_per_device?: number;
  max_devices_per_lab?: number;
  idle_only?: boolean;
  battery_floor_pct?: number;
  cpu_cap_pct?: number;
  ram_cap_mb?: number;
  allow_kinds?: string[];
  deny_kinds?: string[];
  min_trust_score?: number;
  offline_queue_max?: number;
  kill_switch?: boolean;
}

export interface HeartbeatRequest {
  agent_version?: string;
  capabilities?: Record<string, unknown>;
  telemetry?: Record<string, unknown>;
  completed_task_uids?: string[];
}

export interface HeartbeatResponse {
  server_time: string;
  next_heartbeat_s: number;
  task?: Record<string, unknown>;
  models?: ModelInfo[];
  quarantined?: boolean;
  kill_switched?: boolean;
}

export interface TaskResultRequest {
  success: boolean;
  result?: Record<string, unknown>;
  error?: string;
  duration_ms?: number;
}

export interface ModelRegisterRequest {
  name: string;
  version: string;
  runtime?: ModelRuntime;
  format?: string;
  quantization?: string;
  size_mb?: number;
  min_ram_mb?: number;
  min_vram_mb?: number;
  sha256?: string;
  source_url?: string;
  metadata?: Record<string, unknown>;
}

export interface ModelInfo {
  uid: string;
  name: string;
  version: string;
  runtime?: ModelRuntime;
  status: ModelStatus;
  size_mb?: number;
  sha256?: string;
}

export interface ModelStatusUpdate {
  status: ModelStatus;
  rollout_pct?: number;
}

export interface ModelAssignRequest {
  lab_id?: number;
  device_id?: string;
}

export interface EdgeSite {
  id: number;
  name: string;
  lab_id: number;
  status: string;
  last_sync_at?: string;
  created_at: string;
}

// ── MPI ──────────────────────────────────────────────────────────
export interface ResolveRequest {
  lab_id: number;
  patient_id: number;
  name: string;
  phone?: string;
  birth_date?: string;
  gender?: Gender;
  national_id?: string;
  family_id?: string;
}

export interface ResolveResponse {
  citizen_ulid: string;
  match_method: MpiMatchMethod;
  match_score?: number;
  created: boolean;
  features?: Record<string, unknown>;
}

export interface CitizenResponse {
  citizen_ulid: string;
  nid_verified: boolean;
  birth_year?: number;
  gender?: Gender;
  status: string;
  merged_into_ulid?: string;
  created_at: string;
}

export interface MergeRequest {
  primary_ulid: string;
  secondary_ulid: string;
  reason: string;
}

export interface MergeResponse {
  event_id: number;
  primary_ulid: string;
  secondary_ulid: string;
  occurred_at: string;
  entry_hash: string;
}

export interface PendingReviewItem {
  claim_id: number;
  citizen_ulid: string;
  lab_id: number;
  local_patient_id: number;
  match_score?: number;
  match_features?: Record<string, unknown>;
  created_at: string;
}

export interface PendingReviewPage {
  total: number;
  items: PendingReviewItem[];
}

export interface ResolveDecisionBody {
  decision: 'confirm' | 'reject';
  reason: string;
}

// ── AI Telemetry ─────────────────────────────────────────────────
export interface RetrievalRefIn {
  source?: string;
  doc_id?: string;
  doc_title?: string;
  chunk_text?: string;
  similarity?: number;
  rank?: number;
}

export interface InteractionIn {
  anonymous_session_id: string;
  language?: string;
  region?: string;
  intent?: string;
  prompt?: string;
  prompt_redacted?: boolean;
  response?: string;
  response_model?: string;
  retrieval_strategy?: string;
  retrieval_refs?: RetrievalRefIn[];
  biomarkers?: string[];
  latency_ms?: number;
  status?: string;
  error_code?: string;
  confidence_score?: number;
  risk_level?: string;
  escalation_recommended?: boolean;
  retrieval_used?: boolean;
  source_quality?: number;
  unsupported_claims?: number;
  fallback_generation?: boolean;
  safety_flags?: string[];
}

export interface InteractionOut {
  id: string;
  lab_id: number;
  created_at: string;
}

export interface FeedbackIn {
  interaction_id: string;
  anonymous_session_id: string;
  signal: FeedbackSignal;
  notes?: string;
}

export interface UnresolvedIn {
  interaction_id?: string;
  anonymous_session_id?: string;
  question: string;
  language?: string;
  category?: string;
}

// ── Governance ───────────────────────────────────────────────────
export interface NodeCreate {
  node_type: string;
  code: string;
  name_ar: string;
  name_en?: string;
  parent_id?: number;
  governorate?: string;
  district?: string;
  metadata_json?: Record<string, unknown>;
}

export interface GovernanceNode {
  id: number;
  node_type: GovernanceNodeType;
  code: string;
  name_ar: string;
  name_en?: string;
  parent_id?: number;
  governorate?: string;
  district?: string;
  created_at: string;
}

export interface DelegationCreate {
  delegator_node_id: number;
  delegate_node_id: number;
  scope?: Record<string, unknown>;
  reason?: string;
}

export interface ActingAppoint {
  node_id: number;
  acting_node_id: number;
  reason?: string;
}

export interface WorkerCreate {
  employee_code: string;
  full_name_ar: string;
  profession: string;
  full_name_en?: string;
  national_id_hash?: string;
  specialization?: string;
  organization_node_id?: number;
  department?: string;
  unit?: string;
  employment_date?: string;
  contact_phone?: string;
  contact_email?: string;
}

export interface HealthcareWorker {
  id: number;
  employee_code: string;
  full_name_ar: string;
  profession: string;
  specialization?: string;
  organization_node_id?: number;
  created_at: string;
}

export interface LabRegister {
  lab_code: string;
  name_ar: string;
  lab_type: LabType;
  name_en?: string;
  organization_node_id?: number;
  license_number?: string;
  governorate?: string;
}

export interface GovernanceLab {
  id: number;
  lab_code: string;
  name_ar: string;
  lab_type: LabType;
  organization_node_id?: number;
  governorate?: string;
  created_at: string;
}

// ── LIMS ─────────────────────────────────────────────────────────
export interface SpecimenRegisterRequest {
  order_id: number;
  barcode: string;
  specimen_type: string;
  container_type?: string;
  volume_ml?: number;
  clinical_info?: string;
}

export interface SpecimenTransitionRequest {
  target_status: string;
  notes?: string;
  rejection_reason?: string;
}

export interface LimsOrderCreateRequest {
  order_id: number;
  accession_number: string;
  priority?: OrderPriority;
  clinical_note?: string;
  diagnosis_code?: string;
}

export interface LimsResultCreateRequest {
  specimen_id: number;
  test_code: string;
  test_name: string;
  value_numeric?: number;
  value_text?: string;
  unit?: string;
  instrument_id?: number;
  loinc_code?: string;
}

export interface ResultValidateRequest {
  notes?: string;
  signature_hash?: string;
  action?: 'validate' | 'reject' | 'flag';
}

export interface IQCRunRequest {
  program_id: number;
  test_code: string;
  measured_value: number;
  expected_value: number;
  sd: number;
  level?: QcLevel;
  lot_number?: string;
  instrument_id?: number;
  notes?: string;
}

export interface InstrumentCreateRequest {
  model_id: number;
  instrument_code: string;
  serial_number?: string;
  workstation_id?: number;
  ip_address?: string;
  port?: number;
}

export interface InstrumentResponse {
  id: number;
  instrument_code: string;
  model_name: string;
  serial_number?: string;
  ip_address?: string;
  status: string;
  last_calibrated_at?: string;
  created_at: string;
}

export interface MaintenanceRecordRequest {
  maintenance_type: string;
  title: string;
  description?: string;
  performed_at?: string;
  cost?: number;
  notes?: string;
}

export interface CalibrationRecordRequest {
  calibration_type: string;
  calibrator_lot?: string;
  passed?: boolean;
  notes?: string;
}

export interface InventoryRequest {
  code: string;
  name: string;
  name_ar?: string;
  current_quantity: number;
  unit: string;
  minimum_quantity?: number;
  supplier_id?: number;
  storage_location?: string;
}

export interface InventoryItem {
  id: number;
  code: string;
  name: string;
  current_quantity: number;
  unit: string;
  minimum_quantity: number;
  supplier_id?: number;
  storage_location?: string;
}

export interface ReportGenerateRequest {
  order_id: number;
  report_number: string;
  locale?: string;
  title?: string;
  title_ar?: string;
}

export interface DeviceMessageRequest {
  instrument_id: number;
  raw_message: string;
}

export interface ASTMResultResponse {
  specimen_id: string;
  test_code: string;
  value: string;
  unit: string;
  flag: string;
}

export interface QCProgram {
  id: number;
  name: string;
  test_code: string;
  rules: string[];
}

// ── Subscription / Tiers ─────────────────────────────────────────
export interface UpgradeRequestBody {
  target_tier: SubscriptionTier;
  target_deployment_mode?: string;
  target_security_level?: string;
  reason?: string;
}

export interface DemandSignalBody {
  lab_id: number;
  target_tier: SubscriptionTier;
  reason?: string;
}

export interface SetTierBody {
  tier: SubscriptionTier;
  deployment_mode?: string;
  security_level?: string;
  billing_cycle?: string;
  notes?: string;
}

export interface FeatureFlagBody {
  feature_key: string;
  is_enabled: boolean;
  reason?: string;
  expires_at?: string;
}

export interface TierInfo {
  id: number;
  name: string;
  code: SubscriptionTier;
  description?: string;
  price_monthly?: number;
  features: string[];
  limits: Record<string, number>;
}

export interface TierUsage {
  tier: SubscriptionTier;
  labs_count: number;
  total_patients: number;
  total_results: number;
}

// ── Quality Control ──────────────────────────────────────────────
export interface QCSubmit {
  test_code: string;
  level: QcLevel;
  expected_value: number;
  measured_value: number;
  sd?: number;
  unit?: string;
  instrument_name?: string;
  lot_number?: string;
  notes?: string;
}

export interface QCBatchSubmit {
  results: QCSubmit[];
}

export interface QCRecord {
  id: number;
  test_code: string;
  level: QcLevel;
  expected_value: number;
  measured_value: number;
  sd?: number;
  deviation?: number;
  westgard_rules?: string[];
  status: string;
  instrument_name?: string;
  lot_number?: string;
  created_at: string;
}

export interface QCRule {
  id: number;
  name: string;
  description: string;
  rule_type: string;
  parameters: Record<string, unknown>;
}

export interface LeveyJenningsData {
  test_code: string;
  points: LeveyJenningsPoint[];
  mean: number;
  sd: number;
  limits: Record<string, number>;
}

export interface LeveyJenningsPoint {
  date: string;
  value: number;
  level: QcLevel;
  violated_rules: string[];
}

// ── Notifications ────────────────────────────────────────────────
export interface NotifyRequest {
  order_id: number;
  channel?: 'whatsapp' | 'sms';
}

export interface NotificationRecord {
  id: number;
  user_id: number;
  title: string;
  body: string;
  type: string;
  read: boolean;
  created_at: string;
}

export interface NotificationPreferences {
  email: boolean;
  sms: boolean;
  push: boolean;
  whatsapp: boolean;
}

// ── Tasks ────────────────────────────────────────────────────────
export interface TaskPayload {
  task_id?: string;
  type: string;
  payload?: Record<string, unknown>;
  retry_count?: number;
  max_retries?: number;
  timeout_s?: number;
  enqueued_at?: string;
}

export interface TaskResult {
  task_id: string;
  status: TaskStatus;
  result?: unknown;
  error?: string;
  attempt?: number;
  completed_at?: string;
  duration_ms?: number;
}

// ── Dashboard / Stats ────────────────────────────────────────────
export interface DashboardSummary {
  patients_count: number;
  orders_today: number;
  pending_results: number;
  critical_alerts: number;
  samples_today: number;
  revenue_today?: number;
}

export interface StatsResponse {
  [key: string]: unknown;
}

export interface RevenueStats {
  daily: number;
  weekly: number;
  monthly: number;
  yearly: number;
}

export interface PatientDemographics {
  total: number;
  by_gender: Record<string, number>;
  by_age_group: Record<string, number>;
}

export interface TestPopularity {
  test_code: string;
  test_name: string;
  count: number;
}

export interface PeakHours {
  hour: number;
  orders_count: number;
}

// ── Critical Alert ───────────────────────────────────────────────
export interface CriticalAlert {
  id: number;
  lab_id: number;
  result_id?: number;
  patient_name: string;
  test_name: string;
  value: string;
  severity: string;
  status: string;
  acknowledged_at?: string;
  resolved_at?: string;
  created_at: string;
}

// ── Compliance ───────────────────────────────────────────────────
export interface ComplianceRecord {
  id: number;
  lab_id: number;
  regulation: string;
  status: string;
  certified_at?: string;
  expires_at?: string;
  notes?: string;
  created_at: string;
}

export interface Regulation {
  id: number;
  code: string;
  name: string;
  description: string;
  jurisdiction: string;
}

export interface ComplianceReport {
  id: number;
  lab_id: number;
  report_type: string;
  period_start: string;
  period_end: string;
  status: string;
  generated_at: string;
}

// ── Insurance ────────────────────────────────────────────────────
export interface InsuranceRecord {
  id: number;
  patient_id: number;
  provider_name: string;
  policy_number: string;
  coverage_details?: Record<string, unknown>;
  valid_from: string;
  valid_until?: string;
  created_at: string;
}

export interface InsuranceProvider {
  id: number;
  name: string;
  code: string;
  coverage_types: string[];
}

// ── Integrations ─────────────────────────────────────────────────
export interface Integration {
  id: number;
  lab_id: number;
  name: string;
  type: string;
  config: Record<string, unknown>;
  status: string;
  last_sync_at?: string;
  created_at: string;
}

// ── Batch Operations ─────────────────────────────────────────────
export interface BatchOperation {
  id: number;
  operation_type: string;
  status: string;
  total_items: number;
  processed_items: number;
  failed_items: number;
  created_at: string;
  completed_at?: string;
}

// ── FHIR ─────────────────────────────────────────────────────────
export interface FhirPatient {
  resourceType: 'Patient';
  id: string;
  identifier?: FhirIdentifier[];
  name?: FhirHumanName[];
  telecom?: FhirContactPoint[];
  gender?: string;
  birthDate?: string;
  address?: FhirAddress[];
  managingOrganization?: FhirReference;
  meta?: FhirMeta;
}

export interface FhirPractitioner {
  resourceType: 'Practitioner';
  id: string;
  identifier?: FhirIdentifier[];
  name?: FhirHumanName[];
  telecom?: FhirContactPoint[];
  qualification?: FhirQualification[];
  meta?: FhirMeta;
}

export interface FhirOrganization {
  resourceType: 'Organization';
  id: string;
  identifier?: FhirIdentifier[];
  name?: string;
  alias?: string[];
  type?: FhirCodeableConcept[];
  telecom?: FhirContactPoint[];
  address?: FhirAddress[];
  meta?: FhirMeta;
}

export interface FhirObservation {
  resourceType: 'Observation';
  id: string;
  status: string;
  code: FhirCodeableConcept;
  subject: FhirReference;
  effectiveDateTime?: string;
  issued?: string;
  performer?: FhirReference[];
  valueQuantity?: FhirQuantity;
  valueString?: string;
  valueCodeableConcept?: FhirCodeableConcept;
  interpretation?: FhirCodeableConcept[];
  referenceRange?: FhirReferenceRange[];
  meta?: FhirMeta;
}

export interface FhirDiagnosticReport {
  resourceType: 'DiagnosticReport';
  id: string;
  status: string;
  code: FhirCodeableConcept;
  subject: FhirReference;
  effectiveDateTime?: string;
  issued?: string;
  performer?: FhirReference[];
  result?: FhirReference[];
  conclusion?: string;
  presentedForm?: FhirAttachment[];
  meta?: FhirMeta;
}

export interface FhirSpecimen {
  resourceType: 'Specimen';
  id: string;
  identifier?: FhirIdentifier[];
  type: FhirCodeableConcept;
  subject: FhirReference;
  collection?: FhirSpecimenCollection;
  meta?: FhirMeta;
}

export interface FhirServiceRequest {
  resourceType: 'ServiceRequest';
  id: string;
  status: string;
  intent: string;
  code: FhirCodeableConcept;
  subject: FhirReference;
  authoredOn?: string;
  requester?: FhirReference;
  meta?: FhirMeta;
}

export interface FhirDevice {
  resourceType: 'Device';
  id: string;
  identifier?: FhirIdentifier[];
  manufacturer?: string;
  modelNumber?: string;
  serialNumber?: string;
  status?: string;
  meta?: FhirMeta;
}

export interface FhirEncounter {
  resourceType: 'Encounter';
  id: string;
  status: string;
  class: FhirCoding;
  subject: FhirReference;
  period?: FhirPeriod;
  participant?: FhirEncounterParticipant[];
  meta?: FhirMeta;
}

export interface FhirBundle {
  resourceType: 'Bundle';
  id?: string;
  type: 'searchset' | 'transaction' | 'collection' | 'document';
  total?: number;
  entry?: FhirBundleEntry[];
  meta?: FhirMeta;
}

export interface FhirBundleEntry {
  fullUrl?: string;
  resource: FhirResource;
  search?: { mode: string };
  request?: { method: string; url: string };
}

export type FhirResource =
  | FhirPatient
  | FhirPractitioner
  | FhirOrganization
  | FhirObservation
  | FhirDiagnosticReport
  | FhirSpecimen
  | FhirServiceRequest
  | FhirDevice
  | FhirEncounter
  | FhirBundle;

export interface FhirIdentifier {
  system?: string;
  value?: string;
  type?: FhirCodeableConcept;
}

export interface FhirHumanName {
  use?: string;
  family?: string;
  given?: string[];
  text?: string;
}

export interface FhirContactPoint {
  system?: 'phone' | 'email' | 'fax';
  value?: string;
  use?: string;
}

export interface FhirAddress {
  line?: string[];
  city?: string;
  district?: string;
  state?: string;
  country?: string;
  text?: string;
}

export interface FhirCodeableConcept {
  coding?: FhirCoding[];
  text?: string;
}

export interface FhirCoding {
  system?: string;
  code?: string;
  display?: string;
}

export interface FhirReference {
  reference?: string;
  type?: string;
  identifier?: FhirIdentifier;
  display?: string;
}

export interface FhirQuantity {
  value?: number;
  comparator?: string;
  unit?: string;
  system?: string;
  code?: string;
}

export interface FhirReferenceRange {
  low?: FhirSimpleQuantity;
  high?: FhirSimpleQuantity;
  type?: FhirCodeableConcept;
  text?: string;
}

export interface FhirSimpleQuantity {
  value?: number;
  unit?: string;
  system?: string;
  code?: string;
}

export interface FhirPeriod {
  start?: string;
  end?: string;
}

export interface FhirAttachment {
  contentType?: string;
  data?: string;
  url?: string;
  title?: string;
}

export interface FhirQualification {
  identifier?: FhirIdentifier[];
  code: FhirCodeableConcept;
  period?: FhirPeriod;
  issuer?: FhirReference;
}

export interface FhirMeta {
  versionId?: string;
  lastUpdated?: string;
  profile?: string[];
  tag?: FhirCoding[];
}

export interface FhirEncounterParticipant {
  type?: FhirCodeableConcept[];
  individual?: FhirReference;
}

export interface FhirSpecimenCollection {
  collectedDateTime?: string;
  collector?: FhirReference;
  method?: FhirCodeableConcept;
  bodySite?: FhirCodeableConcept;
}

// ── Health ───────────────────────────────────────────────────────
export interface HealthStatus {
  status: string;
  version: string;
  uptime_seconds: number;
}

export interface HealthDeep {
  grade: HealthGrade;
  components: HealthComponent[];
  latency_ms: number;
  memory_mb: number;
  database: string;
  redis: string;
}

export interface HealthComponent {
  name: string;
  status: 'healthy' | 'degraded' | 'down';
  latency_ms: number;
  error?: string;
}

// ── Events ──────────────────────────────────────────────────────
export interface OutboxEvent {
  id: number;
  event_type: string;
  aggregate_type: string;
  aggregate_id: string;
  payload: Record<string, unknown>;
  status: string;
  attempts: number;
  created_at: string;
}

// ── Common ───────────────────────────────────────────────────────
export interface ApiError {
  detail: string;
  errors?: Record<string, string[]>;
  code?: string;
}

export interface QueryParams {
  [key: string]: string | number | boolean | undefined | null;
}

export interface PaginationParams {
  page?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  search?: string;
}
