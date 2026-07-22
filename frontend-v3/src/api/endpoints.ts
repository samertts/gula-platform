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

// ── AI ──
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
  dhis2Aggregate: () => api.get("/compliance/dhis2/aggregate").then((r) => r.data),
  auditIntegrity: () => api.get("/compliance/audit-integrity").then((r) => r.data),
  securityReport: () => api.get("/compliance/security-report").then((r) => r.data),
  systemStatus: () => api.get("/compliance/system-status").then((r) => r.data),
};

// ── MFA ──
export const mfaApi = {
  setupTotp: (deviceName?: string) =>
    api.post("/mfa/totp/setup", { device_name: deviceName }).then((r) => r.data),
  verifyTotp: (token: string) =>
    api.post("/mfa/totp/verify", { token }).then((r) => r.data),
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
};
