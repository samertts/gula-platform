import { api } from "./client";
import type {
  LoginRequest,
  LoginResponse,
  Patient,
  LabOrder,
  LabResult,
  Sample,
  DashboardData,
  Lab,
  User,
  AuditLog,
  CriticalAlert,
  QualityControl,
  SubscriptionTier,
  SubscriptionInfo,
  TrendData,
  FlagDistribution,
  StatsSummary,
  TurnaroundTime,
  PatientCard,
  LabEmployee,
  AIInterpretation,
  AIChatResponse,
  AIProviderStatus,
} from "@/types";

// ── Auth ──
export const authApi = {
  login: (data: LoginRequest) =>
    api.post<LoginResponse>("/login", data).then((r) => r.data),
  logout: () => api.post("/logout").then((r) => r.data),
  register: (data: Record<string, unknown>) =>
    api.post("/register", data).then((r) => r.data),
  registerCitizen: (data: Record<string, unknown>) =>
    api.post("/register/citizen", data).then((r) => r.data),
  registerStaff: (data: Record<string, unknown>) =>
    api.post("/register/staff", data).then((r) => r.data),
  registerDoctor: (data: Record<string, unknown>) =>
    api.post("/register/doctor", data).then((r) => r.data),
  forgotPassword: (email: string) =>
    api.post("/auth/forgot-password", { email }).then((r) => r.data),
  resetPassword: (token: string, new_password: string) =>
    api.post("/auth/reset-password", { token, new_password }).then((r) => r.data),
  changePassword: (current_password: string, new_password: string) =>
    api.post("/auth/change-password", { current_password, new_password }).then((r) => r.data),
};

// ── Setup ──
export const setupApi = {
  status: () => api.get<{ needs_setup: boolean }>("/setup/status").then((r) => r.data),
};

// ── Dashboard ──
export const dashboardApi = {
  greeting: () => api.get<{ greeting: string; message: string; user_name: string }>("/greeting").then((r) => r.data),
  dashboard: () => api.get<DashboardData>("/dashboard").then((r) => r.data),
};

// ── Patients ──
export const patientsApi = {
  list: (params?: { search?: string; skip?: number; limit?: number }) =>
    api.get<Patient[]>("/patients", { params }).then((r) => r.data),
  create: (data: Record<string, unknown>) =>
    api.post("/patients", data).then((r) => r.data),
  get: (id: number) =>
    api.get<Patient>(`/patients/${id}`).then((r) => r.data),
  update: (id: number, data: Record<string, unknown>) =>
    api.put(`/patients/${id}`, data).then((r) => r.data),
  getFamily: (familyId: string) =>
    api.get(`/patients/family/${familyId}`).then((r) => r.data),
  getChildren: (patientId: number) =>
    api.get(`/patients/${patientId}/children`).then((r) => r.data),
};

// ── Orders ──
export const ordersApi = {
  testProfiles: () => api.get<Record<string, unknown[]>>("/test-profiles").then((r) => r.data),
  list: (params?: { skip?: number; limit?: number; search?: string }) =>
    api.get<LabOrder[]>("/orders", { params }).then((r) => r.data),
  get: (id: number) =>
    api.get<LabOrder>(`/orders/${id}`).then((r) => r.data),
  create: (data: Record<string, unknown>) =>
    api.post("/orders", data).then((r) => r.data),
  validate: (id: number) =>
    api.post(`/orders/${id}/validate`).then((r) => r.data),
  cancel: (id: number) =>
    api.post(`/orders/${id}/cancel`).then((r) => r.data),
  analyze: (id: number) =>
    api.get(`/orders/${id}/intelligence`).then((r) => r.data),
};

// ── Test Results ──
export const resultsApi = {
  list: (params?: { health_id?: string; category?: string; date_from?: string; date_to?: string; is_abnormal?: boolean; skip?: number; limit?: number }) =>
    api.get("/test-results", { params }).then((r) => r.data),
  get: (id: number) =>
    api.get<LabResult>(`/test-results/${id}`).then((r) => r.data),
  create: (data: Record<string, unknown>) =>
    api.post("/test-results/", data).then((r) => r.data),
  verify: (id: number) =>
    api.put(`/test-results/${id}/verify`).then((r) => r.data),
  validate: (data: Record<string, unknown>) =>
    api.post("/test-results/validate", data).then((r) => r.data),
  citizenResults: (healthId: string, params?: Record<string, unknown>) =>
    api.get(`/test-results/citizen/${healthId}`, { params }).then((r) => r.data),
  citizenTimeline: (healthId: string, params?: { category?: string }) =>
    api.get(`/test-results/citizen/${healthId}/timeline`, { params }).then((r) => r.data),
};

// ── Public Results ──
export const publicResultsApi = {
  get: (token: string) =>
    api.get(`/r/${token}`).then((r) => r.data),
  downloadPdf: (token: string) =>
    api.get(`/r/${token}/pdf`, { responseType: "blob" }).then((r) => r.data),
};

// ── QR Codes ──
export const qrApi = {
  get: (token: string) => api.get(`/qr/${token}`).then((r) => r.data),
  getMedical: (token: string) => api.get(`/qr-medical/${token}`).then((r) => r.data),
};

// ── Patient History ──
export const patientHistoryApi = {
  byId: (patientId: number) =>
    api.get(`/patient-history/${patientId}`).then((r) => r.data),
  byPhone: (phone: string, name?: string) =>
    api.get(`/history/${phone}`, { params: { name } }).then((r) => r.data),
};

// ── Clinical Intelligence ──
export const clinicalApi = {
  analyze: (data: Record<string, unknown>) =>
    api.post("/analyze", data).then((r) => r.data),
};

// ── Samples ──
export const samplesApi = {
  list: (params?: { status?: string; skip?: number; limit?: number }) =>
    api.get<{ total: number; samples: Sample[] }>("/samples", { params }).then((r) => r.data),
  create: (data: Record<string, unknown>) =>
    api.post("/samples", data).then((r) => r.data),
  get: (barcode: string) =>
    api.get<Sample>(`/samples/${barcode}`).then((r) => r.data),
  update: (barcode: string, data: Record<string, unknown>) =>
    api.put(`/samples/${barcode}`, data).then((r) => r.data),
};

// ── Labs ──
export const labsApi = {
  me: () => api.get<Lab>("/labs/me").then((r) => r.data),
  update: (data: Record<string, unknown>) =>
    api.put("/labs/me", data).then((r) => r.data),
  employees: () =>
    api.get<{ employees: LabEmployee[] }>("/labs/me/employees").then((r) => r.data),
  createEmployee: (data: Record<string, unknown>) =>
    api.post("/labs/me/employees", data).then((r) => r.data),
  updateEmployee: (id: number, data: Record<string, unknown>) =>
    api.put(`/labs/me/employees/${id}`, data).then((r) => r.data),
};

// ── Admin ──
export const adminApi = {
  stats: () => api.get("/admin/stats").then((r) => r.data),
  labs: (params?: { skip?: number; limit?: number }) =>
    api.get<{ total: number; labs: Lab[] }>("/admin/labs", { params }).then((r) => r.data),
  createLab: (data: Record<string, unknown>) =>
    api.post("/admin/labs", data).then((r) => r.data),
  getLab: (id: number) =>
    api.get<Lab>(`/admin/labs/${id}`).then((r) => r.data),
  toggleLab: (id: number) =>
    api.put(`/admin/labs/${id}/toggle`).then((r) => r.data),
  activateLab: (id: number) =>
    api.put(`/admin/labs/${id}/activate`).then((r) => r.data),
  pendingLabs: (params?: { skip?: number; limit?: number }) =>
    api.get("/admin/labs/pending", { params }).then((r) => r.data),
  users: (params?: { role?: string; lab_id?: number; skip?: number; limit?: number }) =>
    api.get<{ total: number; users: User[] }>("/admin/users", { params }).then((r) => r.data),
  createUser: (data: Record<string, unknown>) =>
    api.post("/admin/users", data).then((r) => r.data),
  changeUserRole: (userId: number, data: Record<string, unknown>) =>
    api.patch(`/admin/users/${userId}/role`, data).then((r) => r.data),
  toggleUser: (userId: number) =>
    api.put(`/admin/users/${userId}/toggle`).then((r) => r.data),
  doctors: (params?: { is_verified?: boolean; skip?: number; limit?: number }) =>
    api.get("/admin/doctors", { params }).then((r) => r.data),
  approveDoctor: (id: number) =>
    api.put(`/admin/doctors/${id}/approve`).then((r) => r.data),
  revokeDoctor: (id: number) =>
    api.put(`/admin/doctors/${id}/revoke`).then((r) => r.data),
  citizens: (params?: { is_active?: boolean; is_verified?: boolean; skip?: number; limit?: number }) =>
    api.get("/admin/citizens", { params }).then((r) => r.data),
  toggleCitizen: (id: number) =>
    api.put(`/admin/citizens/${id}/toggle`).then((r) => r.data),
  verifyCitizen: (id: number) =>
    api.put(`/admin/citizens/${id}/verify`).then((r) => r.data),
  auditLogs: (params?: { action?: string; user_id?: number; skip?: number; limit?: number }) =>
    api.get<{ total: number; logs: AuditLog[] }>("/admin/audit-logs", { params }).then((r) => r.data),
  killSwitchStatus: () => api.get("/admin/kill-switch/status").then((r) => r.data),
  killSwitchActivate: (reason: string) =>
    api.post("/admin/kill-switch/activate", { reason }).then((r) => r.data),
  killSwitchDeactivate: (reason: string) =>
    api.post("/admin/kill-switch/deactivate", { reason }).then((r) => r.data),
  controlLayerStats: () => api.get("/admin/control-layer/stats").then((r) => r.data),
};

// ── Admin Log Level ──
export const adminLogLevelApi = {
  get: () => api.get("/admin/log-level").then((r) => r.data),
  set: (level: string) => api.post("/admin/log-level", { level }).then((r) => r.data),
};

// ── Notifications ──
export const notificationsApi = {
  send: (data: { order_id: number; channel?: string }) =>
    api.post("/notify/send", data).then((r) => r.data),
  history: (orderId: number) =>
    api.get(`/notify/history/${orderId}`).then((r) => r.data),
};

// ── Critical Alerts ──
export const criticalAlertsApi = {
  list: (params?: { hours?: number; acknowledged?: boolean }) =>
    api.get<CriticalAlert[]>("/alerts", { params }).then((r) => r.data),
  stats: () => api.get("/alerts/stats").then((r) => r.data),
};

// ── Quality Control ──
export const qcApi = {
  list: (params?: { test_code?: string; status?: string; days?: number; skip?: number; limit?: number }) =>
    api.get<{ total: number; qc_results: QualityControl[] }>("/qc", { params }).then((r) => r.data),
  submit: (data: Record<string, unknown>) =>
    api.post("/qc", data).then((r) => r.data),
  submitBatch: (data: Record<string, unknown>) =>
    api.post("/qc/batch", data).then((r) => r.data),
  summary: (params?: { days?: number }) =>
    api.get("/qc/summary", { params }).then((r) => r.data),
};

// ── Batch ──
export const batchApi = {
  orders: (data: Record<string, unknown>) =>
    api.post("/batch/orders", data).then((r) => r.data),
};

// ── Patient Card ──
export const patientCardApi = {
  get: (patientId: number) =>
    api.get<PatientCard>(`/patient-card/${patientId}`).then((r) => r.data),
  qr: (patientId: number) =>
    api.get(`/patient-card/${patientId}/qr.png`, { responseType: "blob" }).then((r) => r.data),
  scan: (token: string) =>
    api.post("/patient-card/scan", { token }).then((r) => r.data),
  history: (patientId: number, params?: { limit?: number }) =>
    api.get(`/patient-card/${patientId}/history`, { params }).then((r) => r.data),
  print: (patientId: number) =>
    api.get(`/patient-card/${patientId}/print`).then((r) => r.data),
};

// ── ID Scan ──
export const idScanApi = {
  scan: (data: Record<string, unknown>) => api.post("/id-scan/scan", data).then((r) => r.data),
};

// ── Device Results ──
export const deviceApi = {
  submitResults: (data: Record<string, unknown>) =>
    api.post("/device/results", data).then((r) => r.data),
};

// ── Identity ──
export const identityApi = {
  linkNid: (data: { patient_id: number; national_id: string; confirm_name?: string }) =>
    api.post("/identity/link", data).then((r) => r.data),
  lookupByNid: (nationalId: string) =>
    api.get("/identity/lookup", { params: { national_id: nationalId } }).then((r) => r.data),
};

// ── National Identity ──
export const nationalIdentityApi = {
  verify: (data: Record<string, unknown>) => api.post("/national-id/verify", data).then((r) => r.data),
};

// ── Tiers / Subscription ──
export const tiersApi = {
  list: () => api.get<{ tiers: SubscriptionTier[] }>("/tiers").then((r) => r.data),
  my: () => api.get<SubscriptionInfo>("/tiers/my").then((r) => r.data),
  upgrade: (data: Record<string, unknown>) =>
    api.post("/tiers/upgrade", data).then((r) => r.data),
  demand: (data: { lab_id: number; target_tier: string; reason?: string }) =>
    api.post("/tiers/upgrade-demand", data).then((r) => r.data),
  adminDemands: (params?: { limit?: number }) =>
    api.get("/admin/tiers/demands", { params }).then((r) => r.data),
  adminSetTier: (labId: number, data: Record<string, unknown>) =>
    api.put(`/admin/tiers/${labId}`, data).then((r) => r.data),
  adminSetFlag: (labId: number, data: Record<string, unknown>) =>
    api.post(`/admin/tiers/flags/${labId}`, data).then((r) => r.data),
  adminListFlags: (labId: number) =>
    api.get(`/admin/tiers/flags/${labId}`).then((r) => r.data),
};

// ── AI v1 ──
export const aiApi = {
  suggest: (data: Record<string, unknown>) =>
    api.post("/api/ai/suggest", data).then((r) => r.data),
  pending: () => api.get("/api/ai/pending").then((r) => r.data),
  approve: (id: string) =>
    api.post(`/api/ai/approve/${id}`).then((r) => r.data),
  reject: (id: string, reason?: string) =>
    api.post(`/api/ai/reject/${id}`, { reason }).then((r) => r.data),
  execute: (id: string) =>
    api.post(`/api/ai/execute/${id}`).then((r) => r.data),
  analyzeOrder: (orderId: number) =>
    api.post(`/api/ai/analyze-order/${orderId}`).then((r) => r.data),
  operations: () => api.get("/api/ai/operations").then((r) => r.data),
  providers: () => api.get<AIProviderStatus>("/api/ai/providers").then((r) => r.data),
  criticalAlerts: (params?: { limit?: number }) =>
    api.get("/api/ai/critical-alerts", { params }).then((r) => r.data),
  interpret: (token: string) =>
    api.get<AIInterpretation>(`/api/ai/interpret/${token}`).then((r) => r.data),
  chat: (message: string, context?: string) =>
    api.post<AIChatResponse>("/api/ai/chat", { message, context }).then((r) => r.data),
};

// ── AI v2 Platform ──
export const aiPlatformApi = {
  search: (data: Record<string, unknown>) => api.post("/api/ai/v2/search", data).then((r) => r.data),
  index: (data: Record<string, unknown>) => api.post("/api/ai/v2/index", data).then((r) => r.data),
  embeddingInfo: () => api.get("/api/ai/v2/embedding-info").then((r) => r.data),
  ragQuery: (data: Record<string, unknown>) => api.post("/api/ai/v2/rag/query", data).then((r) => r.data),
  knowledgeGraphInfo: () => api.get("/api/ai/v2/knowledge-graph/info").then((r) => r.data),
  knowledgeGraphSearch: (data: Record<string, unknown>) => api.post("/api/ai/v2/knowledge-graph/search", data).then((r) => r.data),
  knowledgeGraphNode: (nodeId: string) => api.get(`/api/ai/v2/knowledge-graph/node/${nodeId}`).then((r) => r.data),
  knowledgeGraphPath: (params: { from: string; to: string }) => api.get("/api/ai/v2/knowledge-graph/path", { params }).then((r) => r.data),
  agentTools: () => api.get("/api/ai/v2/agents/tools").then((r) => r.data),
  agentExecute: (data: Record<string, unknown>) => api.post("/api/ai/v2/agents/execute", data).then((r) => r.data),
  orchestrate: (data: Record<string, unknown>) => api.post("/api/ai/v2/orchestrate", data).then((r) => r.data),
  orchestrateTasks: () => api.get("/api/ai/v2/orchestrate/tasks").then((r) => r.data),
  createSession: () => api.post("/api/ai/v2/sessions").then((r) => r.data),
  sessionMessage: (data: Record<string, unknown>) => api.post("/api/ai/v2/sessions/message", data).then((r) => r.data),
  sessionHistory: (sessionId: string) => api.get(`/api/ai/v2/sessions/${sessionId}`).then((r) => r.data),
  cdsEvaluate: (data: Record<string, unknown>) => api.post("/api/ai/v2/cds/evaluate", data).then((r) => r.data),
  cdsEvaluateOrder: (data: Record<string, unknown>) => api.post("/api/ai/v2/cds/evaluate-order", data).then((r) => r.data),
  governanceModels: () => api.get("/api/ai/v2/governance/models").then((r) => r.data),
  governancePrompts: () => api.get("/api/ai/v2/governance/prompts").then((r) => r.data),
  governanceEvaluations: () => api.get("/api/ai/v2/governance/evaluations").then((r) => r.data),
  securityScan: (data: Record<string, unknown>) => api.post("/api/ai/v2/security/scan", data).then((r) => r.data),
  metrics: () => api.get("/api/ai/v2/metrics").then((r) => r.data),
  metricsPrometheus: () => api.get("/api/ai/v2/metrics/prometheus").then((r) => r.data),
};

// ── AI Telemetry ──
export const aiTelemetryApi = {
  logInteraction: (data: Record<string, unknown>) => api.post("/api/ai/interactions", data).then((r) => r.data),
  logFeedback: (data: Record<string, unknown>) => api.post("/api/ai/feedback", data).then((r) => r.data),
  logUnresolved: (data: Record<string, unknown>) => api.post("/api/ai/unresolved", data).then((r) => r.data),
  safetyFlags: (data: Record<string, unknown>) => api.post("/api/ai/safety-flags", data).then((r) => r.data),
  export: (format: string) => api.get("/api/ai/export", { params: { format } }).then((r) => r.data),
  stats: () => api.get("/api/ai/stats").then((r) => r.data),
};

// ── Stats ──
export const statsApi = {
  dailyTrends: (params?: { days?: number }) =>
    api.get<TrendData>("/stats/trends/daily", { params }).then((r) => r.data),
  testFrequency: (params?: { days?: number; limit?: number }) =>
    api.get("/stats/trends/tests", { params }).then((r) => r.data),
  flagDistribution: (params?: { days?: number }) =>
    api.get<FlagDistribution>("/stats/trends/flags", { params }).then((r) => r.data),
  patientGrowth: (params?: { days?: number }) =>
    api.get("/stats/trends/patients", { params }).then((r) => r.data),
  summary: () => api.get<StatsSummary>("/stats/summary").then((r) => r.data),
  turnaround: (params?: { days?: number }) =>
    api.get<TurnaroundTime>("/stats/turnaround", { params }).then((r) => r.data),
};

// ── Metrics & Health ──
export const healthApi = {
  health: () => api.get("/health").then((r) => r.data),
  ready: () => api.get("/health/ready").then((r) => r.data),
  deep: () => api.get("/health/deep").then((r) => r.data),
  status: () => api.get("/health/status").then((r) => r.data),
};

export const metricsApi = {
  get: () => api.get("/metrics").then((r) => r.data),
  prom: () => api.get("/metrics/prom").then((r) => r.data),
};

// ── Security ──
export const securityApi = {
  status: () => api.get("/security/status").then((r) => r.data),
};

// ── Compliance ──
export const complianceApi = {
  info: () => api.get("/compliance/info").then((r) => r.data),
  auditSummary: () => api.get("/compliance/audit-summary").then((r) => r.data),
  fhirPatient: (patientId: number) =>
    api.get(`/compliance/fhir/patient/${patientId}`).then((r) => r.data),
  fhirObservation: (orderId: number) =>
    api.get(`/compliance/fhir/observation/${orderId}`).then((r) => r.data),
  fhirDiagnosticReport: (orderId: number) =>
    api.get(`/compliance/fhir/diagnostic-report/${orderId}`).then((r) => r.data),
  fhirServiceRequest: (orderId: number) =>
    api.get(`/compliance/fhir/service-request/${orderId}`).then((r) => r.data),
  dhis2Aggregate: () => api.get("/compliance/dhis2/aggregate").then((r) => r.data),
  auditIntegrity: () => api.get("/compliance/audit-integrity").then((r) => r.data),
  securityReport: () => api.get("/compliance/security-report").then((r) => r.data),
  timeSync: () => api.get("/compliance/time-sync").then((r) => r.data),
  systemStatus: () => api.get("/compliance/system-status").then((r) => r.data),
};

// ── MFA ──
export const mfaApi = {
  setupTotp: (deviceName?: string) =>
    api.post("/mfa/totp/setup", { device_name: deviceName }).then((r) => r.data),
  verifyTotp: (token: string) =>
    api.post("/mfa/totp/verify", { token }).then((r) => r.data),
  webauthnRegisterBegin: () => api.post("/mfa/webauthn/register/begin").then((r) => r.data),
  webauthnRegisterComplete: (data: Record<string, unknown>) => api.post("/mfa/webauthn/register/complete", data).then((r) => r.data),
  webauthnAuthBegin: () => api.post("/mfa/webauthn/authenticate/begin").then((r) => r.data),
  webauthnAuthComplete: (data: Record<string, unknown>) => api.post("/mfa/webauthn/authenticate/complete", data).then((r) => r.data),
  devices: () => api.get("/mfa/devices").then((r) => r.data),
  removeDevice: (deviceId: number) =>
    api.delete(`/mfa/devices/${deviceId}`).then((r) => r.data),
  status: () => api.get("/mfa/status").then((r) => r.data),
};

// ── Service Accounts ──
export const serviceAccountsApi = {
  list: () => api.get("/service-accounts").then((r) => r.data),
  create: (data: Record<string, unknown>) =>
    api.post("/service-accounts", data).then((r) => r.data),
  revoke: (id: string) =>
    api.post(`/service-accounts/${id}/revoke`).then((r) => r.data),
  rotate: (id: string) =>
    api.post(`/service-accounts/${id}/rotate`).then((r) => r.data),
};

// ── Canonical Patient ──
export const canonicalPatientApi = {
  create: (data: Record<string, unknown>) => api.post("/api/v1/canonical-patients", data).then((r) => r.data),
  get: (id: string) => api.get(`/api/v1/canonical-patients/${id}`).then((r) => r.data),
  merge: (data: Record<string, unknown>) => api.post("/api/v1/canonical-patients/merge", data).then((r) => r.data),
  byPatient: (patientId: number) => api.get(`/api/v1/canonical-patients/by-patient/${patientId}`).then((r) => r.data),
  byCitizen: (citizenId: string) => api.get(`/api/v1/canonical-patients/by-citizen/${citizenId}`).then((r) => r.data),
  search: (params?: Record<string, unknown>) => api.get("/api/v1/canonical-patients", { params }).then((r) => r.data),
  linkPatient: (data: Record<string, unknown>) => api.post("/api/v1/canonical-patients/link-patient", data).then((r) => r.data),
  linkCitizen: (data: Record<string, unknown>) => api.post("/api/v1/canonical-patients/link-citizen", data).then((r) => r.data),
};

// ── EHR (Electronic Health Record) ──
export const ehrApi = {
  // Clinical Notes
  createClinicalNote: (data: Record<string, unknown>) => api.post("/ehr/clinical-notes", data).then((r) => r.data),
  getClinicalNote: (id: number) => api.get(`/ehr/clinical-notes/${id}`).then((r) => r.data),
  updateClinicalNote: (id: number, data: Record<string, unknown>) => api.put(`/ehr/clinical-notes/${id}`, data).then((r) => r.data),
  deleteClinicalNote: (id: number) => api.delete(`/ehr/clinical-notes/${id}`).then((r) => r.data),
  listClinicalNotes: (params?: Record<string, unknown>) => api.get("/ehr/clinical-notes", { params }).then((r) => r.data),
  searchClinicalNotes: (params?: Record<string, unknown>) => api.get("/ehr/clinical-notes/search", { params }).then((r) => r.data),

  // Allergies
  createAllergy: (data: Record<string, unknown>) => api.post("/ehr/allergies", data).then((r) => r.data),
  getAllergy: (id: number) => api.get(`/ehr/allergies/${id}`).then((r) => r.data),
  updateAllergy: (id: number, data: Record<string, unknown>) => api.put(`/ehr/allergies/${id}`, data).then((r) => r.data),
  deleteAllergy: (id: number) => api.delete(`/ehr/allergies/${id}`).then((r) => r.data),
  listAllergies: (params?: Record<string, unknown>) => api.get("/ehr/allergies", { params }).then((r) => r.data),

  // Medication Statements
  createMedicationStatement: (data: Record<string, unknown>) => api.post("/ehr/medication-statements", data).then((r) => r.data),
  getMedicationStatement: (id: number) => api.get(`/ehr/medication-statements/${id}`).then((r) => r.data),
  updateMedicationStatement: (id: number, data: Record<string, unknown>) => api.put(`/ehr/medication-statements/${id}`, data).then((r) => r.data),
  deleteMedicationStatement: (id: number) => api.delete(`/ehr/medication-statements/${id}`).then((r) => r.data),
  listMedicationStatements: (params?: Record<string, unknown>) => api.get("/ehr/medication-statements", { params }).then((r) => r.data),

  // Medication Requests
  createMedicationRequest: (data: Record<string, unknown>) => api.post("/ehr/medication-requests", data).then((r) => r.data),
  getMedicationRequest: (id: number) => api.get(`/ehr/medication-requests/${id}`).then((r) => r.data),
  updateMedicationRequest: (id: number, data: Record<string, unknown>) => api.put(`/ehr/medication-requests/${id}`, data).then((r) => r.data),
  deleteMedicationRequest: (id: number) => api.delete(`/ehr/medication-requests/${id}`).then((r) => r.data),
  listMedicationRequests: (params?: Record<string, unknown>) => api.get("/ehr/medication-requests", { params }).then((r) => r.data),

  // Medication Dispenses
  createMedicationDispense: (data: Record<string, unknown>) => api.post("/ehr/medication-dispenses", data).then((r) => r.data),
  getMedicationDispense: (id: number) => api.get(`/ehr/medication-dispenses/${id}`).then((r) => r.data),
  updateMedicationDispense: (id: number, data: Record<string, unknown>) => api.put(`/ehr/medication-dispenses/${id}`, data).then((r) => r.data),
  deleteMedicationDispense: (id: number) => api.delete(`/ehr/medication-dispenses/${id}`).then((r) => r.data),
  listMedicationDispenses: (params?: Record<string, unknown>) => api.get("/ehr/medication-dispenses", { params }).then((r) => r.data),

  // Care Plans
  createCarePlan: (data: Record<string, unknown>) => api.post("/ehr/care-plans", data).then((r) => r.data),
  getCarePlan: (id: number) => api.get(`/ehr/care-plans/${id}`).then((r) => r.data),
  updateCarePlan: (id: number, data: Record<string, unknown>) => api.put(`/ehr/care-plans/${id}`, data).then((r) => r.data),
  deleteCarePlan: (id: number) => api.delete(`/ehr/care-plans/${id}`).then((r) => r.data),
  listCarePlans: (params?: Record<string, unknown>) => api.get("/ehr/care-plans", { params }).then((r) => r.data),
  addCarePlanGoal: (planId: number, data: Record<string, unknown>) => api.post(`/ehr/care-plans/${planId}/goals`, data).then((r) => r.data),
  updateCarePlanGoal: (planId: number, goalId: number, data: Record<string, unknown>) => api.put(`/ehr/care-plans/${planId}/goals/${goalId}`, data).then((r) => r.data),
  deleteCarePlanGoal: (planId: number, goalId: number) => api.delete(`/ehr/care-plans/${planId}/goals/${goalId}`).then((r) => r.data),

  // Problem List
  createProblemListItem: (data: Record<string, unknown>) => api.post("/ehr/problem-list", data).then((r) => r.data),
  getProblemListItem: (id: number) => api.get(`/ehr/problem-list/${id}`).then((r) => r.data),
  updateProblemListItem: (id: number, data: Record<string, unknown>) => api.put(`/ehr/problem-list/${id}`, data).then((r) => r.data),
  deleteProblemListItem: (id: number) => api.delete(`/ehr/problem-list/${id}`).then((r) => r.data),
  listProblemList: (params?: Record<string, unknown>) => api.get("/ehr/problem-list", { params }).then((r) => r.data),

  // Conditions
  createCondition: (data: Record<string, unknown>) => api.post("/ehr/conditions", data).then((r) => r.data),
  getCondition: (id: number) => api.get(`/ehr/conditions/${id}`).then((r) => r.data),
  updateCondition: (id: number, data: Record<string, unknown>) => api.put(`/ehr/conditions/${id}`, data).then((r) => r.data),
  deleteCondition: (id: number) => api.delete(`/ehr/conditions/${id}`).then((r) => r.data),
  listConditions: (params?: Record<string, unknown>) => api.get("/ehr/conditions", { params }).then((r) => r.data),

  // Diagnoses
  createDiagnosis: (data: Record<string, unknown>) => api.post("/ehr/diagnoses", data).then((r) => r.data),
  getDiagnosis: (id: number) => api.get(`/ehr/diagnoses/${id}`).then((r) => r.data),
  updateDiagnosis: (id: number, data: Record<string, unknown>) => api.put(`/ehr/diagnoses/${id}`, data).then((r) => r.data),
  deleteDiagnosis: (id: number) => api.delete(`/ehr/diagnoses/${id}`).then((r) => r.data),
  listDiagnoses: (params?: Record<string, unknown>) => api.get("/ehr/diagnoses", { params }).then((r) => r.data),

  // Family History
  createFamilyHistory: (data: Record<string, unknown>) => api.post("/ehr/family-history", data).then((r) => r.data),
  getFamilyHistory: (id: number) => api.get(`/ehr/family-history/${id}`).then((r) => r.data),
  updateFamilyHistory: (id: number, data: Record<string, unknown>) => api.put(`/ehr/family-history/${id}`, data).then((r) => r.data),
  deleteFamilyHistory: (id: number) => api.delete(`/ehr/family-history/${id}`).then((r) => r.data),
  listFamilyHistory: (params?: Record<string, unknown>) => api.get("/ehr/family-history", { params }).then((r) => r.data),

  // Social History
  createSocialHistory: (data: Record<string, unknown>) => api.post("/ehr/social-history", data).then((r) => r.data),
  getSocialHistory: (id: number) => api.get(`/ehr/social-history/${id}`).then((r) => r.data),
  updateSocialHistory: (id: number, data: Record<string, unknown>) => api.put(`/ehr/social-history/${id}`, data).then((r) => r.data),
  deleteSocialHistory: (id: number) => api.delete(`/ehr/social-history/${id}`).then((r) => r.data),
  listSocialHistory: (params?: Record<string, unknown>) => api.get("/ehr/social-history", { params }).then((r) => r.data),

  // Risk Factors
  createRiskFactor: (data: Record<string, unknown>) => api.post("/ehr/risk-factors", data).then((r) => r.data),
  getRiskFactor: (id: number) => api.get(`/ehr/risk-factors/${id}`).then((r) => r.data),
  updateRiskFactor: (id: number, data: Record<string, unknown>) => api.put(`/ehr/risk-factors/${id}`, data).then((r) => r.data),
  deleteRiskFactor: (id: number) => api.delete(`/ehr/risk-factors/${id}`).then((r) => r.data),
  listRiskFactors: (params?: Record<string, unknown>) => api.get("/ehr/risk-factors", { params }).then((r) => r.data),

  // Immunizations
  createImmunization: (data: Record<string, unknown>) => api.post("/ehr/immunizations", data).then((r) => r.data),
  getImmunization: (id: number) => api.get(`/ehr/immunizations/${id}`).then((r) => r.data),
  updateImmunization: (id: number, data: Record<string, unknown>) => api.put(`/ehr/immunizations/${id}`, data).then((r) => r.data),
  deleteImmunization: (id: number) => api.delete(`/ehr/immunizations/${id}`).then((r) => r.data),
  listImmunizations: (params?: Record<string, unknown>) => api.get("/ehr/immunizations", { params }).then((r) => r.data),

  // Attachments
  createAttachment: (data: Record<string, unknown>) => api.post("/ehr/attachments", data).then((r) => r.data),
  getAttachment: (id: number) => api.get(`/ehr/attachments/${id}`).then((r) => r.data),
  updateAttachment: (id: number, data: Record<string, unknown>) => api.put(`/ehr/attachments/${id}`, data).then((r) => r.data),
  deleteAttachment: (id: number) => api.delete(`/ehr/attachments/${id}`).then((r) => r.data),
  listAttachments: (params?: Record<string, unknown>) => api.get("/ehr/attachments", { params }).then((r) => r.data),
  downloadAttachment: (id: number) => api.get(`/ehr/attachments/${id}/download`, { responseType: "blob" }).then((r) => r.data),

  // Patient Summary
  getPatientEhr: (patientId: number) => api.get(`/ehr/patient/${patientId}`).then((r) => r.data),
  getPatientSummary: (patientId: number) => api.get(`/ehr/patient/${patientId}/summary`).then((r) => r.data),
};

// ── EHR FHIR (all FHIR resources) ──
export const ehrFhirApi = {
  getPatient: (id: string) => api.get(`/fhir/Patient/${id}`).then((r) => r.data),
  getEncounter: (id: string) => api.get(`/fhir/Encounter/${id}`).then((r) => r.data),
  getCondition: (id: string) => api.get(`/fhir/Condition/${id}`).then((r) => r.data),
  searchConditions: (params?: Record<string, unknown>) => api.get("/fhir/Condition", { params }).then((r) => r.data),
  getObservation: (id: string) => api.get(`/fhir/Observation/${id}`).then((r) => r.data),
  searchObservations: (params?: Record<string, unknown>) => api.get("/fhir/Observation", { params }).then((r) => r.data),
  getMedicationRequest: (id: string) => api.get(`/fhir/MedicationRequest/${id}`).then((r) => r.data),
  searchMedicationRequests: (params?: Record<string, unknown>) => api.get("/fhir/MedicationRequest", { params }).then((r) => r.data),
  getMedicationStatement: (id: string) => api.get(`/fhir/MedicationStatement/${id}`).then((r) => r.data),
  getCarePlan: (id: string) => api.get(`/fhir/CarePlan/${id}`).then((r) => r.data),
  getProcedure: (id: string) => api.get(`/fhir/Procedure/${id}`).then((r) => r.data),
  searchProcedures: (params?: Record<string, unknown>) => api.get("/fhir/Procedure", { params }).then((r) => r.data),
  getAllergyIntolerance: (id: string) => api.get(`/fhir/AllergyIntolerance/${id}`).then((r) => r.data),
  searchAllergyIntolerances: (params?: Record<string, unknown>) => api.get("/fhir/AllergyIntolerance", { params }).then((r) => r.data),
  getImmunization: (id: string) => api.get(`/fhir/Immunization/${id}`).then((r) => r.data),
  searchImmunizations: (params?: Record<string, unknown>) => api.get("/fhir/Immunization", { params }).then((r) => r.data),
  getDocumentReference: (id: string) => api.get(`/fhir/DocumentReference/${id}`).then((r) => r.data),
  searchDocumentReferences: (params?: Record<string, unknown>) => api.get("/fhir/DocumentReference", { params }).then((r) => r.data),
  getComposition: (id: string) => api.get(`/fhir/Composition/${id}`).then((r) => r.data),
  searchCompositions: (params?: Record<string, unknown>) => api.get("/fhir/Composition", { params }).then((r) => r.data),
  getBundle: (id: string) => api.get(`/fhir/Bundle/${id}`).then((r) => r.data),
  createResource: (resourceType: string, data: Record<string, unknown>) => api.post(`/fhir/${resourceType}`, data).then((r) => r.data),
  updateResource: (resourceType: string, id: string, data: Record<string, unknown>) => api.put(`/fhir/${resourceType}/${id}`, data).then((r) => r.data),
  deleteResource: (resourceType: string, id: string) => api.delete(`/fhir/${resourceType}/${id}`).then((r) => r.data),
  executeBatch: (data: Record<string, unknown>) => api.post("/fhir", data).then((r) => r.data),
};

// ── Care Continuum ──
export const careContinuumApi = {
  // Primary Care
  createPrimaryCareEncounter: (data: Record<string, unknown>) => api.post("/care-continuum/primary-care-encounters", data).then((r) => r.data),
  getPrimaryCareEncounter: (id: number) => api.get(`/care-continuum/primary-care-encounters/${id}`).then((r) => r.data),
  listPrimaryCareEncounters: (params?: Record<string, unknown>) => api.get("/care-continuum/primary-care-encounters", { params }).then((r) => r.data),
  updatePrimaryCareEncounter: (id: number, data: Record<string, unknown>) => api.put(`/care-continuum/primary-care-encounters/${id}`, data).then((r) => r.data),

  // Family Medicine
  createFamilyMedicineRecord: (data: Record<string, unknown>) => api.post("/care-continuum/family-medicine-records", data).then((r) => r.data),
  getFamilyMedicineRecord: (id: number) => api.get(`/care-continuum/family-medicine-records/${id}`).then((r) => r.data),

  // Community Clinic
  createCommunityClinicRecord: (data: Record<string, unknown>) => api.post("/care-continuum/community-clinic-records", data).then((r) => r.data),
  getCommunityClinicRecord: (id: number) => api.get(`/care-continuum/community-clinic-records/${id}`).then((r) => r.data),

  // Health Assessments
  createHealthAssessment: (data: Record<string, unknown>) => api.post("/care-continuum/health-assessments", data).then((r) => r.data),
  listHealthAssessments: (params?: Record<string, unknown>) => api.get("/care-continuum/health-assessments", { params }).then((r) => r.data),

  // Preventive Care
  createPreventiveCareRecord: (data: Record<string, unknown>) => api.post("/care-continuum/preventive-care-records", data).then((r) => r.data),
  getPreventiveCareRecord: (id: number) => api.get(`/care-continuum/preventive-care-records/${id}`).then((r) => r.data),

  // Referrals
  createReferral: (data: Record<string, unknown>) => api.post("/care-continuum/referrals", data).then((r) => r.data),
  acceptReferral: (id: number) => api.put(`/care-continuum/referrals/${id}/accept`).then((r) => r.data),
  rejectReferral: (id: number) => api.put(`/care-continuum/referrals/${id}/reject`).then((r) => r.data),
  updateReferral: (id: number, data: Record<string, unknown>) => api.put(`/care-continuum/referrals/${id}`, data).then((r) => r.data),
  listReferrals: (params?: Record<string, unknown>) => api.get("/care-continuum/referrals", { params }).then((r) => r.data),
  getReferral: (id: number) => api.get(`/care-continuum/referrals/${id}`).then((r) => r.data),

  // Care Journeys
  createCareJourney: (data: Record<string, unknown>) => api.post("/care-continuum/care-journeys", data).then((r) => r.data),
  getCareJourney: (id: number) => api.get(`/care-continuum/care-journeys/${id}`).then((r) => r.data),
  listCareJourneys: (params?: Record<string, unknown>) => api.get("/care-continuum/care-journeys", { params }).then((r) => r.data),

  // Follow-up Plans
  createFollowUpPlan: (data: Record<string, unknown>) => api.post("/care-continuum/follow-up-plans", data).then((r) => r.data),
  listFollowUpPlans: (params?: Record<string, unknown>) => api.get("/care-continuum/follow-up-plans", { params }).then((r) => r.data),

  // Care Coordination
  createCareCoordination: (data: Record<string, unknown>) => api.post("/care-continuum/care-coordination", data).then((r) => r.data),
  listCareCoordination: (params?: Record<string, unknown>) => api.get("/care-continuum/care-coordination", { params }).then((r) => r.data),

  // Transitions of Care
  createTransitionOfCare: (data: Record<string, unknown>) => api.post("/care-continuum/transitions-of-care", data).then((r) => r.data),
  createClinicalHandover: (data: Record<string, unknown>) => api.post("/care-continuum/clinical-handovers", data).then((r) => r.data),

  // Home Care
  createHomeCarePlan: (data: Record<string, unknown>) => api.post("/care-continuum/home-care-plans", data).then((r) => r.data),
  listHomeCarePlans: (params?: Record<string, unknown>) => api.get("/care-continuum/home-care-plans", { params }).then((r) => r.data),

  // Community Care
  createCommunityCareRecord: (data: Record<string, unknown>) => api.post("/care-continuum/community-care-records", data).then((r) => r.data),
  getCommunityCareRecord: (id: number) => api.get(`/care-continuum/community-care-records/${id}`).then((r) => r.data),

  // Maternal Health
  createPregnancyRecord: (data: Record<string, unknown>) => api.post("/care-continuum/pregnancy-records", data).then((r) => r.data),
  getPregnancyRecord: (id: number) => api.get(`/care-continuum/pregnancy-records/${id}`).then((r) => r.data),
  listPregnancyRecords: (params?: Record<string, unknown>) => api.get("/care-continuum/pregnancy-records", { params }).then((r) => r.data),
  createDeliveryRecord: (data: Record<string, unknown>) => api.post("/care-continuum/delivery-records", data).then((r) => r.data),
  createGrowthMonitoringRecord: (data: Record<string, unknown>) => api.post("/care-continuum/growth-monitoring", data).then((r) => r.data),

  // Vaccinations
  createVaccinationRecord: (data: Record<string, unknown>) => api.post("/care-continuum/vaccination-records", data).then((r) => r.data),
  getVaccinationRecord: (id: number) => api.get(`/care-continuum/vaccination-records/${id}`).then((r) => r.data),

  // Reminders
  createReminderSchedule: (data: Record<string, unknown>) => api.post("/care-continuum/reminder-schedules", data).then((r) => r.data),
  getReminderSchedule: (id: number) => api.get(`/care-continuum/reminder-schedules/${id}`).then((r) => r.data),

  // Health Programs
  createHealthProgram: (data: Record<string, unknown>) => api.post("/care-continuum/health-programs", data).then((r) => r.data),
  listHealthPrograms: (params?: Record<string, unknown>) => api.get("/care-continuum/health-programs", { params }).then((r) => r.data),

  // Community Visits
  createCommunityVisit: (data: Record<string, unknown>) => api.post("/care-continuum/community-visits", data).then((r) => r.data),

  // Patient Tasks
  createPatientTask: (data: Record<string, unknown>) => api.post("/care-continuum/patient-tasks", data).then((r) => r.data),
  listPatientTasks: (params?: Record<string, unknown>) => api.get("/care-continuum/patient-tasks", { params }).then((r) => r.data),

  // Population Health
  createPopulationHealthRecord: (data: Record<string, unknown>) => api.post("/care-continuum/population-health", data).then((r) => r.data),
  createChronicDiseaseRecord: (data: Record<string, unknown>) => api.post("/care-continuum/chronic-disease", data).then((r) => r.data),
  createMentalHealthRecord: (data: Record<string, unknown>) => api.post("/care-continuum/mental-health", data).then((r) => r.data),
};

// ── Clinical ──
export const clinicalFullApi = {
  // Terminology
  listCodes: (params?: Record<string, unknown>) => api.get("/clinical/terminology/codes", { params }).then((r) => r.data),
  createCode: (data: Record<string, unknown>) => api.post("/clinical/terminology/codes", data).then((r) => r.data),
  getCode: (id: number) => api.get(`/clinical/terminology/codes/${id}`).then((r) => r.data),
  updateCode: (id: number, data: Record<string, unknown>) => api.put(`/clinical/terminology/codes/${id}`, data).then((r) => r.data),
  deleteCode: (id: number) => api.delete(`/clinical/terminology/codes/${id}`).then((r) => r.data),
  listTerminologyVersions: () => api.get("/clinical/terminology/versions").then((r) => r.data),
  createTerminologyVersion: (data: Record<string, unknown>) => api.post("/clinical/terminology/versions", data).then((r) => r.data),
  createMapping: (data: Record<string, unknown>) => api.post("/clinical/terminology/mappings", data).then((r) => r.data),
  listValueSets: (params?: Record<string, unknown>) => api.get("/clinical/terminology/value-sets", { params }).then((r) => r.data),
  createValueSet: (data: Record<string, unknown>) => api.post("/clinical/terminology/value-sets", data).then((r) => r.data),
  createValueSetMember: (data: Record<string, unknown>) => api.post("/clinical/terminology/value-set-members", data).then((r) => r.data),
  listCodeSystems: (params?: Record<string, unknown>) => api.get("/clinical/terminology/code-systems", { params }).then((r) => r.data),
  createCodeSystem: (data: Record<string, unknown>) => api.post("/clinical/terminology/code-systems", data).then((r) => r.data),
  searchIcd10: (params?: Record<string, unknown>) => api.get("/clinical/terminology/icd10", { params }).then((r) => r.data),
  searchLoinc: (params?: Record<string, unknown>) => api.get("/clinical/terminology/loinc", { params }).then((r) => r.data),
  searchSnomed: (params?: Record<string, unknown>) => api.get("/clinical/terminology/snomed", { params }).then((r) => r.data),
  fhirExpandValueSet: (params?: Record<string, unknown>) => api.get("/clinical/terminology/fhir/$expand", { params }).then((r) => r.data),
  fhirLookupCode: (params?: Record<string, unknown>) => api.get("/clinical/terminology/fhir/$lookup", { params }).then((r) => r.data),

  // Knowledge
  listGuidelines: (params?: Record<string, unknown>) => api.get("/clinical/knowledge/guidelines", { params }).then((r) => r.data),
  createGuideline: (data: Record<string, unknown>) => api.post("/clinical/knowledge/guidelines", data).then((r) => r.data),
  getGuideline: (id: number) => api.get(`/clinical/knowledge/guidelines/${id}`).then((r) => r.data),
  updateGuideline: (id: number, data: Record<string, unknown>) => api.put(`/clinical/knowledge/guidelines/${id}`, data).then((r) => r.data),
  listProtocols: (params?: Record<string, unknown>) => api.get("/clinical/knowledge/protocols", { params }).then((r) => r.data),
  createProtocol: (data: Record<string, unknown>) => api.post("/clinical/knowledge/protocols", data).then((r) => r.data),
  getProtocol: (id: number) => api.get(`/clinical/knowledge/protocols/${id}`).then((r) => r.data),
  updateProtocol: (id: number, data: Record<string, unknown>) => api.put(`/clinical/knowledge/protocols/${id}`, data).then((r) => r.data),
  listPathways: (params?: Record<string, unknown>) => api.get("/clinical/knowledge/pathways", { params }).then((r) => r.data),
  createPathway: (data: Record<string, unknown>) => api.post("/clinical/knowledge/pathways", data).then((r) => r.data),
  getPathway: (id: number) => api.get(`/clinical/knowledge/pathways/${id}`).then((r) => r.data),
  updatePathway: (id: number, data: Record<string, unknown>) => api.put(`/clinical/knowledge/pathways/${id}`, data).then((r) => r.data),
  approveGuideline: (id: number, data: Record<string, unknown>) => api.post(`/clinical/knowledge/guidelines/${id}/approvals`, data).then((r) => r.data),
  listStandingOrders: (params?: Record<string, unknown>) => api.get("/clinical/knowledge/standing-orders", { params }).then((r) => r.data),
  createStandingOrder: (data: Record<string, unknown>) => api.post("/clinical/knowledge/standing-orders", data).then((r) => r.data),
  listRecommendations: (params?: Record<string, unknown>) => api.get("/clinical/knowledge/recommendations", { params }).then((r) => r.data),

  // CDS (Clinical Decision Support)
  getOrderSetRecommendations: (data: Record<string, unknown>) => api.post("/clinical/cds/order-set-recommendations", data).then((r) => r.data),
  checkContraindication: (data: Record<string, unknown>) => api.post("/clinical/cds/contraindication-check", data).then((r) => r.data),
  checkDuplicateOrder: (data: Record<string, unknown>) => api.post("/clinical/cds/duplicate-order-check", data).then((r) => r.data),
  checkDrugInteraction: (data: Record<string, unknown>) => api.post("/clinical/cds/drug-interaction-check", data).then((r) => r.data),
  createAlert: (data: Record<string, unknown>) => api.post("/clinical/cds/alerts", data).then((r) => r.data),
  listAlerts: (params?: Record<string, unknown>) => api.get("/clinical/cds/alerts", { params }).then((r) => r.data),
  acknowledgeAlert: (id: number) => api.put(`/clinical/cds/alerts/${id}/acknowledge`).then((r) => r.data),
  listReminders: (params?: Record<string, unknown>) => api.get("/clinical/cds/reminders", { params }).then((r) => r.data),
  checkCareBundleCompliance: (data: Record<string, unknown>) => api.post("/clinical/cds/care-bundle-compliance", data).then((r) => r.data),

  // Quality
  listQualityIndicators: () => api.get("/clinical/quality/indicators").then((r) => r.data),
  createQualityIndicator: (data: Record<string, unknown>) => api.post("/clinical/quality/indicators", data).then((r) => r.data),
  createQualityMeasurement: (data: Record<string, unknown>) => api.post("/clinical/quality/measurements", data).then((r) => r.data),
  listAuditRecords: (params?: Record<string, unknown>) => api.get("/clinical/quality/audit-records", { params }).then((r) => r.data),
  createAuditRecord: (data: Record<string, unknown>) => api.post("/clinical/quality/audit-records", data).then((r) => r.data),
  createComplianceCheck: (data: Record<string, unknown>) => api.post("/clinical/quality/compliance-checks", data).then((r) => r.data),
  listComplianceChecks: (params?: Record<string, unknown>) => api.get("/clinical/quality/compliance-checks", { params }).then((r) => r.data),
  listBenchmarks: (params?: Record<string, unknown>) => api.get("/clinical/quality/benchmarks", { params }).then((r) => r.data),
  createMortalityReview: (data: Record<string, unknown>) => api.post("/clinical/quality/mortality-reviews", data).then((r) => r.data),
  createIncidentReport: (data: Record<string, unknown>) => api.post("/clinical/quality/incident-reports", data).then((r) => r.data),
  createSafetyEvent: (data: Record<string, unknown>) => api.post("/clinical/quality/safety-events", data).then((r) => r.data),
  getQualityDashboard: (params?: Record<string, unknown>) => api.get("/clinical/quality/dashboard", { params }).then((r) => r.data),

  // Research
  createRegistry: (data: Record<string, unknown>) => api.post("/clinical/research/registries", data).then((r) => r.data),
  listRegistries: (params?: Record<string, unknown>) => api.get("/clinical/research/registries", { params }).then((r) => r.data),
  createCohort: (data: Record<string, unknown>) => api.post("/clinical/research/cohorts", data).then((r) => r.data),
  listCohorts: (params?: Record<string, unknown>) => api.get("/clinical/research/cohorts", { params }).then((r) => r.data),
  exportDeidentified: (data: Record<string, unknown>) => api.post("/clinical/research/export-deidentified", data).then((r) => r.data),

  // Clinical AI
  copilot: (data: Record<string, unknown>) => api.post("/clinical/ai/copilot", data).then((r) => r.data),
  riskPrediction: (data: Record<string, unknown>) => api.post("/clinical/ai/risk-prediction", data).then((r) => r.data),
  careGaps: (data: Record<string, unknown>) => api.post("/clinical/ai/care-gaps", data).then((r) => r.data),
  diagnosticAssistant: (data: Record<string, unknown>) => api.post("/clinical/ai/diagnostic-assistant", data).then((r) => r.data),
  explainAI: (data: Record<string, unknown>) => api.post("/clinical/ai/explain", data).then((r) => r.data),
};

// ── Clinical Documentation ──
export const clinicalDocumentationApi = {
  createSoapNote: (data: Record<string, unknown>) => api.post("/clinical/documentation/soap-notes", data).then((r) => r.data),
  createProgressNote: (data: Record<string, unknown>) => api.post("/clinical/documentation/progress-notes", data).then((r) => r.data),
  createNursingNote: (data: Record<string, unknown>) => api.post("/clinical/documentation/nursing-notes", data).then((r) => r.data),
  createConsultationNote: (data: Record<string, unknown>) => api.post("/clinical/documentation/consultation-notes", data).then((r) => r.data),
  createOperationNote: (data: Record<string, unknown>) => api.post("/clinical/documentation/operation-notes", data).then((r) => r.data),
  createEmergencyNote: (data: Record<string, unknown>) => api.post("/clinical/documentation/emergency-notes", data).then((r) => r.data),
  list: (params?: Record<string, unknown>) => api.get("/clinical/documentation", { params }).then((r) => r.data),
  get: (id: number) => api.get(`/clinical/documentation/${id}`).then((r) => r.data),
  listTemplates: (params?: Record<string, unknown>) => api.get("/clinical/documentation/templates", { params }).then((r) => r.data),
  createTemplate: (data: Record<string, unknown>) => api.post("/clinical/documentation/templates", data).then((r) => r.data),
  sign: (data: Record<string, unknown>) => api.post("/clinical/documentation/sign", data).then((r) => r.data),
  getVersions: (id: number) => api.get(`/clinical/documentation/${id}/versions`).then((r) => r.data),
};

// ── Clinical Orders ──
export const clinicalOrdersApi = {
  create: (data: Record<string, unknown>) => api.post("/clinical/orders", data).then((r) => r.data),
  list: (params?: Record<string, unknown>) => api.get("/clinical/orders", { params }).then((r) => r.data),
  get: (id: number) => api.get(`/clinical/orders/${id}`).then((r) => r.data),
  cancel: (id: number) => api.put(`/clinical/orders/${id}/cancel`).then((r) => r.data),
  complete: (id: number) => api.put(`/clinical/orders/${id}/complete`).then((r) => r.data),
  listTemplates: (params?: Record<string, unknown>) => api.get("/clinical/orders/templates", { params }).then((r) => r.data),
  createTemplate: (data: Record<string, unknown>) => api.post("/clinical/orders/templates", data).then((r) => r.data),
  createRecurring: (data: Record<string, unknown>) => api.post("/clinical/orders/recurring", data).then((r) => r.data),
  listRecurring: (params?: Record<string, unknown>) => api.get("/clinical/orders/recurring", { params }).then((r) => r.data),
  listStanding: (params?: Record<string, unknown>) => api.get("/clinical/orders/standing", { params }).then((r) => r.data),
};

// ── Clinical Quality ──
export const clinicalQualityApi = {
  kpis: (params?: Record<string, unknown>) => api.get("/clinical/quality/kpis", { params }).then((r) => r.data),
  createMeasurement: (data: Record<string, unknown>) => api.post("/clinical/quality/measurements", data).then((r) => r.data),
  complianceDashboard: (params?: Record<string, unknown>) => api.get("/clinical/quality/compliance-dashboard", { params }).then((r) => r.data),
  benchmarks: (params?: Record<string, unknown>) => api.get("/clinical/quality/benchmarks", { params }).then((r) => r.data),
};

// ── Hospital ──
export const hospitalApi = {
  list: (params?: Record<string, unknown>) => api.get("/hospital", { params }).then((r) => r.data),
  get: (id: number) => api.get(`/hospital/${id}`).then((r) => r.data),
  create: (data: Record<string, unknown>) => api.post("/hospital", data).then((r) => r.data),
  update: (id: number, data: Record<string, unknown>) => api.put(`/hospital/${id}`, data).then((r) => r.data),
  deactivate: (id: number) => api.delete(`/hospital/${id}`).then((r) => r.data),

  // Campuses
  listCampuses: (hospitalId: number) => api.get(`/hospital/${hospitalId}/campuses`).then((r) => r.data),
  createCampus: (hospitalId: number, data: Record<string, unknown>) => api.post(`/hospital/${hospitalId}/campuses`, data).then((r) => r.data),
  updateCampus: (campusId: number, data: Record<string, unknown>) => api.put(`/hospital/campuses/${campusId}`, data).then((r) => r.data),
  listBuildings: (campusId: number) => api.get(`/hospital/campuses/${campusId}/buildings`).then((r) => r.data),
  createBuilding: (campusId: number, data: Record<string, unknown>) => api.post(`/hospital/campuses/${campusId}/buildings`, data).then((r) => r.data),
  listFloors: (buildingId: number) => api.get(`/hospital/buildings/${buildingId}/floors`).then((r) => r.data),
  createFloor: (buildingId: number, data: Record<string, unknown>) => api.post(`/hospital/buildings/${buildingId}/floors`, data).then((r) => r.data),

  // Departments
  listDepartments: (hospitalId: number) => api.get(`/hospital/${hospitalId}/departments`).then((r) => r.data),
  createDepartment: (hospitalId: number, data: Record<string, unknown>) => api.post(`/hospital/${hospitalId}/departments`, data).then((r) => r.data),
  updateDepartment: (deptId: number, data: Record<string, unknown>) => api.put(`/hospital/departments/${deptId}`, data).then((r) => r.data),
  listClinics: (deptId: number) => api.get(`/hospital/departments/${deptId}/clinics`).then((r) => r.data),
  createClinic: (deptId: number, data: Record<string, unknown>) => api.post(`/hospital/departments/${deptId}/clinics`, data).then((r) => r.data),

  // Rooms & Beds
  listRooms: (deptId: number) => api.get(`/hospital/departments/${deptId}/rooms`).then((r) => r.data),
  createRoom: (deptId: number, data: Record<string, unknown>) => api.post(`/hospital/departments/${deptId}/rooms`, data).then((r) => r.data),
  listBeds: (roomId: number) => api.get(`/hospital/rooms/${roomId}/beds`).then((r) => r.data),
  createBed: (roomId: number, data: Record<string, unknown>) => api.post(`/hospital/rooms/${roomId}/beds`, data).then((r) => r.data),
  assignBed: (bedId: number, data: Record<string, unknown>) => api.post(`/hospital/beds/${bedId}/assign`, data).then((r) => r.data),
  dischargeBed: (bedId: number) => api.post(`/hospital/beds/${bedId}/discharge`).then((r) => r.data),
  transferBed: (bedId: number, data: Record<string, unknown>) => api.post(`/hospital/beds/${bedId}/transfer`, data).then((r) => r.data),
  bedAssignmentHistory: (bedId: number) => api.get(`/hospital/beds/${bedId}/assignments`).then((r) => r.data),
  occupancy: (params?: Record<string, unknown>) => api.get("/hospital/occupancy", { params }).then((r) => r.data),

  // Units
  listUnits: (hospitalId: number) => api.get(`/hospital/${hospitalId}/units`).then((r) => r.data),
  createUnit: (hospitalId: number, data: Record<string, unknown>) => api.post(`/hospital/${hospitalId}/units`, data).then((r) => r.data),

  // Operation Theaters
  listOperationTheaters: (hospitalId: number) => api.get(`/hospital/${hospitalId}/operation-theaters`).then((r) => r.data),
  createOperationTheater: (hospitalId: number, data: Record<string, unknown>) => api.post(`/hospital/${hospitalId}/operation-theaters`, data).then((r) => r.data),
  updateOperationTheaterStatus: (otId: number, data: Record<string, unknown>) => api.put(`/hospital/operation-theaters/${otId}/status`, data).then((r) => r.data),

  // Equipment
  listEquipment: (hospitalId: number) => api.get(`/hospital/${hospitalId}/equipment`).then((r) => r.data),
  createEquipment: (hospitalId: number, data: Record<string, unknown>) => api.post(`/hospital/${hospitalId}/equipment`, data).then((r) => r.data),
  updateEquipment: (equipId: number, data: Record<string, unknown>) => api.put(`/hospital/equipment/${equipId}`, data).then((r) => r.data),

  // Cost Centers
  listCostCenters: (hospitalId: number) => api.get(`/hospital/${hospitalId}/cost-centers`).then((r) => r.data),
  createCostCenter: (hospitalId: number, data: Record<string, unknown>) => api.post(`/hospital/${hospitalId}/cost-centers`, data).then((r) => r.data),

  // Appointments
  listAppointments: (params?: Record<string, unknown>) => api.get("/hospital/appointments", { params }).then((r) => r.data),
  createAppointment: (data: Record<string, unknown>) => api.post("/hospital/appointments", data).then((r) => r.data),

  // Dashboard
  getDashboard: (hospitalId: number) => api.get(`/hospital/${hospitalId}/dashboard`).then((r) => r.data),
};

// ── National Data ──
export const nationalDataApi = {
  // Patients
  listPatients: (params?: Record<string, unknown>) => api.get("/national-data/patients", { params }).then((r) => r.data),
  getPatient: (id: string) => api.get(`/national-data/patients/${id}`).then((r) => r.data),

  // Encounters
  listEncounters: (params?: Record<string, unknown>) => api.get("/national-data/encounters", { params }).then((r) => r.data),
  getEncounter: (id: string) => api.get(`/national-data/encounters/${id}`).then((r) => r.data),
  createEncounter: (data: Record<string, unknown>) => api.post("/national-data/encounters", data).then((r) => r.data),

  // Observations
  listObservations: (params?: Record<string, unknown>) => api.get("/national-data/observations", { params }).then((r) => r.data),
  getObservation: (id: string) => api.get(`/national-data/observations/${id}`).then((r) => r.data),
  createObservation: (data: Record<string, unknown>) => api.post("/national-data/observations", data).then((r) => r.data),

  // Golden Records
  listGoldenRecords: (params?: Record<string, unknown>) => api.get("/national-data/golden-records", { params }).then((r) => r.data),
  createGoldenRecord: (data: Record<string, unknown>) => api.post("/national-data/golden-records", data).then((r) => r.data),
  resolveGoldenRecord: (id: string) => api.post(`/national-data/golden-records/${id}/resolve`).then((r) => r.data),

  // Duplicate Check & Merge
  duplicateCheck: (data: Record<string, unknown>) => api.post("/national-data/duplicate-check", data).then((r) => r.data),
  merge: (data: Record<string, unknown>) => api.post("/national-data/merge", data).then((r) => r.data),

  // Events
  recordEvent: (data: Record<string, unknown>) => api.post("/national-data/events", data).then((r) => r.data),
  replayEvents: (params?: Record<string, unknown>) => api.get("/national-data/events/replay", { params }).then((r) => r.data),

  // Data Catalog
  listDataCatalog: (params?: Record<string, unknown>) => api.get("/national-data/data-catalog", { params }).then((r) => r.data),
  createDataCatalogEntry: (data: Record<string, unknown>) => api.post("/national-data/data-catalog", data).then((r) => r.data),

  // Data Quality
  recordDataQualityCheck: (data: Record<string, unknown>) => api.post("/national-data/data-quality-checks", data).then((r) => r.data),
  getDataLineage: (params?: Record<string, unknown>) => api.get("/national-data/data-lineage", { params }).then((r) => r.data),
  recordDataLineage: (data: Record<string, unknown>) => api.post("/national-data/data-lineage", data).then((r) => r.data),

  // Retention & Consent
  listRetentionPolicies: () => api.get("/national-data/retention-policies").then((r) => r.data),
  createRetentionPolicy: (data: Record<string, unknown>) => api.post("/national-data/retention-policies", data).then((r) => r.data),
  listConsentDirectives: (params?: Record<string, unknown>) => api.get("/national-data/consent-directives", { params }).then((r) => r.data),
  createConsentDirective: (data: Record<string, unknown>) => api.post("/national-data/consent-directives", data).then((r) => r.data),

  // De-identification
  createDeidentificationJob: (data: Record<string, unknown>) => api.post("/national-data/deidentification-jobs", data).then((r) => r.data),
  listDeidentificationJobs: (params?: Record<string, unknown>) => api.get("/national-data/deidentification-jobs", { params }).then((r) => r.data),

  // Features & ML
  listFeatureDefinitions: () => api.get("/national-data/features").then((r) => r.data),
  createFeatureDefinition: (data: Record<string, unknown>) => api.post("/national-data/features", data).then((r) => r.data),
  storeFeatureValues: (data: Record<string, unknown>) => api.post("/national-data/feature-values", data).then((r) => r.data),
  getFeatureValues: (params?: Record<string, unknown>) => api.get("/national-data/feature-values", { params }).then((r) => r.data),
  listTrainingDatasets: (params?: Record<string, unknown>) => api.get("/national-data/training-datasets", { params }).then((r) => r.data),
  createTrainingDataset: (data: Record<string, unknown>) => api.post("/national-data/training-datasets", data).then((r) => r.data),
  listVectorEmbeddings: (params?: Record<string, unknown>) => api.get("/national-data/vector-embeddings", { params }).then((r) => r.data),
  storeVectorEmbedding: (data: Record<string, unknown>) => api.post("/national-data/vector-embeddings", data).then((r) => r.data),
};

// ── National Streaming ──
export const nationalStreamingApi = {
  streamFhir: (data: Record<string, unknown>) => api.post("/national-data/streaming/fhir", data).then((r) => r.data),
  streamHl7: (data: Record<string, unknown>) => api.post("/national-data/streaming/hl7", data).then((r) => r.data),
  streamEvent: (data: Record<string, unknown>) => api.post("/national-data/streaming/events", data).then((r) => r.data),
  getCdcFeed: (params?: Record<string, unknown>) => api.get("/national-data/streaming/cdc", { params }).then((r) => r.data),
  recordCdcChange: (data: Record<string, unknown>) => api.post("/national-data/streaming/cdc", data).then((r) => r.data),
};

// ── Edge ──
export const edgeApi = {
  // Devices
  listDevices: (params?: Record<string, unknown>) => api.get("/edge/devices", { params }).then((r) => r.data),
  getDevice: (deviceId: string) => api.get(`/edge/devices/${deviceId}`).then((r) => r.data),
  quarantineDevice: (deviceId: string) => api.post(`/edge/devices/${deviceId}/quarantine`).then((r) => r.data),
  revokeDevice: (deviceId: string) => api.post(`/edge/devices/${deviceId}/revoke`).then((r) => r.data),
  reinstateDevice: (deviceId: string) => api.post(`/edge/devices/${deviceId}/reinstate`).then((r) => r.data),
  killSwitchDevice: (deviceId: string) => api.post(`/edge/devices/${deviceId}/kill_switch`).then((r) => r.data),

  // Tasks
  createTask: (data: Record<string, unknown>) => api.post("/edge/tasks", data).then((r) => r.data),
  listTasks: (params?: Record<string, unknown>) => api.get("/edge/tasks", { params }).then((r) => r.data),
  getTask: (taskUid: string) => api.get(`/edge/tasks/${taskUid}`).then((r) => r.data),
  cancelTask: (taskUid: string) => api.post(`/edge/tasks/${taskUid}/cancel`).then((r) => r.data),

  // Policy
  getPolicy: () => api.get("/edge/policy").then((r) => r.data),
  updatePolicy: (data: Record<string, unknown>) => api.put("/edge/policy", data).then((r) => r.data),

  // Fleet
  fleetSummary: () => api.get("/edge/fleet/summary").then((r) => r.data),

  // Models
  createModel: (data: Record<string, unknown>) => api.post("/edge/models", data).then((r) => r.data),
  listModels: (params?: Record<string, unknown>) => api.get("/edge/models", { params }).then((r) => r.data),
  updateModelStatus: (modelUid: string, data: Record<string, unknown>) => api.post(`/edge/models/${modelUid}/status`, data).then((r) => r.data),
  assignModel: (modelUid: string, data: Record<string, unknown>) => api.post(`/edge/models/${modelUid}/assign`, data).then((r) => r.data),

  // Agent
  agentHeartbeat: (data: Record<string, unknown>) => api.post("/edge/agent/heartbeat", data).then((r) => r.data),
  agentTaskResult: (taskUid: string, data: Record<string, unknown>) => api.post(`/edge/agent/tasks/${taskUid}/result`, data).then((r) => r.data),
  agentTelemetry: (data: Record<string, unknown>) => api.post("/edge/agent/telemetry", data).then((r) => r.data),

  // Health
  health: () => api.get("/edge/health").then((r) => r.data),
};

// ── Consent ──
export const consentApi = {
  grant: (data: Record<string, unknown>) => api.post("/consent/grant", data).then((r) => r.data),
  revoke: (data: Record<string, unknown>) => api.post("/consent/revoke", data).then((r) => r.data),
  check: (params?: Record<string, unknown>) => api.get("/consent/check", { params }).then((r) => r.data),
};

// ── Claims ──
export const claimsApi = {
  create: (data: Record<string, unknown>) => api.post("/claims", data).then((r) => r.data),
  validate: (claimId: string) => api.post(`/claims/${claimId}/validate`).then((r) => r.data),
  submit: (claimId: string) => api.post(`/claims/${claimId}/submit`).then((r) => r.data),
  get: (claimId: string) => api.get(`/claims/${claimId}`).then((r) => r.data),
};

// ── Insurance ──
export const insuranceApi = {
  get: (insuranceId: string) => api.get(`/insurance/${insuranceId}`).then((r) => r.data),
};

// ── Citizen Portal ──
export const citizenPortalApi = {
  login: (data: Record<string, unknown>) => api.post("/citizen/login", data).then((r) => r.data),
  logout: () => api.post("/citizen/logout").then((r) => r.data),
  profile: () => api.get("/citizen/profile").then((r) => r.data),
  results: (params?: Record<string, unknown>) => api.get("/citizen/results", { params }).then((r) => r.data),
  orders: (params?: Record<string, unknown>) => api.get("/citizen/orders", { params }).then((r) => r.data),
  healthRecord: () => api.get("/citizen/health-record").then((r) => r.data),
};

// ── OAuth2 ──
export const oauth2Api = {
  register: (data: Record<string, unknown>) => api.post("/oauth2/register", data).then((r) => r.data),
  authorize: (params?: Record<string, unknown>) => api.get("/oauth2/authorize", { params }).then((r) => r.data),
  token: (data: Record<string, unknown>) => api.post("/oauth2/token", data).then((r) => r.data),
  introspect: (data: Record<string, unknown>) => api.post("/oauth2/introspect", data).then((r) => r.data),
  revoke: (data: Record<string, unknown>) => api.post("/oauth2/revoke", data).then((r) => r.data),
  openidConfig: () => api.get("/oauth2/.well-known/openid-configuration").then((r) => r.data),
  jwks: () => api.get("/oauth2/jwks.json").then((r) => r.data),
};

// ── SAML ──
export const samlApi = {
  metadata: () => api.get("/auth/saml/metadata").then((r) => r.data),
  acs: (data: Record<string, unknown>) => api.post("/auth/saml/acs", data).then((r) => r.data),
};

// ── Mobile ──
export const mobileApi = {
  refresh: (data: Record<string, unknown>) => api.post("/auth/refresh", data).then((r) => r.data),
  changePassword: (data: Record<string, unknown>) => api.post("/auth/change-password", data).then((r) => r.data),
  info: () => api.get("/mobile/info").then((r) => r.data),
};

// ── Integrations ──
export const integrationsApi = {
  status: () => api.get("/integrations/status").then((r) => r.data),
  probe: (name: string) => api.post(`/integrations/${name}/probe`).then((r) => r.data),
};

// ── Optimizer ──
export const optimizerApi = {
  metrics: () => api.get("/api/optimizer/metrics").then((r) => r.data),
  analyze: () => api.get("/api/optimizer/analyze").then((r) => r.data),
};

// ── Financial ──
export const financialApi = {
  billingStatus: () => api.get("/financial/billing/status").then((r) => r.data),
  billingRates: () => api.get("/financial/billing/rates").then((r) => r.data),
  listInvoices: (params?: Record<string, unknown>) => api.get("/financial/invoices", { params }).then((r) => r.data),
  getInvoice: (id: string) => api.get(`/financial/invoices/${id}`).then((r) => r.data),
  createInvoice: (data: Record<string, unknown>) => api.post("/financial/invoices", data).then((r) => r.data),
  createPayment: (data: Record<string, unknown>) => api.post("/financial/payments", data).then((r) => r.data),
  listPayments: (params?: Record<string, unknown>) => api.get("/financial/payments", { params }).then((r) => r.data),
  receivables: (params?: Record<string, unknown>) => api.get("/financial/receivables", { params }).then((r) => r.data),
  receivablesAging: (params?: Record<string, unknown>) => api.get("/financial/receivables/aging", { params }).then((r) => r.data),
  payables: (params?: Record<string, unknown>) => api.get("/financial/payables", { params }).then((r) => r.data),
  calculatePricing: (data: Record<string, unknown>) => api.post("/financial/pricing/calculate", data).then((r) => r.data),
  createPricingRule: (data: Record<string, unknown>) => api.post("/financial/pricing/rules", data).then((r) => r.data),
  listPricingRules: (params?: Record<string, unknown>) => api.get("/financial/pricing/rules", { params }).then((r) => r.data),
  createTransaction: (data: Record<string, unknown>) => api.post("/financial/transactions", data).then((r) => r.data),
  listTransactions: (params?: Record<string, unknown>) => api.get("/financial/transactions", { params }).then((r) => r.data),
  runBillingCycle: () => api.post("/financial/billing/run-cycle").then((r) => r.data),
  reportsSummary: (params?: Record<string, unknown>) => api.get("/financial/reports/summary", { params }).then((r) => r.data),
  listSubscriptions: (params?: Record<string, unknown>) => api.get("/financial/subscriptions", { params }).then((r) => r.data),
};

// ── Kernel Runtime ──
export const kernelRuntimeApi = {
  health: () => api.get("/kernel/runtime/health").then((r) => r.data),
  metrics: () => api.get("/kernel/runtime/metrics").then((r) => r.data),
  digitalTwin: () => api.get("/kernel/runtime/digital-twin").then((r) => r.data),
  topology: () => api.get("/kernel/runtime/topology").then((r) => r.data),
  resources: () => api.get("/kernel/runtime/resources").then((r) => r.data),
  optimize: () => api.post("/kernel/runtime/optimize").then((r) => r.data),
  slowQueries: () => api.get("/kernel/runtime/observability/slow-queries").then((r) => r.data),
  validationReport: () => api.get("/kernel/runtime/validation/report").then((r) => r.data),
  runValidation: () => api.post("/kernel/runtime/validation/run").then((r) => r.data),
  aiModels: () => api.get("/kernel/runtime/ai/models").then((r) => r.data),
  aiInfer: (data: Record<string, unknown>) => api.post("/kernel/runtime/ai/infer", data).then((r) => r.data),
  listRules: () => api.get("/kernel/runtime/rules").then((r) => r.data),
  listPolicies: () => api.get("/kernel/runtime/policies").then((r) => r.data),
};
