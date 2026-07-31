import { api } from "./client";
import type {
  LoginRequest,
  LoginResponse,
  Patient,
  PaginatedResponse,
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
  HealthStatus,
  DeepHealth,
  UpgradeRequest,
  FeatureFlag,
  SecurityStatus,
  EHRNote,
  EHRCondition,
  EHRMedication,
  EHRAllergy,
  EHRImmunization,
  ClinicalOrder,
  FHIRResource,
  EdgeDevice,
  EdgeTask,
} from "@/types";

type PatientListResponse = PaginatedResponse<Patient>;

// ── Auth ──
export const authApi = {
  login: (data: LoginRequest) =>
    api.post<LoginResponse>("/login", data).then((r) => r.data),
  logout: () => api.post<Record<string, unknown>>("/logout").then((r) => r.data),
  register: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/register", data).then((r) => r.data),
  registerCitizen: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/register/citizen", data).then((r) => r.data),
  registerStaff: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/register/staff", data).then((r) => r.data),
  registerDoctor: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/register/doctor", data).then((r) => r.data),
  forgotPassword: (email: string) =>
    api.post<Record<string, unknown>>("/auth/forgot-password", { email }).then((r) => r.data),
  resetPassword: (token: string, new_password: string) =>
    api.post<Record<string, unknown>>("/auth/reset-password", { token, new_password }).then((r) => r.data),
  changePassword: (current_password: string, new_password: string) =>
    api.post<Record<string, unknown>>("/auth/change-password", { current_password, new_password }).then((r) => r.data),
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
    api.get<PatientListResponse>("/patients", { params }).then((r) => r.data),
  create: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/patients", data).then((r) => r.data),
  get: (id: number) =>
    api.get<Patient>(`/patients/${id}`).then((r) => r.data),
  update: (id: number, data: Record<string, unknown>) =>
    api.put<Record<string, unknown>>(`/patients/${id}`, data).then((r) => r.data),
  getFamily: (familyId: string) =>
    api.get<Patient[]>(`/patients/family/${familyId}`).then((r) => r.data),
  getChildren: (patientId: number) =>
    api.get<Patient[]>(`/patients/${patientId}/children`).then((r) => r.data),
};

// ── Orders ──
export const ordersApi = {
  testProfiles: () => api.get<Record<string, unknown[]>>("/test-profiles").then((r) => r.data),
  list: (params?: { skip?: number; limit?: number; search?: string }) =>
    api.get<LabOrder[]>("/orders", { params }).then((r) => r.data),
  get: (id: number) =>
    api.get<LabOrder>(`/orders/${id}`).then((r) => r.data),
  create: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/orders", data).then((r) => r.data),
  validate: (id: number) =>
    api.post<Record<string, unknown>>(`/orders/${id}/validate`).then((r) => r.data),
  cancel: (id: number) =>
    api.post<Record<string, unknown>>(`/orders/${id}/cancel`).then((r) => r.data),
  analyze: (id: number) =>
    api.get<AIInterpretation>(`/orders/${id}/intelligence`).then((r) => r.data),
};

// ── Test Results ──
export const resultsApi = {
  list: (params?: { health_id?: string; category?: string; date_from?: string; date_to?: string; is_abnormal?: boolean; skip?: number; limit?: number }) =>
    api.get<PaginatedResponse<LabResult>>("/test-results", { params }).then((r) => r.data),
  get: (id: number) =>
    api.get<LabResult>(`/test-results/${id}`).then((r) => r.data),
  create: (data: Record<string, unknown>) =>
    api.post<LabResult>("/test-results/", data).then((r) => r.data),
  verify: (id: number) =>
    api.put<LabResult>(`/test-results/${id}/verify`).then((r) => r.data),
  validate: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/test-results/validate", data).then((r) => r.data),
  citizenResults: (healthId: string, params?: Record<string, unknown>) =>
    api.get<LabResult[]>(`/test-results/citizen/${healthId}`, { params }).then((r) => r.data),
  citizenTimeline: (healthId: string, params?: { category?: string }) =>
    api.get<{ timeline: { category: string; results: LabResult[] }[] }>(`/test-results/citizen/${healthId}/timeline`, { params }).then((r) => r.data),
};

// ── Public Results ──
export const publicResultsApi = {
  get: (token: string) =>
    api.get<{ results: LabResult[]; patient: { full_name: string; health_id: string } }>(`/r/${token}`).then((r) => r.data),
  downloadPdf: (token: string) =>
    api.get<Blob>(`/r/${token}/pdf`, { responseType: "blob" }).then((r) => r.data),
};

// ── QR Codes ──
export const qrApi = {
  get: (token: string) => api.get<PatientCard>(`/qr/${token}`).then((r) => r.data),
  getMedical: (token: string) => api.get<{ patient: Patient; results: LabResult[] }>(`/qr-medical/${token}`).then((r) => r.data),
};

// ── Patient History ──
export const patientHistoryApi = {
  byId: (patientId: number) =>
    api.get<{ orders: LabOrder[]; results: LabResult[] }>(`/patient-history/${patientId}`).then((r) => r.data),
  byPhone: (phone: string, name?: string) =>
    api.get<{ patient: Patient; orders: LabOrder[]; results: LabResult[] }>(`/history/${phone}`, { params: { name } }).then((r) => r.data),
};

// ── Clinical Intelligence ──
export const clinicalApi = {
  analyze: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/analyze", data).then((r) => r.data),
};

// ── Samples ──
export const samplesApi = {
  list: (params?: { status?: string; skip?: number; limit?: number }) =>
    api.get<{ total: number; samples: Sample[] }>("/samples", { params }).then((r) => r.data),
  create: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/samples", data).then((r) => r.data),
  get: (barcode: string) =>
    api.get<Sample>(`/samples/${barcode}`).then((r) => r.data),
  update: (barcode: string, data: Record<string, unknown>) =>
    api.put<Record<string, unknown>>(`/samples/${barcode}`, data).then((r) => r.data),
};

// ── Labs ──
export const labsApi = {
  me: () => api.get<Lab>("/labs/me").then((r) => r.data),
  update: (data: Record<string, unknown>) =>
    api.put<Record<string, unknown>>("/labs/me", data).then((r) => r.data),
  employees: () =>
    api.get<{ employees: LabEmployee[] }>("/labs/me/employees").then((r) => r.data),
  createEmployee: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/labs/me/employees", data).then((r) => r.data),
  updateEmployee: (id: number, data: Record<string, unknown>) =>
    api.put<Record<string, unknown>>(`/labs/me/employees/${id}`, data).then((r) => r.data),
};

// ── Admin ──
export const adminApi = {
  stats: () =>
    api
      .get<{ total_labs: number; active_labs: number; total_users: number; total_patients: number; total_orders: number; total_critical: number }>(
        "/admin/stats",
      )
      .then((r) => r.data),
  labs: (params?: { skip?: number; limit?: number }) =>
    api.get<{ total: number; labs: Lab[] }>("/admin/labs", { params }).then((r) => r.data),
  createLab: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/admin/labs", data).then((r) => r.data),
  getLab: (id: number) =>
    api.get<Lab>(`/admin/labs/${id}`).then((r) => r.data),
  toggleLab: (id: number) =>
    api.put<Record<string, unknown>>(`/admin/labs/${id}/toggle`).then((r) => r.data),
  activateLab: (id: number) =>
    api.put<Record<string, unknown>>(`/admin/labs/${id}/activate`).then((r) => r.data),
  pendingLabs: (params?: { skip?: number; limit?: number }) =>
    api.get<{ total: number; labs: Lab[] }>("/admin/labs/pending", { params }).then((r) => r.data),
  users: (params?: { role?: string; lab_id?: number; skip?: number; limit?: number }) =>
    api.get<{ total: number; users: User[] }>("/admin/users", { params }).then((r) => r.data),
  createUser: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/admin/users", data).then((r) => r.data),
  changeUserRole: (userId: number, data: Record<string, unknown>) =>
    api.patch<Record<string, unknown>>(`/admin/users/${userId}/role`, data).then((r) => r.data),
  toggleUser: (userId: number) =>
    api.put<Record<string, unknown>>(`/admin/users/${userId}/toggle`).then((r) => r.data),
  doctors: (params?: { is_verified?: boolean; skip?: number; limit?: number }) =>
    api.get<{ total: number; users: User[] }>("/admin/doctors", { params }).then((r) => r.data),
  approveDoctor: (id: number) =>
    api.put<Record<string, unknown>>(`/admin/doctors/${id}/approve`).then((r) => r.data),
  revokeDoctor: (id: number) =>
    api.put<Record<string, unknown>>(`/admin/doctors/${id}/revoke`).then((r) => r.data),
  citizens: (params?: { is_active?: boolean; is_verified?: boolean; skip?: number; limit?: number }) =>
    api.get<{ total: number; citizens: Patient[] }>("/admin/citizens", { params }).then((r) => r.data),
  toggleCitizen: (id: number) =>
    api.put<Record<string, unknown>>(`/admin/citizens/${id}/toggle`).then((r) => r.data),
  verifyCitizen: (id: number) =>
    api.put<Record<string, unknown>>(`/admin/citizens/${id}/verify`).then((r) => r.data),
  auditLogs: (params?: { action?: string; user_id?: number; skip?: number; limit?: number }) =>
    api.get<{ total: number; logs: AuditLog[] }>("/admin/audit-logs", { params }).then((r) => r.data),
  killSwitchStatus: () =>
    api
      .get<{ active: boolean; activated_at?: string; reason?: string; activated_by?: string; deactivated_at?: string }>(
        "/admin/kill-switch/status",
      )
      .then((r) => r.data),
  killSwitchActivate: (reason: string) =>
    api.post<Record<string, unknown>>("/admin/kill-switch/activate", { reason }).then((r) => r.data),
  killSwitchDeactivate: (reason: string) =>
    api.post<Record<string, unknown>>("/admin/kill-switch/deactivate", { reason }).then((r) => r.data),
  controlLayerStats: () =>
    api
      .get<{ total_requests: number; blocked_requests: number; active_rules: number; rate_limit_hits: number }>(
        "/admin/control-layer/stats",
      )
      .then((r) => r.data),
};

// ── Admin Log Level ──
export const adminLogLevelApi = {
  get: () => api.get<{ level: string }>("/admin/log-level").then((r) => r.data),
  set: (level: string) => api.post<Record<string, unknown>>("/admin/log-level", { level }).then((r) => r.data),
};

// ── Notifications ──
export const notificationsApi = {
  send: (data: { order_id: number; channel?: string }) =>
    api.post<Record<string, unknown>>("/notify/send", data).then((r) => r.data),
  history: (orderId: number) =>
    api
      .get<{ total_views: number; first_viewed?: string; last_viewed?: string }>(`/notify/history/${orderId}`)
      .then((r) => r.data),
};

// ── Critical Alerts ──
export const criticalAlertsApi = {
  list: (params?: { hours?: number; acknowledged?: boolean }) =>
    api.get<CriticalAlert[]>("/alerts", { params }).then((r) => r.data),
  stats: () => api.get<{ total: number; critical: number; acknowledged: number; unacknowledged: number }>("/alerts/stats").then((r) => r.data),
};

// ── Quality Control ──
export const qcApi = {
  list: (params?: { test_code?: string; status?: string; days?: number; skip?: number; limit?: number }) =>
    api.get<{ total: number; qc_results: QualityControl[] }>("/qc", { params }).then((r) => r.data),
  submit: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/qc", data).then((r) => r.data),
  submitBatch: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/qc/batch", data).then((r) => r.data),
  summary: (params?: { days?: number }) =>
    api.get<{ total_tests: number; passed: number; failed: number; warning: number; pass_rate_pct: number }>("/qc/summary", { params }).then((r) => r.data),
};

// ── Batch ──
export const batchApi = {
  orders: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/batch/orders", data).then((r) => r.data),
};

// ── Patient Card ──
export const patientCardApi = {
  get: (patientId: number) =>
    api.get<PatientCard>(`/patient-card/${patientId}`).then((r) => r.data),
  qr: (patientId: number) =>
    api.get<Blob>(`/patient-card/${patientId}/qr.png`, { responseType: "blob" }).then((r) => r.data),
  scan: (token: string) =>
    api.post<Record<string, unknown>>("/patient-card/scan", { token }).then((r) => r.data),
  history: (patientId: number, params?: { limit?: number }) =>
    api.get<{ scans: { scanned_at: string; scanner_ip?: string }[] }>(`/patient-card/${patientId}/history`, { params }).then((r) => r.data),
  print: (patientId: number) =>
    api.get<PatientCard>(`/patient-card/${patientId}/print`).then((r) => r.data),
};

// ── ID Scan ──
export const idScanApi = {
  scan: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/id-scan/scan", data).then((r) => r.data),
};

// ── Device Results ──
export const deviceApi = {
  submitResults: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/device/results", data).then((r) => r.data),
};

// ── Identity ──
export const identityApi = {
  linkNid: (data: { patient_id: number; national_id: string; confirm_name?: string }) =>
    api.post<Record<string, unknown>>("/identity/link", data).then((r) => r.data),
  lookupByNid: (nationalId: string) =>
    api.get<{ found: boolean; patient?: Patient }>("/identity/lookup", { params: { national_id: nationalId } }).then((r) => r.data),
};

// ── National Identity ──
export const nationalIdentityApi = {
  verify: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/national-id/verify", data).then((r) => r.data),
};

// ── Tiers / Subscription ──
export const tiersApi = {
  list: () => api.get<{ tiers: SubscriptionTier[] }>("/tiers").then((r) => r.data),
  my: () => api.get<SubscriptionInfo>("/tiers/my").then((r) => r.data),
  upgrade: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/tiers/upgrade", data).then((r) => r.data),
  demand: (data: { lab_id: number; target_tier: string; reason?: string }) =>
    api.post<Record<string, unknown>>("/tiers/upgrade-demand", data).then((r) => r.data),
  adminDemands: (params?: { limit?: number }) =>
    api.get<{ demands: UpgradeRequest[] }>("/admin/tiers/demands", { params }).then((r) => r.data),
  adminSetTier: (labId: number, data: Record<string, unknown>) =>
    api.put<Record<string, unknown>>(`/admin/tiers/${labId}`, data).then((r) => r.data),
  adminSetFlag: (labId: number, data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>(`/admin/tiers/flags/${labId}`, data).then((r) => r.data),
  adminListFlags: (labId: number) =>
    api.get<FeatureFlag[]>(`/admin/tiers/flags/${labId}`).then((r) => r.data),
};

// ── AI v1 ──
export const aiApi = {
  suggest: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/api/ai/suggest", data).then((r) => r.data),
  pending: () =>
    api
      .get<{
        total: number;
        items?: { id: number; order_id: number; test_name: string; patient_name: string; suggestion: string; confidence: number }[];
        approvals?: { id: number; order_id: number; test_name: string; patient_name: string; suggestion: string; confidence: number }[];
      }>("/api/ai/pending")
      .then((r) => r.data),
  approve: (id: string) =>
    api.post<Record<string, unknown>>(`/api/ai/approve/${id}`).then((r) => r.data),
  reject: (id: string, reason?: string) =>
    api.post<Record<string, unknown>>(`/api/ai/reject/${id}`, { reason }).then((r) => r.data),
  execute: (id: string) =>
    api.post<Record<string, unknown>>(`/api/ai/execute/${id}`).then((r) => r.data),
  analyzeOrder: (orderId: number) =>
    api.post<Record<string, unknown>>(`/api/ai/analyze-order/${orderId}`).then((r) => r.data),
  operations: () =>
    api.get<{ operations: { id: string; type: string; status: string; started_at: string }[] }>("/api/ai/operations").then((r) => r.data),
  providers: () => api.get<AIProviderStatus>("/api/ai/providers").then((r) => r.data),
  criticalAlerts: (params?: { limit?: number }) =>
    api.get<CriticalAlert[]>("/api/ai/critical-alerts", { params }).then((r) => r.data),
  interpret: (token: string) =>
    api.get<AIInterpretation>(`/api/ai/interpret/${token}`).then((r) => r.data),
  chat: (message: string, context?: string) =>
    api.post<AIChatResponse>("/api/ai/chat", { message, context }).then((r) => r.data),
};

// ── AI v2 Platform ──
export const aiPlatformApi = {
  search: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/api/ai/v2/search", data).then((r) => r.data),
  index: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/api/ai/v2/index", data).then((r) => r.data),
  embeddingInfo: () =>
    api.get<{ dimensions: number; model_name: string; total_embeddings: number }>("/api/ai/v2/embedding-info").then((r) => r.data),
  ragQuery: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/api/ai/v2/rag/query", data).then((r) => r.data),
  knowledgeGraphInfo: () =>
    api.get<{ nodes?: number; edges?: number; relationships?: number; node_types?: number; node_count: number; edge_count: number; relation_types: string[] }>("/api/ai/v2/knowledge-graph/info").then((r) => r.data),
  knowledgeGraphSearch: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/api/ai/v2/knowledge-graph/search", data).then((r) => r.data),
  knowledgeGraphNode: (nodeId: string) =>
    api.get<{ id: string; type: string; label: string; properties: Record<string, unknown> }>(`/api/ai/v2/knowledge-graph/node/${nodeId}`).then((r) => r.data),
  knowledgeGraphPath: (params: { from: string; to: string }) =>
    api.get<{ nodes: unknown[]; edges: unknown[]; distance: number }>("/api/ai/v2/knowledge-graph/path", { params }).then((r) => r.data),
  agentTools: () =>
    api.get<{ tools: { name: string; description: string; parameters: Record<string, unknown> }[] }>("/api/ai/v2/agents/tools").then((r) => r.data),
  agentExecute: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/api/ai/v2/agents/execute", data).then((r) => r.data),
  orchestrate: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/api/ai/v2/orchestrate", data).then((r) => r.data),
  orchestrateTasks: () =>
    api.get<{ tasks: { id: string; workflow: string; status: string; progress: number }[] }>("/api/ai/v2/orchestrate/tasks").then((r) => r.data),
  createSession: () =>
    api.post<Record<string, unknown>>("/api/ai/v2/sessions").then((r) => r.data),
  sessionMessage: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/api/ai/v2/sessions/message", data).then((r) => r.data),
  sessionHistory: (sessionId: string) =>
    api.get<{ id: string; messages: { role: string; content: string; timestamp: string }[] }>(`/api/ai/v2/sessions/${sessionId}`).then((r) => r.data),
  cdsEvaluate: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/api/ai/v2/cds/evaluate", data).then((r) => r.data),
  cdsEvaluateOrder: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/api/ai/v2/cds/evaluate-order", data).then((r) => r.data),
  governanceModels: () =>
    api.get<{ total?: number; count?: number; models: { name: string; version: string; status: string; approved: boolean }[] }>("/api/ai/v2/governance/models").then((r) => r.data),
  governancePrompts: () =>
    api.get<{ total?: number; count?: number; prompts: { id: string; name: string; version: string; status: string }[] }>("/api/ai/v2/governance/prompts").then((r) => r.data),
  governanceEvaluations: () =>
    api.get<{ evaluations: { id: string; prompt_id: string; model: string; passed: boolean; score: number; timestamp: string }[] }>("/api/ai/v2/governance/evaluations").then((r) => r.data),
  securityScan: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/api/ai/v2/security/scan", data).then((r) => r.data),
  metrics: () =>
    api.get<{ total_requests: number; success_rate?: number; today_requests?: number; total_tokens: number; avg_latency_ms: number; error_rate: number; period_hours: number }>("/api/ai/v2/metrics").then((r) => r.data),
  metricsPrometheus: () =>
    api.get<string>("/api/ai/v2/metrics/prometheus").then((r) => r.data),
};

// ── AI Telemetry ──
export const aiTelemetryApi = {
  logInteraction: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/api/ai/interactions", data).then((r) => r.data),
  logFeedback: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/api/ai/feedback", data).then((r) => r.data),
  logUnresolved: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/api/ai/unresolved", data).then((r) => r.data),
  safetyFlags: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/api/ai/safety-flags", data).then((r) => r.data),
  export: (format: string) => api.get<Blob>("/api/ai/export", { params: { format } }).then((r) => r.data),
  stats: () =>
    api
      .get<{ total_interactions: number; total_feedback: number; total_unresolved: number; total_safety_flags: number }>(
        "/api/ai/stats",
      )
      .then((r) => r.data),
};

// ── Stats ──
export const statsApi = {
  dailyTrends: (params?: { days?: number }) =>
    api.get<TrendData>("/stats/trends/daily", { params }).then((r) => r.data),
  testFrequency: (params?: { days?: number; limit?: number }) =>
    api.get<{ series: { test_name: string; count: number; date: string }[] }>("/stats/trends/tests", { params }).then((r) => r.data),
  flagDistribution: (params?: { days?: number }) =>
    api.get<FlagDistribution>("/stats/trends/flags", { params }).then((r) => r.data),
  patientGrowth: (params?: { days?: number }) =>
    api.get<{ series: { date: string; new_patients: number; cumulative: number }[] }>("/stats/trends/patients", { params }).then((r) => r.data),
  summary: () => api.get<StatsSummary>("/stats/summary").then((r) => r.data),
  turnaround: (params?: { days?: number }) =>
    api.get<TurnaroundTime>("/stats/turnaround", { params }).then((r) => r.data),
};

// ── Metrics & Health ──
export const healthApi = {
  health: () => api.get<HealthStatus>("/health").then((r) => r.data),
  ready: () => api.get<HealthStatus>("/health/ready").then((r) => r.data),
  deep: () => api.get<DeepHealth>("/health/deep").then((r) => r.data),
  status: () => api.get<HealthStatus>("/health/status").then((r) => r.data),
};

export const metricsApi = {
  get: () => api.get<Record<string, number>>("/metrics").then((r) => r.data),
  prom: () => api.get<string>("/metrics/prom").then((r) => r.data),
};

// ── Security ──
export const securityApi = {
  status: () => api.get<SecurityStatus>("/security/status").then((r) => r.data),
};

// ── Compliance ──
export const complianceApi = {
  info: () =>
    api
      .get<{ compliance_framework: string; standards: string[]; last_assessment: string; overall_status: string }>(
        "/compliance/info",
      )
      .then((r) => r.data),
  auditSummary: () =>
    api
      .get<{ total_audits: number; passed: number; failed: number; in_progress: number; last_audit_date: string }>(
        "/compliance/audit-summary",
      )
      .then((r) => r.data),
  fhirPatient: (patientId: number) =>
    api.get<FHIRResource>(`/compliance/fhir/patient/${patientId}`).then((r) => r.data),
  fhirObservation: (orderId: number) =>
    api.get<FHIRResource>(`/compliance/fhir/observation/${orderId}`).then((r) => r.data),
  fhirDiagnosticReport: (orderId: number) =>
    api.get<FHIRResource>(`/compliance/fhir/diagnostic-report/${orderId}`).then((r) => r.data),
  fhirServiceRequest: (orderId: number) =>
    api.get<FHIRResource>(`/compliance/fhir/service-request/${orderId}`).then((r) => r.data),
  dhis2Aggregate: () => api.get<Record<string, unknown>>("/compliance/dhis2/aggregate").then((r) => r.data),
  auditIntegrity: () =>
    api
      .get<{ status: string; checks: { check: string; passed: boolean; details?: string }[] }>(
        "/compliance/audit-integrity",
      )
      .then((r) => r.data),
  securityReport: () =>
    api
      .get<{ overall_grade: string; findings: { severity: string; description: string }[]; recommendations: string[] }>(
        "/compliance/security-report",
      )
      .then((r) => r.data),
  timeSync: () =>
    api
      .get<{ server_time_utc: string; ntp_synced: boolean; offset_ms: number }>("/compliance/time-sync")
      .then((r) => r.data),
  systemStatus: () =>
    api
      .get<{ status: string; components: { name: string; status: string; latency_ms?: number }[] }>("/compliance/system-status")
      .then((r) => r.data),
};

// ── MFA ──
export const mfaApi = {
  setupTotp: (deviceName?: string) =>
    api.post<Record<string, unknown>>("/mfa/totp/setup", { device_name: deviceName }).then((r) => r.data),
  verifyTotp: (token: string) =>
    api.post<Record<string, unknown>>("/mfa/totp/verify", { token }).then((r) => r.data),
  webauthnRegisterBegin: () => api.post<Record<string, unknown>>("/mfa/webauthn/register/begin").then((r) => r.data),
  webauthnRegisterComplete: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/mfa/webauthn/register/complete", data).then((r) => r.data),
  webauthnAuthBegin: () => api.post<Record<string, unknown>>("/mfa/webauthn/authenticate/begin").then((r) => r.data),
  webauthnAuthComplete: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/mfa/webauthn/authenticate/complete", data).then((r) => r.data),
  devices: () =>
    api
      .get<{ devices: { id: number; type: string; name: string; created_at: string; last_used?: string }[] }>(
        "/mfa/devices",
      )
      .then((r) => r.data),
  removeDevice: (deviceId: number) =>
    api.delete<Record<string, unknown>>(`/mfa/devices/${deviceId}`).then((r) => r.data),
  status: () =>
    api
      .get<{
        mfa_enabled: boolean;
        totp_configured: boolean;
        webauthn_configured: boolean;
        recommended_method: string;
      }>("/mfa/status")
      .then((r) => r.data),
};

// ── Service Accounts ──
export const serviceAccountsApi = {
  list: () =>
    api
      .get<{ accounts: { id: string; name: string; role: string; is_active: boolean; created_at: string; last_used?: string }[] }>(
        "/service-accounts",
      )
      .then((r) => r.data),
  create: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/service-accounts", data).then((r) => r.data),
  revoke: (id: string) =>
    api.post<Record<string, unknown>>(`/service-accounts/${id}/revoke`).then((r) => r.data),
  rotate: (id: string) =>
    api.post<Record<string, unknown>>(`/service-accounts/${id}/rotate`).then((r) => r.data),
};

type CanonicalPatientEntry = {
  id: string;
  gpid: string;
  patient?: Patient;
  citizen_id?: string;
  linked_patients: number[];
  linked_citizens: string[];
  created_at: string;
};

// ── Canonical Patient ──
export const canonicalPatientApi = {
  create: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/api/v1/canonical-patients", data).then((r) => r.data),
  get: (id: string) => api.get<CanonicalPatientEntry>(`/api/v1/canonical-patients/${id}`).then((r) => r.data),
  merge: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/api/v1/canonical-patients/merge", data).then((r) => r.data),
  byPatient: (patientId: number) =>
    api.get<CanonicalPatientEntry>(`/api/v1/canonical-patients/by-patient/${patientId}`).then((r) => r.data),
  byCitizen: (citizenId: string) =>
    api.get<CanonicalPatientEntry>(`/api/v1/canonical-patients/by-citizen/${citizenId}`).then((r) => r.data),
  search: (params?: Record<string, unknown>) =>
    api.get<{ total: number; items: { id: string; gpid: string; patient?: Patient }[] }>(
      "/api/v1/canonical-patients",
      { params },
    ).then((r) => r.data),
  linkPatient: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/api/v1/canonical-patients/link-patient", data).then((r) => r.data),
  linkCitizen: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/api/v1/canonical-patients/link-citizen", data).then((r) => r.data),
};

// ── EHR (Electronic Health Record) ──
export const ehrApi = {
  // Clinical Notes
  createClinicalNote: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/ehr/clinical-notes", data).then((r) => r.data),
  getClinicalNote: (id: number) =>
    api.get<EHRNote>(`/ehr/clinical-notes/${id}`).then((r) => r.data),
  updateClinicalNote: (id: number, data: Record<string, unknown>) =>
    api.put<Record<string, unknown>>(`/ehr/clinical-notes/${id}`, data).then((r) => r.data),
  deleteClinicalNote: (id: number) =>
    api.delete<Record<string, unknown>>(`/ehr/clinical-notes/${id}`).then((r) => r.data),
  listClinicalNotes: (patientId: string, params?: { skip?: number; limit?: number }) =>
    api.get<EHRNote[]>(`/ehr/patients/${patientId}/clinical-notes`, { params }).then((r) => r.data),

  // Allergies
  createAllergy: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/ehr/allergies", data).then((r) => r.data),
  getAllergy: (id: number) =>
    api.get<EHRAllergy>(`/ehr/allergies/${id}`).then((r) => r.data),
  updateAllergy: (id: number, data: Record<string, unknown>) =>
    api.put<Record<string, unknown>>(`/ehr/allergies/${id}`, data).then((r) => r.data),
  deleteAllergy: (id: number) =>
    api.delete<Record<string, unknown>>(`/ehr/allergies/${id}`).then((r) => r.data),
  listAllergies: (patientId: string, params?: { skip?: number; limit?: number }) =>
    api.get<EHRAllergy[]>(`/ehr/patients/${patientId}/allergies`, { params }).then((r) => r.data),

  // Medication Statements
  createMedicationStatement: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/ehr/medication-statements", data).then((r) => r.data),
  getMedicationStatement: (id: number) =>
    api.get<EHRMedication>(`/ehr/medication-statements/${id}`).then((r) => r.data),
  updateMedicationStatement: (id: number, data: Record<string, unknown>) =>
    api.put<Record<string, unknown>>(`/ehr/medication-statements/${id}`, data).then((r) => r.data),
  deleteMedicationStatement: (id: number) =>
    api.delete<Record<string, unknown>>(`/ehr/medication-statements/${id}`).then((r) => r.data),
  listMedicationStatements: (patientId: string, params?: { skip?: number; limit?: number }) =>
    api.get<EHRMedication[]>(`/ehr/patients/${patientId}/medication-statements`, { params }).then((r) => r.data),

  // Medication Requests
  createMedicationRequest: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/ehr/medication-requests", data).then((r) => r.data),
  getMedicationRequest: (id: number) =>
    api.get<ClinicalOrder>(`/ehr/medication-requests/${id}`).then((r) => r.data),
  updateMedicationRequest: (id: number, data: Record<string, unknown>) =>
    api.put<Record<string, unknown>>(`/ehr/medication-requests/${id}`, data).then((r) => r.data),
  deleteMedicationRequest: (id: number) =>
    api.delete<Record<string, unknown>>(`/ehr/medication-requests/${id}`).then((r) => r.data),
  listMedicationRequests: (patientId: string, params?: { skip?: number; limit?: number }) =>
    api.get<ClinicalOrder[]>(`/ehr/patients/${patientId}/medication-requests`, { params }).then((r) => r.data),

  // Medication Dispenses
  createMedicationDispense: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/ehr/medication-dispenses", data).then((r) => r.data),
  getMedicationDispense: (id: number) =>
    api
      .get<{ id: number; medication_name: string; dosage?: string; dispensed_date: string; dispensed_by?: string; status: string }>(
        `/ehr/medication-dispenses/${id}`,
      )
      .then((r) => r.data),
  updateMedicationDispense: (id: number, data: Record<string, unknown>) =>
    api.put<Record<string, unknown>>(`/ehr/medication-dispenses/${id}`, data).then((r) => r.data),
  deleteMedicationDispense: (id: number) =>
    api.delete<Record<string, unknown>>(`/ehr/medication-dispenses/${id}`).then((r) => r.data),
  listMedicationDispenses: (patientId: string, params?: { skip?: number; limit?: number }) =>
    api.get<{ id: number; medication_name: string; dosage?: string; dispensed_date: string; status: string }[]>(
      `/ehr/patients/${patientId}/medication-dispenses`,
      { params },
    ).then((r) => r.data),

  // Care Plans
  createCarePlan: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/ehr/care-plans", data).then((r) => r.data),
  getCarePlan: (id: number) =>
    api
      .get<{ id: number; patient_id: number; plan_name: string; status: string; goals: { id: number; description: string; status: string }[] }>(
        `/ehr/care-plans/${id}`,
      )
      .then((r) => r.data),
  updateCarePlan: (id: number, data: Record<string, unknown>) =>
    api.put<Record<string, unknown>>(`/ehr/care-plans/${id}`, data).then((r) => r.data),
  deleteCarePlan: (id: number) =>
    api.delete<Record<string, unknown>>(`/ehr/care-plans/${id}`).then((r) => r.data),
  listCarePlans: (patientId: string, params?: { skip?: number; limit?: number }) =>
    api
      .get<{ id: number; patient_id: number; plan_name: string; status: string }[]>(
        `/ehr/patients/${patientId}/care-plans`,
        { params },
      )
      .then((r) => r.data),
  addCarePlanGoal: (planId: number, data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>(`/ehr/care-plans/${planId}/goals`, data).then((r) => r.data),
  updateCarePlanGoal: (planId: number, goalId: number, data: Record<string, unknown>) =>
    api.put<Record<string, unknown>>(`/ehr/care-plans/${planId}/goals/${goalId}`, data).then((r) => r.data),
  deleteCarePlanGoal: (planId: number, goalId: number) =>
    api.delete<Record<string, unknown>>(`/ehr/care-plans/${planId}/goals/${goalId}`).then((r) => r.data),

  // Problem List
  createProblemListItem: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/ehr/problem-list", data).then((r) => r.data),
  getProblemListItem: (id: number) =>
    api
      .get<{ id: number; patient_id: number; problem: string; onset_date?: string; status: string }>(
        `/ehr/problem-list/${id}`,
      )
      .then((r) => r.data),
  updateProblemListItem: (id: number, data: Record<string, unknown>) =>
    api.put<Record<string, unknown>>(`/ehr/problem-list/${id}`, data).then((r) => r.data),
  deleteProblemListItem: (id: number) =>
    api.delete<Record<string, unknown>>(`/ehr/problem-list/${id}`).then((r) => r.data),
  listProblemList: (patientId: string, params?: { skip?: number; limit?: number }) =>
    api
      .get<{ id: number; patient_id: number; problem: string; onset_date?: string; status: string }[]>(
        `/ehr/patients/${patientId}/problem-list`,
        { params },
      )
      .then((r) => r.data),

  // Conditions
  createCondition: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/ehr/conditions", data).then((r) => r.data),
  getCondition: (id: number) =>
    api.get<EHRCondition>(`/ehr/conditions/${id}`).then((r) => r.data),
  updateCondition: (id: number, data: Record<string, unknown>) =>
    api.put<Record<string, unknown>>(`/ehr/conditions/${id}`, data).then((r) => r.data),
  deleteCondition: (id: number) =>
    api.delete<Record<string, unknown>>(`/ehr/conditions/${id}`).then((r) => r.data),
  listConditions: (patientId: string, params?: { skip?: number; limit?: number }) =>
    api.get<EHRCondition[]>(`/ehr/patients/${patientId}/conditions`, { params }).then((r) => r.data),

  // Diagnoses
  createDiagnosis: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/ehr/diagnoses", data).then((r) => r.data),
  getDiagnosis: (id: number) =>
    api.get<EHRCondition>(`/ehr/diagnoses/${id}`).then((r) => r.data),
  updateDiagnosis: (id: number, data: Record<string, unknown>) =>
    api.put<Record<string, unknown>>(`/ehr/diagnoses/${id}`, data).then((r) => r.data),
  deleteDiagnosis: (id: number) =>
    api.delete<Record<string, unknown>>(`/ehr/diagnoses/${id}`).then((r) => r.data),
  listDiagnoses: (patientId: string, params?: { skip?: number; limit?: number }) =>
    api.get<EHRCondition[]>(`/ehr/patients/${patientId}/diagnoses`, { params }).then((r) => r.data),

  // Family History
  createFamilyHistory: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/ehr/family-history", data).then((r) => r.data),
  getFamilyHistory: (id: number) =>
    api
      .get<{ id: number; patient_id: number; relation: string; condition: string; notes?: string }>(
        `/ehr/family-history/${id}`,
      )
      .then((r) => r.data),
  updateFamilyHistory: (id: number, data: Record<string, unknown>) =>
    api.put<Record<string, unknown>>(`/ehr/family-history/${id}`, data).then((r) => r.data),
  deleteFamilyHistory: (id: number) =>
    api.delete<Record<string, unknown>>(`/ehr/family-history/${id}`).then((r) => r.data),
  listFamilyHistory: (patientId: string, params?: { skip?: number; limit?: number }) =>
    api
      .get<{ id: number; patient_id: number; relation: string; condition: string; notes?: string }[]>(
        `/ehr/patients/${patientId}/family-history`,
        { params },
      )
      .then((r) => r.data),

  // Social History
  createSocialHistory: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/ehr/social-history", data).then((r) => r.data),
  getSocialHistory: (id: number) =>
    api
      .get<{ id: number; patient_id: number; habit: string; status: string; notes?: string }>(
        `/ehr/social-history/${id}`,
      )
      .then((r) => r.data),
  updateSocialHistory: (id: number, data: Record<string, unknown>) =>
    api.put<Record<string, unknown>>(`/ehr/social-history/${id}`, data).then((r) => r.data),
  deleteSocialHistory: (id: number) =>
    api.delete<Record<string, unknown>>(`/ehr/social-history/${id}`).then((r) => r.data),
  listSocialHistory: (patientId: string, params?: { skip?: number; limit?: number }) =>
    api
      .get<{ id: number; patient_id: number; habit: string; status: string; notes?: string }[]>(
        `/ehr/patients/${patientId}/social-history`,
        { params },
      )
      .then((r) => r.data),

  // Risk Factors
  createRiskFactor: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/ehr/risk-factors", data).then((r) => r.data),
  getRiskFactor: (id: number) =>
    api
      .get<{ id: number; patient_id: number; factor: string; severity: string; notes?: string }>(
        `/ehr/risk-factors/${id}`,
      )
      .then((r) => r.data),
  updateRiskFactor: (id: number, data: Record<string, unknown>) =>
    api.put<Record<string, unknown>>(`/ehr/risk-factors/${id}`, data).then((r) => r.data),
  deleteRiskFactor: (id: number) =>
    api.delete<Record<string, unknown>>(`/ehr/risk-factors/${id}`).then((r) => r.data),
  listRiskFactors: (patientId: string, params?: { skip?: number; limit?: number }) =>
    api
      .get<{ id: number; patient_id: number; factor: string; severity: string; notes?: string }[]>(
        `/ehr/patients/${patientId}/risk-factors`,
        { params },
      )
      .then((r) => r.data),

  // Immunizations
  createImmunization: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/ehr/immunizations", data).then((r) => r.data),
  getImmunization: (id: number) =>
    api.get<EHRImmunization>(`/ehr/immunizations/${id}`).then((r) => r.data),
  updateImmunization: (id: number, data: Record<string, unknown>) =>
    api.put<Record<string, unknown>>(`/ehr/immunizations/${id}`, data).then((r) => r.data),
  deleteImmunization: (id: number) =>
    api.delete<Record<string, unknown>>(`/ehr/immunizations/${id}`).then((r) => r.data),
  listImmunizations: (patientId: string, params?: { skip?: number; limit?: number }) =>
    api
      .get<EHRImmunization[]>(`/ehr/patients/${patientId}/immunizations`, { params })
      .then((r) => r.data),

  // Attachments
  createAttachment: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/ehr/attachments", data).then((r) => r.data),
  getAttachment: (id: number) =>
    api
      .get<{ id: number; file_name: string; mime_type: string; file_size: number; uploaded_at: string }>(
        `/ehr/attachments/${id}`,
      )
      .then((r) => r.data),
  updateAttachment: (id: number, data: Record<string, unknown>) =>
    api.put<Record<string, unknown>>(`/ehr/attachments/${id}`, data).then((r) => r.data),
  deleteAttachment: (id: number) =>
    api.delete<Record<string, unknown>>(`/ehr/attachments/${id}`).then((r) => r.data),
  listAttachments: (patientId: string, params?: { skip?: number; limit?: number }) =>
    api
      .get<{ id: number; file_name: string; mime_type: string; file_size: number }[]>(
        `/ehr/patients/${patientId}/attachments`,
        { params },
      )
      .then((r) => r.data),

  // Patient Summary
  getPatientEhr: (patientId: string) =>
    api
      .get<{
        patient: {
          id: string;
          full_name: string | null;
          health_id: string;
          date_of_birth: string | null;
          gender: string | null;
          phone: string | null;
        };
        clinical_notes: EHRNote[];
        conditions: EHRCondition[];
        medications: EHRMedication[];
        allergies: EHRAllergy[];
        immunizations: EHRImmunization[];
      }>(`/ehr/patient/${patientId}`)
      .then((r) => r.data),
  getPatientSummary: (patientId: string) =>
    api
      .get<{
        patient_id: string;
        patient_name: string | null;
        health_id: string;
        age: number | null;
        gender: string | null;
        active_allergies: unknown[];
        active_conditions: unknown[];
        active_diagnoses: unknown[];
        current_medications: unknown[];
        immunizations: unknown[];
      }>(`/ehr/patient/${patientId}/summary`)
      .then((r) => r.data),
};

// ── EHR FHIR (all FHIR resources) ──
export const ehrFhirApi = {
  getPatient: (id: string) => api.get<FHIRResource>(`/fhir/Patient/${id}`).then((r) => r.data),
  getEncounter: (id: string) => api.get<FHIRResource>(`/fhir/Encounter/${id}`).then((r) => r.data),
  getCondition: (id: string) => api.get<FHIRResource>(`/fhir/Condition/${id}`).then((r) => r.data),
  searchConditions: (params?: Record<string, unknown>) =>
    api.get<FHIRResource[]>("/fhir/Condition", { params }).then((r) => r.data),
  getObservation: (id: string) => api.get<FHIRResource>(`/fhir/Observation/${id}`).then((r) => r.data),
  searchObservations: (params?: Record<string, unknown>) =>
    api.get<FHIRResource[]>("/fhir/Observation", { params }).then((r) => r.data),
  getMedicationRequest: (id: string) =>
    api.get<FHIRResource>(`/fhir/MedicationRequest/${id}`).then((r) => r.data),
  searchMedicationRequests: (params?: Record<string, unknown>) =>
    api.get<FHIRResource[]>("/fhir/MedicationRequest", { params }).then((r) => r.data),
  getMedicationStatement: (id: string) =>
    api.get<FHIRResource>(`/fhir/MedicationStatement/${id}`).then((r) => r.data),
  getCarePlan: (id: string) => api.get<FHIRResource>(`/fhir/CarePlan/${id}`).then((r) => r.data),
  getProcedure: (id: string) => api.get<FHIRResource>(`/fhir/Procedure/${id}`).then((r) => r.data),
  searchProcedures: (params?: Record<string, unknown>) =>
    api.get<FHIRResource[]>("/fhir/Procedure", { params }).then((r) => r.data),
  getAllergyIntolerance: (id: string) =>
    api.get<FHIRResource>(`/fhir/AllergyIntolerance/${id}`).then((r) => r.data),
  searchAllergyIntolerances: (params?: Record<string, unknown>) =>
    api.get<FHIRResource[]>("/fhir/AllergyIntolerance", { params }).then((r) => r.data),
  getImmunization: (id: string) =>
    api.get<FHIRResource>(`/fhir/Immunization/${id}`).then((r) => r.data),
  searchImmunizations: (params?: Record<string, unknown>) =>
    api.get<FHIRResource[]>("/fhir/Immunization", { params }).then((r) => r.data),
  getDocumentReference: (id: string) =>
    api.get<FHIRResource>(`/fhir/DocumentReference/${id}`).then((r) => r.data),
  searchDocumentReferences: (params?: Record<string, unknown>) =>
    api.get<FHIRResource[]>("/fhir/DocumentReference", { params }).then((r) => r.data),
  getComposition: (id: string) =>
    api.get<FHIRResource>(`/fhir/Composition/${id}`).then((r) => r.data),
  searchCompositions: (params?: Record<string, unknown>) =>
    api.get<FHIRResource[]>("/fhir/Composition", { params }).then((r) => r.data),
  getBundle: (id: string) => api.get<FHIRResource>(`/fhir/Bundle/${id}`).then((r) => r.data),
  createResource: (resourceType: string, data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>(`/fhir/${resourceType}`, data).then((r) => r.data),
  updateResource: (resourceType: string, id: string, data: Record<string, unknown>) =>
    api.put<Record<string, unknown>>(`/fhir/${resourceType}/${id}`, data).then((r) => r.data),
  deleteResource: (resourceType: string, id: string) =>
    api.delete<Record<string, unknown>>(`/fhir/${resourceType}/${id}`).then((r) => r.data),
  executeBatch: (data: Record<string, unknown>) =>
    api.post<Record<string, unknown>>("/fhir", data).then((r) => r.data),
};

// ── Care Continuum ──
export const careContinuumApi = {
  // Primary Care
  createPrimaryCareEncounter: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/care-continuum/primary-care-encounters", data).then((r) => r.data),
  getPrimaryCareEncounter: (id: number) => api.get<Record<string, unknown>>(`/care-continuum/primary-care-encounters/${id}`).then((r) => r.data),
  listPrimaryCareEncounters: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/care-continuum/primary-care-encounters", { params }).then((r) => r.data),
  updatePrimaryCareEncounter: (id: number, data: Record<string, unknown>) => api.put<Record<string, unknown>>(`/care-continuum/primary-care-encounters/${id}`, data).then((r) => r.data),

  // Family Medicine
  createFamilyMedicineRecord: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/care-continuum/family-medicine-records", data).then((r) => r.data),
  getFamilyMedicineRecord: (id: number) => api.get<Record<string, unknown>>(`/care-continuum/family-medicine-records/${id}`).then((r) => r.data),

  // Community Clinic
  createCommunityClinicRecord: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/care-continuum/community-clinic-records", data).then((r) => r.data),
  getCommunityClinicRecord: (id: number) => api.get<Record<string, unknown>>(`/care-continuum/community-clinic-records/${id}`).then((r) => r.data),

  // Health Assessments
  createHealthAssessment: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/care-continuum/health-assessments", data).then((r) => r.data),
  listHealthAssessments: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/care-continuum/health-assessments", { params }).then((r) => r.data),

  // Preventive Care
  createPreventiveCareRecord: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/care-continuum/preventive-care-records", data).then((r) => r.data),
  getPreventiveCareRecord: (id: number) => api.get<Record<string, unknown>>(`/care-continuum/preventive-care-records/${id}`).then((r) => r.data),

  // Referrals
  createReferral: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/care-continuum/referrals", data).then((r) => r.data),
  acceptReferral: (id: number) => api.put<Record<string, unknown>>(`/care-continuum/referrals/${id}/accept`).then((r) => r.data),
  rejectReferral: (id: number) => api.put<Record<string, unknown>>(`/care-continuum/referrals/${id}/reject`).then((r) => r.data),
  updateReferral: (id: number, data: Record<string, unknown>) => api.put<Record<string, unknown>>(`/care-continuum/referrals/${id}`, data).then((r) => r.data),
  listReferrals: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/care-continuum/referrals", { params }).then((r) => r.data),
  getReferral: (id: number) => api.get<Record<string, unknown>>(`/care-continuum/referrals/${id}`).then((r) => r.data),

  // Care Journeys
  createCareJourney: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/care-continuum/care-journeys", data).then((r) => r.data),
  getCareJourney: (id: number) => api.get<Record<string, unknown>>(`/care-continuum/care-journeys/${id}`).then((r) => r.data),
  listCareJourneys: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/care-continuum/care-journeys", { params }).then((r) => r.data),

  // Follow-up Plans
  createFollowUpPlan: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/care-continuum/follow-up-plans", data).then((r) => r.data),
  listFollowUpPlans: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/care-continuum/follow-up-plans", { params }).then((r) => r.data),

  // Care Coordination
  createCareCoordination: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/care-continuum/care-coordination", data).then((r) => r.data),
  listCareCoordination: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/care-continuum/care-coordination", { params }).then((r) => r.data),

  // Transitions of Care
  createTransitionOfCare: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/care-continuum/transitions-of-care", data).then((r) => r.data),
  createClinicalHandover: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/care-continuum/clinical-handovers", data).then((r) => r.data),

  // Home Care
  createHomeCarePlan: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/care-continuum/home-care-plans", data).then((r) => r.data),
  listHomeCarePlans: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/care-continuum/home-care-plans", { params }).then((r) => r.data),

  // Community Care
  createCommunityCareRecord: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/care-continuum/community-care-records", data).then((r) => r.data),
  getCommunityCareRecord: (id: number) => api.get<Record<string, unknown>>(`/care-continuum/community-care-records/${id}`).then((r) => r.data),

  // Maternal Health
  createPregnancyRecord: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/care-continuum/pregnancy-records", data).then((r) => r.data),
  getPregnancyRecord: (id: number) => api.get<Record<string, unknown>>(`/care-continuum/pregnancy-records/${id}`).then((r) => r.data),
  listPregnancyRecords: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/care-continuum/pregnancy-records", { params }).then((r) => r.data),
  createDeliveryRecord: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/care-continuum/delivery-records", data).then((r) => r.data),
  createGrowthMonitoringRecord: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/care-continuum/growth-monitoring", data).then((r) => r.data),

  // Vaccinations
  createVaccinationRecord: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/care-continuum/vaccination-records", data).then((r) => r.data),
  getVaccinationRecord: (id: number) => api.get<Record<string, unknown>>(`/care-continuum/vaccination-records/${id}`).then((r) => r.data),

  // Reminders
  createReminderSchedule: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/care-continuum/reminder-schedules", data).then((r) => r.data),
  getReminderSchedule: (id: number) => api.get<Record<string, unknown>>(`/care-continuum/reminder-schedules/${id}`).then((r) => r.data),

  // Health Programs
  createHealthProgram: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/care-continuum/health-programs", data).then((r) => r.data),
  listHealthPrograms: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/care-continuum/health-programs", { params }).then((r) => r.data),

  // Community Visits
  createCommunityVisit: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/care-continuum/community-visits", data).then((r) => r.data),

  // Patient Tasks
  createPatientTask: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/care-continuum/patient-tasks", data).then((r) => r.data),
  listPatientTasks: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/care-continuum/patient-tasks", { params }).then((r) => r.data),

  // Population Health
  createPopulationHealthRecord: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/care-continuum/population-health", data).then((r) => r.data),
  createChronicDiseaseRecord: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/care-continuum/chronic-disease", data).then((r) => r.data),
  createMentalHealthRecord: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/care-continuum/mental-health", data).then((r) => r.data),
};

// ── Clinical ──
export const clinicalFullApi = {
  // Terminology
  listCodes: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/terminology/codes", { params }).then((r) => r.data),
  createCode: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/terminology/codes", data).then((r) => r.data),
  getCode: (id: number) => api.get<Record<string, unknown>>(`/clinical/terminology/codes/${id}`).then((r) => r.data),
  updateCode: (id: number, data: Record<string, unknown>) => api.put<Record<string, unknown>>(`/clinical/terminology/codes/${id}`, data).then((r) => r.data),
  deleteCode: (id: number) => api.delete<Record<string, unknown>>(`/clinical/terminology/codes/${id}`).then((r) => r.data),
  listTerminologyVersions: () => api.get<Record<string, unknown>>("/clinical/terminology/versions").then((r) => r.data),
  createTerminologyVersion: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/terminology/versions", data).then((r) => r.data),
  createMapping: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/terminology/mappings", data).then((r) => r.data),
  listValueSets: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/terminology/value-sets", { params }).then((r) => r.data),
  createValueSet: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/terminology/value-sets", data).then((r) => r.data),
  createValueSetMember: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/terminology/value-set-members", data).then((r) => r.data),
  listCodeSystems: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/terminology/code-systems", { params }).then((r) => r.data),
  createCodeSystem: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/terminology/code-systems", data).then((r) => r.data),
  searchIcd10: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/terminology/icd10", { params }).then((r) => r.data),
  searchLoinc: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/terminology/loinc", { params }).then((r) => r.data),
  searchSnomed: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/terminology/snomed", { params }).then((r) => r.data),
  fhirExpandValueSet: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/terminology/fhir/$expand", { params }).then((r) => r.data),
  fhirLookupCode: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/terminology/fhir/$lookup", { params }).then((r) => r.data),

  // Knowledge
  listGuidelines: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/knowledge/guidelines", { params }).then((r) => r.data),
  createGuideline: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/knowledge/guidelines", data).then((r) => r.data),
  getGuideline: (id: number) => api.get<Record<string, unknown>>(`/clinical/knowledge/guidelines/${id}`).then((r) => r.data),
  updateGuideline: (id: number, data: Record<string, unknown>) => api.put<Record<string, unknown>>(`/clinical/knowledge/guidelines/${id}`, data).then((r) => r.data),
  listProtocols: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/knowledge/protocols", { params }).then((r) => r.data),
  createProtocol: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/knowledge/protocols", data).then((r) => r.data),
  getProtocol: (id: number) => api.get<Record<string, unknown>>(`/clinical/knowledge/protocols/${id}`).then((r) => r.data),
  updateProtocol: (id: number, data: Record<string, unknown>) => api.put<Record<string, unknown>>(`/clinical/knowledge/protocols/${id}`, data).then((r) => r.data),
  listPathways: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/knowledge/pathways", { params }).then((r) => r.data),
  createPathway: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/knowledge/pathways", data).then((r) => r.data),
  getPathway: (id: number) => api.get<Record<string, unknown>>(`/clinical/knowledge/pathways/${id}`).then((r) => r.data),
  updatePathway: (id: number, data: Record<string, unknown>) => api.put<Record<string, unknown>>(`/clinical/knowledge/pathways/${id}`, data).then((r) => r.data),
  approveGuideline: (id: number, data: Record<string, unknown>) => api.post<Record<string, unknown>>(`/clinical/knowledge/guidelines/${id}/approvals`, data).then((r) => r.data),
  listStandingOrders: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/knowledge/standing-orders", { params }).then((r) => r.data),
  createStandingOrder: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/knowledge/standing-orders", data).then((r) => r.data),
  listRecommendations: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/knowledge/recommendations", { params }).then((r) => r.data),

  // CDS (Clinical Decision Support)
  getOrderSetRecommendations: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/cds/order-set-recommendations", data).then((r) => r.data),
  checkContraindication: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/cds/contraindication-check", data).then((r) => r.data),
  checkDuplicateOrder: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/cds/duplicate-order-check", data).then((r) => r.data),
  checkDrugInteraction: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/cds/drug-interaction-check", data).then((r) => r.data),
  createAlert: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/cds/alerts", data).then((r) => r.data),
  listAlerts: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/cds/alerts", { params }).then((r) => r.data),
  acknowledgeAlert: (id: number) => api.put<Record<string, unknown>>(`/clinical/cds/alerts/${id}/acknowledge`).then((r) => r.data),
  listReminders: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/cds/reminders", { params }).then((r) => r.data),
  checkCareBundleCompliance: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/cds/care-bundle-compliance", data).then((r) => r.data),

  // Quality
  listQualityIndicators: () => api.get<Record<string, unknown>>("/clinical/quality/indicators").then((r) => r.data),
  createQualityIndicator: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/quality/indicators", data).then((r) => r.data),
  createQualityMeasurement: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/quality/measurements", data).then((r) => r.data),
  listAuditRecords: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/quality/audit-records", { params }).then((r) => r.data),
  createAuditRecord: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/quality/audit-records", data).then((r) => r.data),
  createComplianceCheck: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/quality/compliance-checks", data).then((r) => r.data),
  listComplianceChecks: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/quality/compliance-checks", { params }).then((r) => r.data),
  listBenchmarks: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/quality/benchmarks", { params }).then((r) => r.data),
  createMortalityReview: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/quality/mortality-reviews", data).then((r) => r.data),
  createIncidentReport: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/quality/incident-reports", data).then((r) => r.data),
  createSafetyEvent: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/quality/safety-events", data).then((r) => r.data),
  getQualityDashboard: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/quality/dashboard", { params }).then((r) => r.data),

  // Research
  createRegistry: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/research/registries", data).then((r) => r.data),
  listRegistries: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/research/registries", { params }).then((r) => r.data),
  createCohort: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/research/cohorts", data).then((r) => r.data),
  listCohorts: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/research/cohorts", { params }).then((r) => r.data),
  exportDeidentified: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/research/export-deidentified", data).then((r) => r.data),

  // Clinical AI
  copilot: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/ai/copilot", data).then((r) => r.data),
  riskPrediction: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/ai/risk-prediction", data).then((r) => r.data),
  careGaps: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/ai/care-gaps", data).then((r) => r.data),
  diagnosticAssistant: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/ai/diagnostic-assistant", data).then((r) => r.data),
  explainAI: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/ai/explain", data).then((r) => r.data),
};

// ── Clinical Documentation ──
export const clinicalDocumentationApi = {
  createSoapNote: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/documentation/soap-notes", data).then((r) => r.data),
  createProgressNote: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/documentation/progress-notes", data).then((r) => r.data),
  createNursingNote: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/documentation/nursing-notes", data).then((r) => r.data),
  createConsultationNote: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/documentation/consultation-notes", data).then((r) => r.data),
  createOperationNote: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/documentation/operation-notes", data).then((r) => r.data),
  createEmergencyNote: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/documentation/emergency-notes", data).then((r) => r.data),
  list: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/documentation", { params }).then((r) => r.data),
  get: (id: number) => api.get<Record<string, unknown>>(`/clinical/documentation/${id}`).then((r) => r.data),
  listTemplates: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/documentation/templates", { params }).then((r) => r.data),
  createTemplate: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/documentation/templates", data).then((r) => r.data),
  sign: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/documentation/sign", data).then((r) => r.data),
  getVersions: (id: number) => api.get<Record<string, unknown>>(`/clinical/documentation/${id}/versions`).then((r) => r.data),
};

// ── Clinical Orders ──
export const clinicalOrdersApi = {
  create: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/orders", data).then((r) => r.data),
  list: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/orders", { params }).then((r) => r.data),
  get: (id: number) => api.get<Record<string, unknown>>(`/clinical/orders/${id}`).then((r) => r.data),
  cancel: (id: number) => api.put<Record<string, unknown>>(`/clinical/orders/${id}/cancel`).then((r) => r.data),
  complete: (id: number) => api.put<Record<string, unknown>>(`/clinical/orders/${id}/complete`).then((r) => r.data),
  listTemplates: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/orders/templates", { params }).then((r) => r.data),
  createTemplate: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/orders/templates", data).then((r) => r.data),
  createRecurring: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/orders/recurring", data).then((r) => r.data),
  listRecurring: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/orders/recurring", { params }).then((r) => r.data),
  listStanding: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/orders/standing", { params }).then((r) => r.data),
};

// ── Clinical Quality ──
export const clinicalQualityApi = {
  kpis: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/quality/kpis", { params }).then((r) => r.data),
  createMeasurement: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/clinical/quality/measurements", data).then((r) => r.data),
  complianceDashboard: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/quality/compliance-dashboard", { params }).then((r) => r.data),
  benchmarks: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/clinical/quality/benchmarks", { params }).then((r) => r.data),
};

// ── Hospital ──
export const hospitalApi = {
  list: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/hospital", { params }).then((r) => r.data),
  get: (id: number) => api.get<Record<string, unknown>>(`/hospital/${id}`).then((r) => r.data),
  create: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/hospital", data).then((r) => r.data),
  update: (id: number, data: Record<string, unknown>) => api.put<Record<string, unknown>>(`/hospital/${id}`, data).then((r) => r.data),
  deactivate: (id: number) => api.delete<Record<string, unknown>>(`/hospital/${id}`).then((r) => r.data),

  // Campuses
  listCampuses: (hospitalId: number) => api.get<Record<string, unknown>>(`/hospital/${hospitalId}/campuses`).then((r) => r.data),
  createCampus: (hospitalId: number, data: Record<string, unknown>) => api.post<Record<string, unknown>>(`/hospital/${hospitalId}/campuses`, data).then((r) => r.data),
  updateCampus: (campusId: number, data: Record<string, unknown>) => api.put<Record<string, unknown>>(`/hospital/campuses/${campusId}`, data).then((r) => r.data),
  listBuildings: (campusId: number) => api.get<Record<string, unknown>>(`/hospital/campuses/${campusId}/buildings`).then((r) => r.data),
  createBuilding: (campusId: number, data: Record<string, unknown>) => api.post<Record<string, unknown>>(`/hospital/campuses/${campusId}/buildings`, data).then((r) => r.data),
  listFloors: (buildingId: number) => api.get<Record<string, unknown>>(`/hospital/buildings/${buildingId}/floors`).then((r) => r.data),
  createFloor: (buildingId: number, data: Record<string, unknown>) => api.post<Record<string, unknown>>(`/hospital/buildings/${buildingId}/floors`, data).then((r) => r.data),

  // Departments
  listDepartments: (hospitalId: number) => api.get<Record<string, unknown>>(`/hospital/${hospitalId}/departments`).then((r) => r.data),
  createDepartment: (hospitalId: number, data: Record<string, unknown>) => api.post<Record<string, unknown>>(`/hospital/${hospitalId}/departments`, data).then((r) => r.data),
  updateDepartment: (deptId: number, data: Record<string, unknown>) => api.put<Record<string, unknown>>(`/hospital/departments/${deptId}`, data).then((r) => r.data),
  listClinics: (deptId: number) => api.get<Record<string, unknown>>(`/hospital/departments/${deptId}/clinics`).then((r) => r.data),
  createClinic: (deptId: number, data: Record<string, unknown>) => api.post<Record<string, unknown>>(`/hospital/departments/${deptId}/clinics`, data).then((r) => r.data),

  // Rooms & Beds
  listRooms: (deptId: number) => api.get<Record<string, unknown>>(`/hospital/departments/${deptId}/rooms`).then((r) => r.data),
  createRoom: (deptId: number, data: Record<string, unknown>) => api.post<Record<string, unknown>>(`/hospital/departments/${deptId}/rooms`, data).then((r) => r.data),
  listBeds: (roomId: number) => api.get<Record<string, unknown>>(`/hospital/rooms/${roomId}/beds`).then((r) => r.data),
  createBed: (roomId: number, data: Record<string, unknown>) => api.post<Record<string, unknown>>(`/hospital/rooms/${roomId}/beds`, data).then((r) => r.data),
  assignBed: (bedId: number, data: Record<string, unknown>) => api.post<Record<string, unknown>>(`/hospital/beds/${bedId}/assign`, data).then((r) => r.data),
  dischargeBed: (bedId: number) => api.post<Record<string, unknown>>(`/hospital/beds/${bedId}/discharge`).then((r) => r.data),
  transferBed: (bedId: number, data: Record<string, unknown>) => api.post<Record<string, unknown>>(`/hospital/beds/${bedId}/transfer`, data).then((r) => r.data),
  bedAssignmentHistory: (bedId: number) => api.get<Record<string, unknown>>(`/hospital/beds/${bedId}/assignments`).then((r) => r.data),
  occupancy: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/hospital/occupancy", { params }).then((r) => r.data),

  // Units
  listUnits: (hospitalId: number) => api.get<Record<string, unknown>>(`/hospital/${hospitalId}/units`).then((r) => r.data),
  createUnit: (hospitalId: number, data: Record<string, unknown>) => api.post<Record<string, unknown>>(`/hospital/${hospitalId}/units`, data).then((r) => r.data),

  // Operation Theaters
  listOperationTheaters: (hospitalId: number) => api.get<Record<string, unknown>>(`/hospital/${hospitalId}/operation-theaters`).then((r) => r.data),
  createOperationTheater: (hospitalId: number, data: Record<string, unknown>) => api.post<Record<string, unknown>>(`/hospital/${hospitalId}/operation-theaters`, data).then((r) => r.data),
  updateOperationTheaterStatus: (otId: number, data: Record<string, unknown>) => api.put<Record<string, unknown>>(`/hospital/operation-theaters/${otId}/status`, data).then((r) => r.data),

  // Equipment
  listEquipment: (hospitalId: number) => api.get<Record<string, unknown>>(`/hospital/${hospitalId}/equipment`).then((r) => r.data),
  createEquipment: (hospitalId: number, data: Record<string, unknown>) => api.post<Record<string, unknown>>(`/hospital/${hospitalId}/equipment`, data).then((r) => r.data),
  updateEquipment: (equipId: number, data: Record<string, unknown>) => api.put<Record<string, unknown>>(`/hospital/equipment/${equipId}`, data).then((r) => r.data),

  // Cost Centers
  listCostCenters: (hospitalId: number) => api.get<Record<string, unknown>>(`/hospital/${hospitalId}/cost-centers`).then((r) => r.data),
  createCostCenter: (hospitalId: number, data: Record<string, unknown>) => api.post<Record<string, unknown>>(`/hospital/${hospitalId}/cost-centers`, data).then((r) => r.data),

  // Appointments
  listAppointments: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/hospital/appointments", { params }).then((r) => r.data),
  createAppointment: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/hospital/appointments", data).then((r) => r.data),

  // Dashboard
  getDashboard: (hospitalId: number) => api.get<Record<string, unknown>>(`/hospital/${hospitalId}/dashboard`).then((r) => r.data),
};

// ── National Data ──
export const nationalDataApi = {
  // Patients
  listPatients: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/national-data/patients", { params }).then((r) => r.data),
  getPatient: (id: string) => api.get<Record<string, unknown>>(`/national-data/patients/${id}`).then((r) => r.data),

  // Encounters
  listEncounters: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/national-data/encounters", { params }).then((r) => r.data),
  getEncounter: (id: string) => api.get<Record<string, unknown>>(`/national-data/encounters/${id}`).then((r) => r.data),
  createEncounter: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/national-data/encounters", data).then((r) => r.data),

  // Observations
  listObservations: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/national-data/observations", { params }).then((r) => r.data),
  getObservation: (id: string) => api.get<Record<string, unknown>>(`/national-data/observations/${id}`).then((r) => r.data),
  createObservation: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/national-data/observations", data).then((r) => r.data),

  // Golden Records
  listGoldenRecords: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/national-data/golden-records", { params }).then((r) => r.data),
  createGoldenRecord: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/national-data/golden-records", data).then((r) => r.data),
  resolveGoldenRecord: (id: string) => api.post<Record<string, unknown>>(`/national-data/golden-records/${id}/resolve`).then((r) => r.data),

  // Duplicate Check & Merge
  duplicateCheck: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/national-data/duplicate-check", data).then((r) => r.data),
  merge: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/national-data/merge", data).then((r) => r.data),

  // Events
  recordEvent: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/national-data/events", data).then((r) => r.data),
  replayEvents: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/national-data/events/replay", { params }).then((r) => r.data),

  // Data Catalog
  listDataCatalog: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/national-data/data-catalog", { params }).then((r) => r.data),
  createDataCatalogEntry: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/national-data/data-catalog", data).then((r) => r.data),

  // Data Quality
  recordDataQualityCheck: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/national-data/data-quality-checks", data).then((r) => r.data),
  getDataLineage: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/national-data/data-lineage", { params }).then((r) => r.data),
  recordDataLineage: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/national-data/data-lineage", data).then((r) => r.data),

  // Retention & Consent
  listRetentionPolicies: () => api.get<Record<string, unknown>>("/national-data/retention-policies").then((r) => r.data),
  createRetentionPolicy: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/national-data/retention-policies", data).then((r) => r.data),
  listConsentDirectives: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/national-data/consent-directives", { params }).then((r) => r.data),
  createConsentDirective: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/national-data/consent-directives", data).then((r) => r.data),

  // De-identification
  createDeidentificationJob: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/national-data/deidentification-jobs", data).then((r) => r.data),
  listDeidentificationJobs: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/national-data/deidentification-jobs", { params }).then((r) => r.data),

  // Features & ML
  listFeatureDefinitions: () => api.get<Record<string, unknown>>("/national-data/features").then((r) => r.data),
  createFeatureDefinition: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/national-data/features", data).then((r) => r.data),
  storeFeatureValues: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/national-data/feature-values", data).then((r) => r.data),
  getFeatureValues: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/national-data/feature-values", { params }).then((r) => r.data),
  listTrainingDatasets: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/national-data/training-datasets", { params }).then((r) => r.data),
  createTrainingDataset: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/national-data/training-datasets", data).then((r) => r.data),
  listVectorEmbeddings: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/national-data/vector-embeddings", { params }).then((r) => r.data),
  storeVectorEmbedding: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/national-data/vector-embeddings", data).then((r) => r.data),
};

// ── National Streaming ──
export const nationalStreamingApi = {
  streamFhir: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/national-data/streaming/fhir", data).then((r) => r.data),
  streamHl7: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/national-data/streaming/hl7", data).then((r) => r.data),
  streamEvent: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/national-data/streaming/events", data).then((r) => r.data),
  getCdcFeed: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/national-data/streaming/cdc", { params }).then((r) => r.data),
  recordCdcChange: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/national-data/streaming/cdc", data).then((r) => r.data),
};

// ── Edge ──
export const edgeApi = {
  // Devices
  listDevices: (params?: Record<string, unknown>) => api.get<{ devices: EdgeDevice[] }>("/edge/devices", { params }).then((r) => r.data),
  getDevice: (deviceId: string) => api.get<Record<string, unknown>>(`/edge/devices/${deviceId}`).then((r) => r.data),
  quarantineDevice: (deviceId: string) => api.post<Record<string, unknown>>(`/edge/devices/${deviceId}/quarantine`).then((r) => r.data),
  revokeDevice: (deviceId: string) => api.post<Record<string, unknown>>(`/edge/devices/${deviceId}/revoke`).then((r) => r.data),
  reinstateDevice: (deviceId: string) => api.post<Record<string, unknown>>(`/edge/devices/${deviceId}/reinstate`).then((r) => r.data),
  killSwitchDevice: (deviceId: string) => api.post<Record<string, unknown>>(`/edge/devices/${deviceId}/kill_switch`).then((r) => r.data),

  // Tasks
  createTask: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/edge/tasks", data).then((r) => r.data),
  listTasks: (params?: Record<string, unknown>) => api.get<{ tasks: EdgeTask[] }>("/edge/tasks", { params }).then((r) => r.data),
  getTask: (taskUid: string) => api.get<Record<string, unknown>>(`/edge/tasks/${taskUid}`).then((r) => r.data),
  cancelTask: (taskUid: string) => api.post<Record<string, unknown>>(`/edge/tasks/${taskUid}/cancel`).then((r) => r.data),

  // Policy
  getPolicy: () => api.get<Record<string, unknown>>("/edge/policy").then((r) => r.data),
  updatePolicy: (data: Record<string, unknown>) => api.put<Record<string, unknown>>("/edge/policy", data).then((r) => r.data),

  // Fleet
  fleetSummary: () => api.get<{ devices_total: number; online_devices: number; pending_tasks: number; tasks_completed_total: number }>("/edge/fleet/summary").then((r) => r.data),

  // Models
  createModel: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/edge/models", data).then((r) => r.data),
  listModels: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/edge/models", { params }).then((r) => r.data),
  updateModelStatus: (modelUid: string, data: Record<string, unknown>) => api.post<Record<string, unknown>>(`/edge/models/${modelUid}/status`, data).then((r) => r.data),
  assignModel: (modelUid: string, data: Record<string, unknown>) => api.post<Record<string, unknown>>(`/edge/models/${modelUid}/assign`, data).then((r) => r.data),

  // Agent
  agentHeartbeat: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/edge/agent/heartbeat", data).then((r) => r.data),
  agentTaskResult: (taskUid: string, data: Record<string, unknown>) => api.post<Record<string, unknown>>(`/edge/agent/tasks/${taskUid}/result`, data).then((r) => r.data),
  agentTelemetry: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/edge/agent/telemetry", data).then((r) => r.data),

  // Health
  health: () => api.get<Record<string, unknown>>("/edge/health").then((r) => r.data),
};

// ── Consent ──
export const consentApi = {
  grant: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/consent/grant", data).then((r) => r.data),
  revoke: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/consent/revoke", data).then((r) => r.data),
  check: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/consent/check", { params }).then((r) => r.data),
};

// ── Claims ──
export const claimsApi = {
  create: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/claims", data).then((r) => r.data),
  validate: (claimId: string) => api.post<Record<string, unknown>>(`/claims/${claimId}/validate`).then((r) => r.data),
  submit: (claimId: string) => api.post<Record<string, unknown>>(`/claims/${claimId}/submit`).then((r) => r.data),
  get: (claimId: string) => api.get<Record<string, unknown>>(`/claims/${claimId}`).then((r) => r.data),
};

// ── Insurance ──
export const insuranceApi = {
  get: (insuranceId: string) => api.get<Record<string, unknown>>(`/insurance/${insuranceId}`).then((r) => r.data),
};

// ── Citizen Portal ──
export const citizenPortalApi = {
  login: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/citizen/login", data).then((r) => r.data),
  logout: () => api.post<Record<string, unknown>>("/citizen/logout").then((r) => r.data),
  profile: () => api.get<Record<string, unknown>>("/citizen/profile").then((r) => r.data),
  results: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/citizen/results", { params }).then((r) => r.data),
  orders: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/citizen/orders", { params }).then((r) => r.data),
  healthRecord: () => api.get<Record<string, unknown>>("/citizen/health-record").then((r) => r.data),
};

// ── OAuth2 ──
export const oauth2Api = {
  register: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/oauth2/register", data).then((r) => r.data),
  authorize: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/oauth2/authorize", { params }).then((r) => r.data),
  token: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/oauth2/token", data).then((r) => r.data),
  introspect: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/oauth2/introspect", data).then((r) => r.data),
  revoke: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/oauth2/revoke", data).then((r) => r.data),
  openidConfig: () => api.get<Record<string, unknown>>("/oauth2/.well-known/openid-configuration").then((r) => r.data),
  jwks: () => api.get<Record<string, unknown>>("/oauth2/jwks.json").then((r) => r.data),
};

// ── SAML ──
export const samlApi = {
  metadata: () => api.get<Record<string, unknown>>("/auth/saml/metadata").then((r) => r.data),
  acs: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/auth/saml/acs", data).then((r) => r.data),
};

// ── Mobile ──
export const mobileApi = {
  refresh: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/auth/refresh", data).then((r) => r.data),
  changePassword: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/auth/change-password", data).then((r) => r.data),
  info: () => api.get<Record<string, unknown>>("/mobile/info").then((r) => r.data),
};

// ── Integrations ──
export const integrationsApi = {
  status: () => api.get<Record<string, unknown>>("/integrations/status").then((r) => r.data),
  probe: (name: string) => api.post<Record<string, unknown>>(`/integrations/${name}/probe`).then((r) => r.data),
};

// ── Optimizer ──
export const optimizerApi = {
  metrics: () => api.get<Record<string, unknown>>("/api/optimizer/metrics").then((r) => r.data),
  analyze: () => api.get<Record<string, unknown>>("/api/optimizer/analyze").then((r) => r.data),
};

// ── Financial ──
export const financialApi = {
  billingStatus: () => api.get<Record<string, unknown>>("/financial/billing/status").then((r) => r.data),
  billingRates: () => api.get<Record<string, unknown>>("/financial/billing/rates").then((r) => r.data),
  listInvoices: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/financial/invoices", { params }).then((r) => r.data),
  getInvoice: (id: string) => api.get<Record<string, unknown>>(`/financial/invoices/${id}`).then((r) => r.data),
  createInvoice: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/financial/invoices", data).then((r) => r.data),
  createPayment: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/financial/payments", data).then((r) => r.data),
  listPayments: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/financial/payments", { params }).then((r) => r.data),
  receivables: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/financial/receivables", { params }).then((r) => r.data),
  receivablesAging: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/financial/receivables/aging", { params }).then((r) => r.data),
  payables: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/financial/payables", { params }).then((r) => r.data),
  calculatePricing: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/financial/pricing/calculate", data).then((r) => r.data),
  createPricingRule: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/financial/pricing/rules", data).then((r) => r.data),
  listPricingRules: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/financial/pricing/rules", { params }).then((r) => r.data),
  createTransaction: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/financial/transactions", data).then((r) => r.data),
  listTransactions: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/financial/transactions", { params }).then((r) => r.data),
  runBillingCycle: () => api.post<Record<string, unknown>>("/financial/billing/run-cycle").then((r) => r.data),
  reportsSummary: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/financial/reports/summary", { params }).then((r) => r.data),
  listSubscriptions: (params?: Record<string, unknown>) => api.get<Record<string, unknown>>("/financial/subscriptions", { params }).then((r) => r.data),
};

// ── Kernel Runtime ──
export const kernelRuntimeApi = {
  health: () => api.get<Record<string, unknown>>("/kernel/runtime/health").then((r) => r.data),
  metrics: () => api.get<Record<string, unknown>>("/kernel/runtime/metrics").then((r) => r.data),
  digitalTwin: () => api.get<Record<string, unknown>>("/kernel/runtime/digital-twin").then((r) => r.data),
  topology: () => api.get<Record<string, unknown>>("/kernel/runtime/topology").then((r) => r.data),
  resources: () => api.get<Record<string, unknown>>("/kernel/runtime/resources").then((r) => r.data),
  optimize: () => api.post<Record<string, unknown>>("/kernel/runtime/optimize").then((r) => r.data),
  slowQueries: () => api.get<Record<string, unknown>>("/kernel/runtime/observability/slow-queries").then((r) => r.data),
  validationReport: () => api.get<Record<string, unknown>>("/kernel/runtime/validation/report").then((r) => r.data),
  runValidation: () => api.post<Record<string, unknown>>("/kernel/runtime/validation/run").then((r) => r.data),
  aiModels: () => api.get<Record<string, unknown>>("/kernel/runtime/ai/models").then((r) => r.data),
  aiInfer: (data: Record<string, unknown>) => api.post<Record<string, unknown>>("/kernel/runtime/ai/infer", data).then((r) => r.data),
  listRules: () => api.get<Record<string, unknown>>("/kernel/runtime/rules").then((r) => r.data),
  listPolicies: () => api.get<Record<string, unknown>>("/kernel/runtime/policies").then((r) => r.data),
};
