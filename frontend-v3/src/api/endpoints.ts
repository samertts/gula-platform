import { api } from './client';
import { buildQueryString } from '@/lib/utils';
import type {
  LoginRequest, LoginResponse, LabUser, Lab, Patient, LabOrder,
  LabResult, Sample, TestType, QualityControl, AuditLog, DashboardStats,
  StatsSummary, StatsTrend, TurnaroundTime, CriticalAlert, EdgeDevice,
  EdgeTask, Claim, Organization, Facility, LabSubscription, FeatureFlag,
  UpgradeRequest, PaginatedResponse, AdminCreateUser, AdminUpdateUser,
  AdminCreateLab, AdminUpdateLab, CreatePatientRequest, UpdatePatientRequest,
  CreateOrderRequest, CreateSampleRequest, CreateResultRequest, QCSubmission,
  PatientCard, ClinicalOrder, ClinicalDocumentation, Appointment,
  ConsentRecord, IntegrationStatus, SecurityStatus, FHIRResource,
  EHRNote, EHRCondition, EHRMedication, EHRAllergy, EHRImmunization,
} from '@/types/backend';

type RequestOptions = { skip?: number; limit?: number; [key: string]: any };

export const auth = {
  login: (data: LoginRequest) =>
    api.post<LoginResponse>('/login', data).then((r) => r.data),
  logout: () => api.post('/logout').then((r) => r.data),
  register: (data: any) => api.post('/register', data).then((r) => r.data),
  registerCitizen: (data: any) => api.post('/register/citizen', data).then((r) => r.data),
  registerStaff: (data: any) => api.post('/register/staff', data).then((r) => r.data),
  registerDoctor: (data: any) => api.post('/register/doctor', data).then((r) => r.data),
  refresh: (refreshToken: string) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }).then((r) => r.data),
  changePassword: (currentPassword: string, newPassword: string) =>
    api.post('/auth/change-password', { current_password: currentPassword, new_password: newPassword }).then((r) => r.data),
  forgotPassword: (email: string) =>
    api.post('/auth/forgot-password', { email }).then((r) => r.data),
  resetPassword: (token: string, password: string) =>
    api.post('/auth/reset-password', { token, password }).then((r) => r.data),
  mfaStatus: () => api.get('/mfa/status').then((r) => r.data),
  mfaSetup: () => api.post('/mfa/totp/setup').then((r) => r.data),
  mfaVerify: (token: string) => api.post('/mfa/totp/verify', { token }).then((r) => r.data),
  sessions: () => api.get('/auth/sessions').then((r) => r.data),
  revokeSession: (sessionId: number) => api.delete(`/auth/sessions/${sessionId}`).then((r) => r.data),
};

export const me = {
  lab: () => api.get<Lab>('/labs/me').then((r) => r.data),
  updateLab: (data: any) => api.put('/labs/me', data).then((r) => r.data),
  resetToken: () => api.post('/labs/me/reset-token').then((r) => r.data),
};

export const patients = {
  list: (opts?: RequestOptions) =>
    api.get<PaginatedResponse<Patient>>(`/patients${buildQueryString(opts || {})}`).then((r) => r.data),
  get: (id: number) =>
    api.get<Patient>(`/patients/${id}`).then((r) => r.data),
  create: (data: CreatePatientRequest) =>
    api.post<Patient>('/patients', data).then((r) => r.data),
  update: (id: number, data: UpdatePatientRequest) =>
    api.put<Patient>(`/patients/${id}`, data).then((r) => r.data),
  family: (familyId: string) =>
    api.get<Patient[]>(`/patients/family/${familyId}`).then((r) => r.data),
  children: (id: number) =>
    api.get<Patient[]>(`/patients/${id}/children`).then((r) => r.data),
  history: (id: number) =>
    api.get(`/patient-history/${id}`).then((r) => r.data),
};

export const orders = {
  list: (opts?: RequestOptions) =>
    api.get<PaginatedResponse<LabOrder>>(`/orders${buildQueryString(opts || {})}`).then((r) => r.data),
  get: (id: number) =>
    api.get<LabOrder>(`/orders/${id}`).then((r) => r.data),
  create: (data: CreateOrderRequest) =>
    api.post<LabOrder>('/orders', data).then((r) => r.data),
  validate: (id: number) =>
    api.post(`/orders/${id}/validate`).then((r) => r.data),
  cancel: (id: number) =>
    api.post(`/orders/${id}/cancel`).then((r) => r.data),
  createBatch: (orders: CreateOrderRequest[]) =>
    api.post('/batch/orders', { orders }).then((r) => r.data),
};

export const results = {
  get: (id: number) =>
    api.get<LabResult>(`/test-results/${id}`).then((r) => r.data),
  create: (data: CreateResultRequest) =>
    api.post<LabResult>('/test-results/', data).then((r) => r.data),
  validate: (data: any) =>
    api.post('/test-results/validate', data).then((r) => r.data),
  verify: (id: number) =>
    api.put(`/test-results/${id}/verify`).then((r) => r.data),
  citizenResults: (healthId: string, opts?: RequestOptions) =>
    api.get(`/test-results/citizen/${healthId}${buildQueryString(opts || {})}`).then((r) => r.data),
  citizenTimeline: (healthId: string) =>
    api.get(`/test-results/citizen/${healthId}/timeline`).then((r) => r.data),
  publicResult: (token: string) =>
    api.get(`/r/${token}`).then((r) => r.data),
  downloadPdf: (token: string) =>
    api.get(`/r/${token}/pdf`, { responseType: 'blob' }).then((r) => r.data),
  publicHistory: (phone: string, name: string) =>
    api.get(`/history/${phone}`, { params: { name } }).then((r) => r.data),
  interpret: (token: string) =>
    api.get(`/api/ai/interpret/${token}`).then((r) => r.data),
  analyze: (orderId: number) =>
    api.post(`/analyze`, { order_id: orderId }).then((r) => r.data),
};

export const samples = {
  list: (opts?: RequestOptions) =>
    api.get<PaginatedResponse<Sample>>(`/samples${buildQueryString(opts || {})}`).then((r) => r.data),
  get: (barcode: string) =>
    api.get<Sample>(`/samples/${barcode}`).then((r) => r.data),
  create: (data: CreateSampleRequest) =>
    api.post<Sample>('/samples', data).then((r) => r.data),
  update: (barcode: string, data: Partial<CreateSampleRequest>) =>
    api.put<Sample>(`/samples/${barcode}`, data).then((r) => r.data),
};

export const testTypes = {
  list: () => api.get<TestType[]>('/test-types').then((r) => r.data),
  profiles: () => api.get('/test-profiles').then((r) => r.data),
};

export const dashboard = {
  stats: () => api.get<DashboardStats>('/dashboard').then((r) => r.data),
  greeting: () => api.get('/greeting').then((r) => r.data),
  metrics: () => api.get('/metrics').then((r) => r.data),
};

export const stats = {
  summary: () => api.get<StatsSummary>('/stats/summary').then((r) => r.data),
  daily: (days?: number) =>
    api.get<StatsTrend[]>(`/stats/trends/daily${days ? `?days=${days}` : ''}`).then((r) => r.data),
  tests: (limit?: number) =>
    api.get(`/stats/trends/tests${limit ? `?limit=${limit}` : ''}`).then((r) => r.data),
  flags: () => api.get('/stats/trends/flags').then((r) => r.data),
  patients: (weeks?: number) =>
    api.get(`/stats/trends/patients${weeks ? `?weeks=${weeks}` : ''}`).then((r) => r.data),
  turnaround: () => api.get<TurnaroundTime[]>('/stats/turnaround').then((r) => r.data),
};

export const qualityControl = {
  list: (opts?: RequestOptions) =>
    api.get<PaginatedResponse<QualityControl>>(`/qc${buildQueryString(opts || {})}`).then((r) => r.data),
  submit: (data: QCSubmission) =>
    api.post<QualityControl>('/qc', data).then((r) => r.data),
  submitBatch: (data: QCSubmission[]) =>
    api.post('/qc/batch', data).then((r) => r.data),
  summary: () => api.get('/qc/summary').then((r) => r.data),
};

export const criticalAlerts = {
  list: (opts?: { hours?: number; acknowledged?: boolean }) =>
    api.get<CriticalAlert[]>(`/alerts${buildQueryString(opts || {})}`).then((r) => r.data),
  stats: () => api.get('/alerts/stats').then((r) => r.data),
};

export const admin = {
  users: {
    list: (opts?: RequestOptions) =>
      api.get<PaginatedResponse<LabUser>>(`/admin/users${buildQueryString(opts || {})}`).then((r) => r.data),
    create: (data: AdminCreateUser) =>
      api.post<LabUser>('/admin/users', data).then((r) => r.data),
    update: (id: number, data: AdminUpdateUser) =>
      api.patch(`/admin/users/${id}`, data).then((r) => r.data),
    delete: (id: number) =>
      api.delete(`/admin/users/${id}`).then((r) => r.data),
  },
  labs: {
    list: (opts?: RequestOptions) =>
      api.get<PaginatedResponse<Lab>>(`/admin/labs${buildQueryString(opts || {})}`).then((r) => r.data),
    create: (data: AdminCreateLab) =>
      api.post<Lab>('/admin/labs', data).then((r) => r.data),
    update: (id: number, data: AdminUpdateLab) =>
      api.patch(`/admin/labs/${id}`, data).then((r) => r.data),
    delete: (id: number) =>
      api.delete(`/admin/labs/${id}`).then((r) => r.data),
  },
  auditLog: (opts?: RequestOptions) =>
    api.get<PaginatedResponse<AuditLog>>(`/admin/audit-log${buildQueryString(opts || {})}`).then((r) => r.data),
  auditLogStats: (days?: number) =>
    api.get(`/admin/audit-log/stats${days ? `?days=${days}` : ''}`).then((r) => r.data),
  labAuditLog: (labId: number, opts?: RequestOptions) =>
    api.get(`/admin/labs/${labId}/audit-log${buildQueryString(opts || {})}`).then((r) => r.data),
  systemHealth: () => api.get('/admin/system/health').then((r) => r.data),
  systemConfig: () => api.get('/admin/system/config').then((r) => r.data),
  updateConfig: (data: any) => api.post('/admin/system/config', data).then((r) => r.data),
  reloadConfig: () => api.post('/admin/system/config/reload').then((r) => r.data),
  platformStats: () => api.get('/admin/stats').then((r) => r.data),
  maintenance: (data: any) => api.post('/admin/maintenance', data).then((r) => r.data),
  broadcast: (data: any) => api.post('/admin/broadcast', data).then((r) => r.data),
  upgradeDemands: () => api.get('/admin/tiers/demands').then((r) => r.data),
  setLabTier: (labId: number, tier: string) =>
    api.put(`/admin/tiers/${labId}`, { tier }).then((r) => r.data),
  setFeatureFlag: (labId: number, data: any) =>
    api.post(`/admin/tiers/flags/${labId}`, data).then((r) => r.data),
  featureFlags: (labId: number) =>
    api.get<FeatureFlag[]>(`/admin/tiers/flags/${labId}`).then((r) => r.data),
};

export const ehr = {
  notes: {
    list: (patientId: number) =>
      api.get<EHRNote[]>(`/ehr/${patientId}/notes`).then((r) => r.data),
    create: (patientId: number, data: any) =>
      api.post(`/ehr/${patientId}/notes`, data).then((r) => r.data),
  },
  conditions: {
    list: (patientId: number) =>
      api.get<EHRCondition[]>(`/ehr/${patientId}/conditions`).then((r) => r.data),
    create: (patientId: number, data: any) =>
      api.post(`/ehr/${patientId}/conditions`, data).then((r) => r.data),
  },
  medications: {
    list: (patientId: number) =>
      api.get<EHRMedication[]>(`/ehr/${patientId}/medications`).then((r) => r.data),
    create: (patientId: number, data: any) =>
      api.post(`/ehr/${patientId}/medications`, data).then((r) => r.data),
  },
  allergies: {
    list: (patientId: number) =>
      api.get<EHRAllergy[]>(`/ehr/${patientId}/allergies`).then((r) => r.data),
    create: (patientId: number, data: any) =>
      api.post(`/ehr/${patientId}/allergies`, data).then((r) => r.data),
  },
  immunizations: {
    list: (patientId: number) =>
      api.get<EHRImmunization[]>(`/ehr/${patientId}/immunizations`).then((r) => r.data),
    create: (patientId: number, data: any) =>
      api.post(`/ehr/${patientId}/immunizations`, data).then((r) => r.data),
  },
  summary: (patientId: number) =>
    api.get(`/ehr/${patientId}/summary`).then((r) => r.data),
  vitals: (patientId: number) =>
    api.get(`/ehr/${patientId}/vitals`).then((r) => r.data),
};

export const fhir = {
  read: (resourceType: string, id: string) =>
    api.get<FHIRResource>(`/fhir/${resourceType}/${id}`).then((r) => r.data),
  search: (resourceType: string, params?: any) =>
    api.get<FHIRResource[]>(`/fhir/${resourceType}`, { params }).then((r) => r.data),
  create: (resourceType: string, data: any) =>
    api.post<FHIRResource>(`/fhir/${resourceType}`, data).then((r) => r.data),
  update: (resourceType: string, id: string, data: any) =>
    api.put<FHIRResource>(`/fhir/${resourceType}/${id}`, data).then((r) => r.data),
  delete: (resourceType: string, id: string) =>
    api.delete(`/fhir/${resourceType}/${id}`).then((r) => r.data),
  patientEverything: (patientId: number) =>
    api.get(`/fhir/patient/${patientId}/everything`).then((r) => r.data),
  metadata: () => api.get('/fhir/metadata').then((r) => r.data),
};

export const ai = {
  suggest: (data: any) => api.post('/api/ai/suggest', data).then((r) => r.data),
  pending: () => api.get('/api/ai/pending').then((r) => r.data),
  approve: (id: number) => api.post(`/api/ai/approve/${id}`).then((r) => r.data),
  reject: (id: number, reason: string) => api.post(`/api/ai/reject/${id}`, { reason }).then((r) => r.data),
  execute: (id: number) => api.post(`/api/ai/execute/${id}`).then((r) => r.data),
  analyzeOrder: (orderId: number) => api.post(`/api/ai/analyze-order/${orderId}`).then((r) => r.data),
  operations: () => api.get('/api/ai/operations').then((r) => r.data),
  criticalAlerts: () => api.get('/api/ai/critical-alerts').then((r) => r.data),
  interpret: (token: string) => api.get(`/api/ai/interpret/${token}`).then((r) => r.data),
};

export const aiV2 = {
  search: (data: any) => api.post('/api/ai/v2/search', data).then((r) => r.data),
  rag: (data: any) => api.post('/api/ai/v2/rag', data).then((r) => r.data),
  executeAgent: (data: any) => api.post('/api/ai/v2/agent/execute', data).then((r) => r.data),
  orchestrate: (data: any) => api.post('/api/ai/v2/orchestrate', data).then((r) => r.data),
  cdsEvaluate: (data: any) => api.post('/api/ai/v2/cds/evaluate', data).then((r) => r.data),
};

export const patientCard = {
  get: (patientId: number) =>
    api.get<PatientCard>(`/patient-card/${patientId}`).then((r) => r.data),
  qr: (patientId: number) =>
    api.get(`/patient-card/${patientId}/qr.png`, { responseType: 'blob' }).then((r) => r.data),
  scan: (token: string) =>
    api.post('/patient-card/scan', { token }).then((r) => r.data),
  history: (patientId: number) =>
    api.get(`/patient-card/${patientId}/history`).then((r) => r.data),
  print: (patientId: number) =>
    api.get(`/patient-card/${patientId}/print`).then((r) => r.data),
};

export const identity = {
  linkNationalId: (patientId: number, nationalId: string) =>
    api.post('/identity/link', { patient_id: patientId, national_id: nationalId }).then((r) => r.data),
  verifyIdentity: (data: any) =>
    api.post('/identity/verify', data).then((r) => r.data),
  scanId: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/id-scan/scan', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r) => r.data);
  },
};

export const notifications = {
  send: (data: any) => api.post('/notify/send', data).then((r) => r.data),
  registerPush: (token: string) =>
    api.post('/auth/register/push', { token }).then((r) => r.data),
};

export const deviceResults = {
  receive: (data: any[]) =>
    api.post('/device/results', { results: data }).then((r) => r.data),
};

export const security = {
  status: () => api.get<SecurityStatus>('/security/status').then((r) => r.data),
};

export const compliance = {
  info: () => api.get('/compliance/info').then((r) => r.data),
  auditTrail: () => api.get('/compliance/audit-trail').then((r) => r.data),
  auditDetail: (anchorId: string) => api.get(`/compliance/audit-trail/${anchorId}`).then((r) => r.data),
  report: () => api.get('/compliance/report').then((r) => r.data),
};

export const tiers = {
  list: () => api.get('/tiers').then((r) => r.data),
  my: () => api.get<LabSubscription>('/tiers/my').then((r) => r.data),
  upgrade: (data: any) => api.post('/tiers/upgrade', data).then((r) => r.data),
  demand: (data: any) => api.post('/tiers/upgrade-demand', data).then((r) => r.data),
};

export const edge = {
  devices: {
    list: () => api.get<EdgeDevice[]>('/edge/devices').then((r) => r.data),
    get: (id: string) => api.get<EdgeDevice>(`/edge/devices/${id}`).then((r) => r.data),
    register: (data: any) => api.post('/edge/devices/register', data).then((r) => r.data),
    quarantine: (id: string) => api.post(`/edge/devices/${id}/quarantine`).then((r) => r.data),
    revoke: (id: string) => api.post(`/edge/devices/${id}/revoke`).then((r) => r.data),
    reinstate: (id: string) => api.post(`/edge/devices/${id}/reinstate`).then((r) => r.data),
  },
  tasks: {
    list: () => api.get<EdgeTask[]>('/edge/tasks').then((r) => r.data),
    get: (uid: string) => api.get<EdgeTask>(`/edge/tasks/${uid}`).then((r) => r.data),
    submit: (data: any) => api.post('/edge/tasks', data).then((r) => r.data),
    cancel: (uid: string) => api.post(`/edge/tasks/${uid}/cancel`).then((r) => r.data),
  },
  policy: {
    get: () => api.get('/edge/policy').then((r) => r.data),
    update: (data: any) => api.put('/edge/policy', data).then((r) => r.data),
  },
  fleet: {
    summary: () => api.get('/edge/fleet/summary').then((r) => r.data),
  },
};

export const claims = {
  create: (data: any) => api.post<Claim>('/claims', data).then((r) => r.data),
  get: (id: number) => api.get<Claim>(`/claims/${id}`).then((r) => r.data),
  validate: (id: number) => api.post(`/claims/${id}/validate`).then((r) => r.data),
  submit: (id: number) => api.post(`/claims/${id}/submit`).then((r) => r.data),
};

export const hospital = {
  list: (opts?: RequestOptions) =>
    api.get(`/hospital${buildQueryString(opts || {})}`).then((r) => r.data),
  departments: (hospitalId: number) =>
    api.get(`/hospital/${hospitalId}/departments`).then((r) => r.data),
  beds: (departmentId: number) =>
    api.get(`/hospital/departments/${departmentId}/beds`).then((r) => r.data),
};

export const clinical = {
  orders: {
    list: (opts?: RequestOptions) =>
      api.get<ClinicalOrder[]>(`/clinical/orders${buildQueryString(opts || {})}`).then((r) => r.data),
    create: (data: any) => api.post('/clinical/orders', data).then((r) => r.data),
    get: (id: number) => api.get(`/clinical/orders/${id}`).then((r) => r.data),
    cancel: (id: number) => api.post(`/clinical/orders/${id}/cancel`).then((r) => r.data),
    complete: (id: number) => api.post(`/clinical/orders/${id}/complete`).then((r) => r.data),
    hold: (id: number) => api.post(`/clinical/orders/${id}/hold`).then((r) => r.data),
    resume: (id: number) => api.post(`/clinical/orders/${id}/resume`).then((r) => r.data),
  },
  documentation: {
    list: (opts?: RequestOptions) =>
      api.get(`/clinical/documentation${buildQueryString(opts || {})}`).then((r) => r.data),
    create: (data: any) => api.post('/clinical/documentation', data).then((r) => r.data),
  },
  quality: {
    kpis: (department?: string) =>
      api.get(`/clinical/quality/kpis${department ? `?department=${department}` : ''}`).then((r) => r.data),
    measurements: (opts?: RequestOptions) =>
      api.get(`/clinical/quality/measurements${buildQueryString(opts || {})}`).then((r) => r.data),
    indicators: () => api.get('/clinical/quality/indicators').then((r) => r.data),
  },
};

export const consent = {
  grant: (data: any) => api.post<ConsentRecord>('/consent/grant', data).then((r) => r.data),
  revoke: (data: any) => api.post('/consent/revoke', data).then((r) => r.data),
  check: (scope: string) => api.get(`/consent/check?scope=${scope}`).then((r) => r.data),
  active: () => api.get<ConsentRecord[]>('/consent/active').then((r) => r.data),
};

export const wellbeing = {
  appointments: {
    list: (opts?: RequestOptions) =>
      api.get(`/care-continuum/primary-care/encounters${buildQueryString(opts || {})}`).then((r) => r.data),
  },
  referrals: {
    list: () => api.get('/care-continuum/referrals').then((r) => r.data),
    create: (data: any) => api.post('/care-continuum/referrals', data).then((r) => r.data),
    accept: (id: number) => api.post(`/care-continuum/referrals/${id}/accept`).then((r) => r.data),
    complete: (id: number) => api.post(`/care-continuum/referrals/${id}/complete`).then((r) => r.data),
  },
};

export const integration = {
  status: () => api.get<IntegrationStatus[]>('/integrations/status').then((r) => r.data),
  probe: (name: string) => api.post(`/integrations/${name}/probe`).then((r) => r.data),
};

export const serviceAccounts = {
  list: () => api.get('/service-accounts').then((r) => r.data),
  create: (data: any) => api.post('/service-accounts', data).then((r) => r.data),
  revoke: (id: number) => api.delete(`/service-accounts/${id}`).then((r) => r.data),
  rotate: (id: number) => api.post(`/service-accounts/${id}/rotate`).then((r) => r.data),
};
