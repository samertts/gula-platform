import axios, {
  type AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios";

const LIVE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";
// Demo is deliberately same-origin so a stale deployment variable cannot
// redirect a public visitor to an unprovisioned or production API host.
const DEMO_API_BASE_URL = "/demo-api";
const API_MODE_STORAGE_KEY = "gula.api-mode";

export type DemoPersonaId = "doctor" | "technician" | "lab_admin" | "citizen";

export interface WorkspaceSummary {
  id: string;
  uuid: string;
  workspace_type: string;
  name: string;
  name_ar?: string | null;
  status: string;
  organization_id?: string | null;
  facility_id?: string | null;
  department_id?: string | null;
  professional_type?: string | null;
  is_personal: boolean;
}

export interface WorkspaceContextResponse {
  context: { account_id: string; identity_id: string; workspace_id: string; version: number };
  workspace: WorkspaceSummary;
}

export interface MembershipSummary {
  id: string;
  uuid: string;
  account_id: string;
  identity_id?: string | null;
  organization_id: string;
  facility_id?: string | null;
  department_id?: string | null;
  unit_id?: string | null;
  workspace_id?: string | null;
  relationship_type: string;
  scope_type: string;
  status: string;
  source: string;
  expires_at?: string | null;
  version: number;
  is_active: boolean;
}

export interface MembershipApplicationRequest {
  organization_id: string;
  relationship_type: string;
  scope_type: string;
  identity_id?: string;
  facility_id?: string;
  department_id?: string;
  unit_id?: string;
  workspace_id?: string;
}

export interface MembershipInvitationRequest extends Omit<MembershipApplicationRequest, "identity_id"> {
  recipient_account_id?: string;
  ttl_hours?: number;
}

export interface RoleSummary {
  id: string;
  uuid: string;
  role_key: string;
  name: string;
  name_ar?: string | null;
  scope_type: string;
  status: string;
  is_system: boolean;
  version: number;
}

export interface PermissionSummary {
  id: string;
  uuid: string;
  permission_key: string;
  name: string;
  name_ar?: string | null;
  resource: string;
  action: string;
  sensitivity: string;
  status: string;
  version: number;
}

export interface EffectivePermissionsResponse {
  organization_id: string;
  permissions: string[];
}

export interface RoleAssignmentRequest {
  account_id: string;
  membership_id: string;
  role_id: string;
  facility_id?: string;
  department_id?: string;
  unit_id?: string;
  workspace_id?: string;
}

export type AccountRequestStatus =
  | "pending_review"
  | "under_review"
  | "pending_verification"
  | "verified"
  | "pending_approval"
  | "approved"
  | "rejected"
  | "expired"
  | "cancelled";

export interface AccountRequestCreatePayload {
  email?: string;
  phone?: string;
  display_name?: string;
  requested_account_type?: "human";
}

export interface AccountRequestAccepted {
  accepted: boolean;
  status: string;
  request_id: string | null;
  message: string;
}

export interface AccountRequestSummary {
  request_id: string;
  status: AccountRequestStatus;
  requested_account_type: string;
  account_id?: string | null;
  reviewed_at?: string | null;
  verified_at?: string | null;
  expires_at?: string | null;
  is_active: boolean;
}

export interface AccountSummary {
  account_id: string;
  account_uuid: string;
  identity_id?: string | null;
  status: string;
  is_active: boolean;
  is_locked: boolean;
  suspended_until?: string | null;
  email_verified: boolean;
  phone_verified: boolean;
  identity_verified: boolean;
  activated_at?: string | null;
}

export interface AccountRequestApprovalResponse {
  request: AccountRequestSummary;
  account: AccountSummary;
}

export interface MembershipInvitationResponse {
  id: string;
  uuid: string;
  organization_id: string;
  facility_id?: string | null;
  department_id?: string | null;
  unit_id?: string | null;
  workspace_id?: string | null;
  relationship_type: string;
  scope_type: string;
  status: string;
  recipient_account_id?: string | null;
  expires_at: string;
  version: number;
  token?: string;
}

export interface DemoPersona {
  id: DemoPersonaId;
  role: string;
  name: string;
  nameAr: string;
  descriptionAr: string;
  descriptionEn: string;
  email: string;
}

export const DEMO_PERSONAS: DemoPersona[] = [
  {
    id: "doctor",
    role: "doctor",
    name: "Demo Doctor",
    nameAr: "طبيب تجريبي",
    descriptionAr: "استعراض المرضى والطلبات والنتائج الاصطناعية للقراءة.",
    descriptionEn: "Read-only view of synthetic patients, orders, and results.",
    email: "demo.doctor@gula-demo.invalid",
  },
  {
    id: "technician",
    role: "technician",
    name: "Demo Lab Technician",
    nameAr: "فني مختبر تجريبي",
    descriptionAr: "استعراض سير العمل المختبري والعينات والنتائج الاصطناعية.",
    descriptionEn: "Synthetic laboratory workflow, samples, and results.",
    email: "demo.technician@gula-demo.invalid",
  },
  {
    id: "lab_admin",
    role: "lab_admin",
    name: "Demo Lab Administrator",
    nameAr: "مدير مختبر تجريبي",
    descriptionAr: "استعراض لوحة المختبر والموظفين والتقارير دون عمليات كتابة.",
    descriptionEn: "Read-only laboratory dashboard, staff, and reports.",
    email: "demo.lab-admin@gula-demo.invalid",
  },
  {
    id: "citizen",
    role: "citizen",
    name: "Demo Citizen",
    nameAr: "مواطن تجريبي",
    descriptionAr: "استعراض مساحة المواطن ببيانات اصطناعية معزولة.",
    descriptionEn: "Explore the citizen workspace with isolated synthetic data.",
    email: "demo.citizen@gula-demo.invalid",
  },
];

function syntheticDemoUser(persona: DemoPersona) {
  return {
    id: `demo-${persona.id}`,
    name: persona.nameAr,
    email: persona.email,
    role: persona.role,
    lab_id: "demo-tenant",
    lab_name: "GULA Synthetic Demo",
    is_verified: true,
  };
}

const SYNTHETIC_DEMO_DASHBOARDS: Record<DemoPersonaId, Record<string, unknown>> = {
  doctor: { total_patients: 24, today_orders: 11, today_results: 17, critical_alerts: 2 },
  technician: { total_patients: 12, today_orders: 18, today_results: 26, critical_alerts: 1 },
  lab_admin: { total_patients: 48, today_orders: 32, today_results: 39, critical_alerts: 4 },
  citizen: { total_patients: 1, today_orders: 2, today_results: 2, critical_alerts: 0 },
};

function syntheticDemoDashboard(personaId: DemoPersonaId = "doctor") {
  return {
    demo_mode: true,
    ...(SYNTHETIC_DEMO_DASHBOARDS[personaId] ?? SYNTHETIC_DEMO_DASHBOARDS.doctor),
    synthetic_notice: "All values are generated for demonstration and training only.",
    synthetic_notice_ar: "جميع القيم مولدة للعرض والتدريب فقط.",
  };
}

export type ApiMode = "live" | "demo";
type RetryableRequest = InternalAxiosRequestConfig & { _retry?: boolean };
type RestWriteMethod = "post" | "put" | "patch" | "delete";

const IDENTITY_AND_DECISION_ALLOWLIST = new Set([
  "POST /login",
  "POST /logout",
  "POST /demo/access",
  "POST /auth/verification/request",
  "POST /auth/verification/confirm",
  "POST /auth/forgot-password",
  "POST /auth/reset-password",
  "POST /auth/change-password",
  "POST /register/citizen",
  "POST /authz/check",
  "POST /consent/check",
]);

const INITIALIZATION_READ_ALLOWLIST = new Set([
  "GET /session",
  "GET /setup/status",
  "GET /greeting",
  "GET /niam/workspaces",
  "GET /niam/memberships/me",
  "GET /niam/roles",
  "GET /niam/roles/permissions",
  "GET /niam/roles/effective",
  "GET /api/v1/clinical/patients",
  "GET /api/v1/clinical/orders",
]);

export class OperationalWriteBlockedError extends Error {
  constructor(
    public readonly method: string,
    public readonly url: string,
  ) {
    super("أُوقفت العملية لأن عقد الكتابة وتفويضها وأثرها التشغيلي لم تُعتمد بعد.");
    this.name = "OperationalWriteBlockedError";
  }
}

export class OperationalReadBlockedError extends Error {
  constructor(
    public readonly method: string,
    public readonly url: string,
  ) {
    super("أُوقفت القراءة لأن مصدر البيانات غير مصنف بعقد خادمي مفروض أو جسر آمن.");
    this.name = "OperationalReadBlockedError";
  }
}

const BILLING_READ_PATTERN = /^GET \/billing\/(summary|invoices(?:\/\d+)?|claims|coverages|payments|alerts)$/;
const FINANCIAL_CONTROL_READ_PATTERN = /^GET \/payments\/controls\/(summary|requests)$/;
const DEVICE_INTEGRATION_READ_PATTERN = /^GET \/device-integration\/(protocols|summary|devices(?:\/[^/]+)?|connectors|protocol-profiles|simulators|events|printer-jobs|monitoring|monitoring\/alerts)$/;
const BILLING_WRITE_PATTERN = /^POST \/billing\/(invoices|coverages|claims\/\d+\/advance|coverages\/\d+\/verify-local|invoices\/\d+\/simulate-settlement)$/;
const DEVICE_INTEGRATION_WRITE_PATTERN = /^POST \/device-integration\/(devices|devices\/[^/]+\/(status|probe)|connectors|connectors\/[^/]+\/(status|simulate)|protocol-profiles|printer-jobs|monitoring\/metrics|monitoring\/alerts\/\d+\/acknowledge)$/;
const ACCOUNT_REQUEST_READ_PATTERN = /^GET \/niam\/account-requests\/?$/;
const ACCOUNT_REQUEST_WRITE_PATTERN = /^POST \/niam\/account-requests\/(?:[^/]+\/(review|approve|activation-token|reject|expire)|accounts\/[^/]+\/(suspend|lock|reactivate|deactivate))$/;
const ACCOUNT_REQUEST_CREATE_PATTERN = /^POST \/niam\/account-requests\/?$/;
const ACCOUNT_REQUEST_PUBLIC_WRITE_PATTERN = /^POST \/niam\/account-requests\/[^/]+\/(verification\/start|verification\/confirm|activate)$/;

function toRequestKey(method?: string, url?: string): string {
  const normalizedMethod = (method ?? "get").toUpperCase();
  const normalizedUrl = (url ?? "").split("?")[0] || "/";
  return `${normalizedMethod} ${normalizedUrl.startsWith("/") ? normalizedUrl : `/${normalizedUrl}`}`;
}

/**
 * يمنع العميل نفسه أي كتابة تشغيلية غير مشمولة بعقد مفوض ومراجع. الاستثناءات
 * ضيقة ومحصورة في المصادقة والتحقق وقرارات القراءة؛ ولا تشمل كتابة بيانات سريرية
 * أو إدارية أو أجهزة أو إشعارات ذات أثر خارجي؛ مسارات الأجهزة المسموحة هنا
 * محصورة في كتالوج المحاكاة وprobe ووظائف الطباعة والتنبيهات الاصطناعية المعلنة.
 */
export function assertFrontendWriteIsAllowed(method?: string, url?: string): void {
  const normalizedMethod = (method ?? "get").toLowerCase();
  if (!( ["post", "put", "patch", "delete"] as RestWriteMethod[]).includes(normalizedMethod as RestWriteMethod)) {
    return;
  }

  const key = toRequestKey(normalizedMethod, url);
  const workspaceSwitch = normalizedMethod === "post" && /^POST \/niam\/workspaces\/[^/]+\/switch$/.test(key);
  const membershipMutation = normalizedMethod === "post" && /^POST \/niam\/memberships\/(?:applications(?:\/[^/]+\/approve)?|invitations(?:\/[^/]+\/(?:accept|revoke))?|[^/]+\/(?:revoke|suspend|reactivate))$/.test(key);
  const accountRequestMutation = ACCOUNT_REQUEST_CREATE_PATTERN.test(key) || ACCOUNT_REQUEST_WRITE_PATTERN.test(key) || ACCOUNT_REQUEST_PUBLIC_WRITE_PATTERN.test(key);
  if (!IDENTITY_AND_DECISION_ALLOWLIST.has(key) && !workspaceSwitch && !membershipMutation && !accountRequestMutation && (BILLING_WRITE_PATTERN.test(key) || DEVICE_INTEGRATION_WRITE_PATTERN.test(key))) {
    return;
  }
  if (!IDENTITY_AND_DECISION_ALLOWLIST.has(key) && !workspaceSwitch && !membershipMutation && !accountRequestMutation) {
    throw new OperationalWriteBlockedError(normalizedMethod.toUpperCase(), url ?? "/");
  }
}

/**
 * ترفض القراءات المباشرة كذلك؛ فلا يصح أن يعالج الحاجز الكتابات فقط بينما يبقى
 * `GET` مباشرًا قادرًا على عرض سجل سريري أو مختبري. الاستثناءات هي تهيئة جلسة
 * وهوية أولية ضيقة لا تمنح عرض مورد تشغيلي.
 */
export function assertFrontendReadIsAllowed(method?: string, url?: string): void {
  const normalizedMethod = (method ?? "get").toLowerCase();
  if (normalizedMethod !== "get") return;

  const key = toRequestKey(normalizedMethod, url);
  const workspaceDetail = /^GET \/niam\/workspaces\/[^/]+$/.test(key);
  if (BILLING_READ_PATTERN.test(key) || FINANCIAL_CONTROL_READ_PATTERN.test(key) || DEVICE_INTEGRATION_READ_PATTERN.test(key) || ACCOUNT_REQUEST_READ_PATTERN.test(key)) return;
  if (!INITIALIZATION_READ_ALLOWLIST.has(key) && !workspaceDetail) {
    throw new OperationalReadBlockedError(normalizedMethod.toUpperCase(), url ?? "/");
  }
}

function initialMode(): ApiMode {
  if (typeof window === "undefined") return "live";
  return window.sessionStorage.getItem(API_MODE_STORAGE_KEY) === "demo" && DEMO_API_BASE_URL ? "demo" : "live";
}

function baseUrlFor(mode: ApiMode): string {
  return mode === "demo" && DEMO_API_BASE_URL ? DEMO_API_BASE_URL : LIVE_API_BASE_URL;
}

class ApiClient {
  private instance: AxiosInstance;
  private refreshPromise: Promise<boolean> | null = null;
  private mode: ApiMode;

  constructor() {
    this.mode = initialMode();
    this.instance = axios.create({
      baseURL: baseUrlFor(this.mode),
      headers: { "Content-Type": "application/json" },
      withCredentials: true,
      timeout: 30_000,
    });

    this.instance.interceptors.request.use((config) => {
      assertFrontendReadIsAllowed(config.method, config.url);
      assertFrontendWriteIsAllowed(config.method, config.url);
      return config;
    });

    this.instance.interceptors.response.use(
      (res) => res,
      this.handleError.bind(this),
    );
  }

  setMode(mode: ApiMode) {
    if (mode === "demo" && !DEMO_API_BASE_URL) {
      throw new Error("DEMO_API_NOT_CONFIGURED");
    }
    this.mode = mode;
    this.instance.defaults.baseURL = baseUrlFor(mode);
    if (typeof window !== "undefined") {
      window.sessionStorage.setItem(API_MODE_STORAGE_KEY, mode);
    }
  }

  async startDemoSession<T>(personaId: DemoPersonaId = "doctor") {
    // Public Demo is intentionally frontend-local: it cannot reach the live API,
    // and all values are synthetic constants. The optional Vercel function remains
    // available for deployments that need a server-side HttpOnly demo session.
    this.setMode("demo");
    const persona = DEMO_PERSONAS.find((candidate) => candidate.id === personaId) ?? DEMO_PERSONAS[0]!;
    return {
      demo_mode: true,
      demo_persona: persona.id,
      user: syntheticDemoUser(persona),
    } as T;
  }

  async listWorkspaces() {
    const response = await this.instance.get<{ workspaces: WorkspaceSummary[] }>("/niam/workspaces");
    return response.data;
  }

  async switchWorkspace(workspaceId: string) {
    const response = await this.instance.post<WorkspaceContextResponse>(`/niam/workspaces/${encodeURIComponent(workspaceId)}/switch`, {});
    return response.data;
  }

  async listMyMemberships() {
    const response = await this.instance.get<{ memberships: MembershipSummary[] }>("/niam/memberships/me");
    return response.data;
  }

  async submitMembershipApplication(body: MembershipApplicationRequest) {
    const response = await this.instance.post("/niam/memberships/applications", body);
    return response.data;
  }

  async approveMembershipApplication(applicationId: string) {
    const response = await this.instance.post(`/niam/memberships/applications/${encodeURIComponent(applicationId)}/approve`, {});
    return response.data as MembershipSummary;
  }

  async createMembershipInvitation(body: MembershipInvitationRequest) {
    const response = await this.instance.post<MembershipInvitationResponse>("/niam/memberships/invitations", body);
    return response.data;
  }

  async acceptMembershipInvitation(invitationId: string, token: string) {
    const response = await this.instance.post<MembershipSummary>(`/niam/memberships/invitations/${encodeURIComponent(invitationId)}/accept`, { token });
    return response.data;
  }

  async revokeMembershipInvitation(invitationId: string) {
    const response = await this.instance.post(`/niam/memberships/invitations/${encodeURIComponent(invitationId)}/revoke`, {});
    return response.data;
  }

  async changeMembershipState(membershipId: string, action: "revoke" | "suspend" | "reactivate", reason?: string) {
    const response = await this.instance.post<MembershipSummary>(`/niam/memberships/${encodeURIComponent(membershipId)}/${action}`, reason ? { reason } : {});
    return response.data;
  }

  async submitAccountRequest(body: AccountRequestCreatePayload, idempotencyKey: string) {
    const response = await this.instance.post<AccountRequestAccepted>("/niam/account-requests/", body, {
      headers: { "Idempotency-Key": idempotencyKey },
    });
    return response.data;
  }

  async listAccountRequests(status?: AccountRequestStatus) {
    const response = await this.instance.get<{ requests: AccountRequestSummary[] }>("/niam/account-requests/", {
      params: status ? { request_status: status } : undefined,
    });
    return response.data;
  }

  async reviewAccountRequest(requestId: string) {
    const response = await this.instance.post<AccountRequestSummary>(`/niam/account-requests/${encodeURIComponent(requestId)}/review`, {});
    return response.data;
  }

  async approveAccountRequest(requestId: string) {
    const response = await this.instance.post<AccountRequestApprovalResponse>(`/niam/account-requests/${encodeURIComponent(requestId)}/approve`, {});
    return response.data;
  }

  async rejectAccountRequest(requestId: string, reason_code: string) {
    const response = await this.instance.post<AccountRequestSummary>(`/niam/account-requests/${encodeURIComponent(requestId)}/reject`, { reason_code });
    return response.data;
  }

  async expireAccountRequest(requestId: string) {
    const response = await this.instance.post<AccountRequestSummary>(`/niam/account-requests/${encodeURIComponent(requestId)}/expire`, {});
    return response.data;
  }

  async issueAccountActivationToken(requestId: string) {
    const response = await this.instance.post<{ accepted: boolean; message: string }>(`/niam/account-requests/${encodeURIComponent(requestId)}/activation-token`, {});
    return response.data;
  }

  async mutateAccount(accountUuid: string, action: "suspend" | "lock" | "reactivate" | "deactivate", reason_code: string) {
    const response = await this.instance.post<AccountSummary>(`/niam/account-requests/accounts/${encodeURIComponent(accountUuid)}/${action}`, { reason_code });
    return response.data;
  }

  async startAccountRequestVerification(requestId: string) {
    const response = await this.instance.post<{ accepted: boolean; status: string; message: string }>(`/niam/account-requests/${encodeURIComponent(requestId)}/verification/start`, {});
    return response.data;
  }

  async confirmAccountRequestVerification(requestId: string, code: string) {
    const response = await this.instance.post<{ status: string; message: string }>(`/niam/account-requests/${encodeURIComponent(requestId)}/verification/confirm`, { code });
    return response.data;
  }

  async activateAccountRequest(requestId: string, token: string, password: string) {
    const response = await this.instance.post<AccountSummary>(`/niam/account-requests/${encodeURIComponent(requestId)}/activate`, { token, password });
    return response.data;
  }

  async listRoles() {
    const response = await this.instance.get<{ roles: RoleSummary[] }>("/niam/roles");
    return response.data;
  }

  async listPermissions() {
    const response = await this.instance.get<{ permissions: PermissionSummary[] }>("/niam/roles/permissions");
    return response.data;
  }

  async getEffectivePermissions(organizationId: string, context: Omit<RoleAssignmentRequest, "account_id" | "membership_id" | "role_id"> = {}) {
    const response = await this.instance.get<EffectivePermissionsResponse>("/niam/roles/effective", {
      params: { organization_id: organizationId, ...context },
    });
    return response.data;
  }

  async assignRole(body: RoleAssignmentRequest) {
    const response = await this.instance.post("/niam/roles/assignments", body);
    return response.data;
  }

  async revokeRoleAssignment(assignmentId: string, reason?: string) {
    const response = await this.instance.post(`/niam/roles/assignments/${encodeURIComponent(assignmentId)}/revoke`, reason ? { reason } : {});
    return response.data;
  }

  async demoDashboard<T>(personaId: DemoPersonaId = "doctor") {
    if (this.mode !== "demo") this.setMode("demo");
    return syntheticDemoDashboard(personaId) as T;
  }

  private async handleError(error: AxiosError) {
    const originalRequest = error.config as RetryableRequest | undefined;
    const requestUrl = originalRequest?.url ?? "";

    if (
      !originalRequest ||
      error.response?.status !== 401 ||
      originalRequest._retry ||
      requestUrl.includes("/auth/refresh")
    ) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;
    const refreshed = await this.refreshToken();
    if (refreshed) return this.instance(originalRequest);

    this.clearSession();
    if (window.location.pathname !== "/login") window.location.assign("/login");
    return Promise.reject(error);
  }

  private async refreshToken(): Promise<boolean> {
    if (this.refreshPromise) return this.refreshPromise;

    this.refreshPromise = this.instance
      .post("/auth/refresh", {})
      .then(() => true)
      .catch(() => false)
      .finally(() => { this.refreshPromise = null; });

    return this.refreshPromise;
  }

  private clearSession() {
    window.dispatchEvent(new CustomEvent("gula:session-expired"));
  }

  get api(): AxiosInstance {
    return this.instance;
  }

  get currentMode(): ApiMode {
    return this.mode;
  }

  get isDemoConfigured(): boolean {
    return true;
  }
}

export const apiClient = new ApiClient();
export const api = apiClient.api;
export const setApiMode = (mode: ApiMode) => apiClient.setMode(mode);
export const demoApiConfigured = () => apiClient.isDemoConfigured;
