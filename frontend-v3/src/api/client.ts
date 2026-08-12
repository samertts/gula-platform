import axios, {
  type AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

type RetryableRequest = InternalAxiosRequestConfig & { _retry?: boolean };

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
