import axios, {
  type AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

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
  if (!IDENTITY_AND_DECISION_ALLOWLIST.has(key)) {
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
  if (!INITIALIZATION_READ_ALLOWLIST.has(key)) {
    throw new OperationalReadBlockedError(normalizedMethod.toUpperCase(), url ?? "/");
  }
}

class ApiClient {
  private instance: AxiosInstance;
  private refreshPromise: Promise<boolean> | null = null;

  constructor() {
    this.instance = axios.create({
      baseURL: API_BASE_URL,
      headers: { "Content-Type": "application/json" },
      withCredentials: true,
      timeout: 30000,
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
    if (refreshed) {
      return this.instance(originalRequest);
    }

    this.clearSession();
    if (window.location.pathname !== "/login") {
      window.location.assign("/login");
    }
    return Promise.reject(error);
  }

  private async refreshToken(): Promise<boolean> {
    if (this.refreshPromise) return this.refreshPromise;

    this.refreshPromise = axios
      .post(`${API_BASE_URL}/auth/refresh`, {}, { withCredentials: true })
      .then(() => true)
      .catch(() => false)
      .finally(() => {
        this.refreshPromise = null;
      });

    return this.refreshPromise;
  }

  private clearSession() {
    // Tokens are HttpOnly cookies and are never readable by JavaScript.
    window.dispatchEvent(new CustomEvent("gula:session-expired"));
  }

  get api(): AxiosInstance {
    return this.instance;
  }
}

export const apiClient = new ApiClient();
export const api = apiClient.api;
