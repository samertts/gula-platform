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

function toRequestKey(method?: string, url?: string): string {
  const normalizedMethod = (method ?? "get").toUpperCase();
  const normalizedUrl = (url ?? "").split("?")[0] || "/";
  return `${normalizedMethod} ${normalizedUrl.startsWith("/") ? normalizedUrl : `/${normalizedUrl}`}`;
}

/**
 * يمنع العميل نفسه أي كتابة تشغيلية غير مشمولة بعقد مفوض ومراجع. الاستثناءات
 * ضيقة ومحصورة في المصادقة والتحقق وقرارات القراءة؛ ولا تشمل كتابة بيانات سريرية
 * أو إدارية أو أجهزة أو إشعارات ذات أثر خارجي.
 */
export function assertFrontendWriteIsAllowed(method?: string, url?: string): void {
  const normalizedMethod = (method ?? "get").toLowerCase();
  if (!( ["post", "put", "patch", "delete"] as RestWriteMethod[]).includes(normalizedMethod as RestWriteMethod)) {
    return;
  }

  const key = toRequestKey(normalizedMethod, url);
  const workspaceSwitch = normalizedMethod === "post" && /^POST \/niam\/workspaces\/[^/]+\/switch$/.test(key);
  if (!IDENTITY_AND_DECISION_ALLOWLIST.has(key) && !workspaceSwitch) {
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
