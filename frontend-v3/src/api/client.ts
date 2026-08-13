import axios, {
  type AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios";

const LIVE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";
const DEMO_API_BASE_URL = import.meta.env.VITE_DEMO_API_BASE_URL?.replace(/\/$/, "") ?? "";
const API_MODE_STORAGE_KEY = "gula.api-mode";

export type ApiMode = "live" | "demo";
type RetryableRequest = InternalAxiosRequestConfig & { _retry?: boolean };

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

  async startDemoSession<T>() {
    if (!DEMO_API_BASE_URL) {
      throw new Error("DEMO_API_NOT_CONFIGURED");
    }
    const response = await axios.post<T>(
      `${DEMO_API_BASE_URL}/demo/access`,
      {},
      { headers: { "Content-Type": "application/json" }, withCredentials: true, timeout: 30_000 },
    );
    this.setMode("demo");
    return response.data;
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
    return Boolean(DEMO_API_BASE_URL);
  }
}

export const apiClient = new ApiClient();
export const api = apiClient.api;
export const setApiMode = (mode: ApiMode) => apiClient.setMode(mode);
export const demoApiConfigured = () => apiClient.isDemoConfigured;
