import axios, { AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from "axios";
import { isDemoSessionActive } from "@/demo/session";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export class DemoModeBlockedError extends Error {
  constructor() {
    super("Demo mode is read-only: API access is disabled");
    this.name = "DemoModeBlockedError";
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

    this.instance.interceptors.request.use(this.handleRequest.bind(this));
    this.instance.interceptors.response.use(
      (res) => res,
      this.handleError.bind(this),
    );
  }

  private handleRequest(config: InternalAxiosRequestConfig) {
    if (isDemoSessionActive()) {
      return Promise.reject(new DemoModeBlockedError());
    }
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  }

  private async handleError(error: AxiosError) {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshed = await this.refreshToken();
        if (refreshed) {
          const token = localStorage.getItem("access_token");
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return this.instance(originalRequest);
        }
      } catch {
        this.clearTokens();
        window.location.href = "/login";
      }
    }

    return Promise.reject(error);
  }

  private async refreshToken(): Promise<boolean> {
    if (this.refreshPromise) return this.refreshPromise;

    this.refreshPromise = new Promise<boolean>((resolve) => {
      const refreshToken = localStorage.getItem("refresh_token");
      if (!refreshToken) {
        resolve(false);
        return;
      }

      axios
        .post<{ token: string; refresh_token: string }>(
          `${API_BASE_URL}/auth/refresh`,
          { refresh_token: refreshToken },
        )
        .then((res) => {
          localStorage.setItem("access_token", res.data.token);
          localStorage.setItem("refresh_token", res.data.refresh_token);
          resolve(true);
        })
        .catch(() => {
          resolve(false);
        });
    }).finally(() => {
      this.refreshPromise = null;
    });

    return this.refreshPromise;
  }

  private clearTokens() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  }

  get api(): AxiosInstance {
    return this.instance;
  }
}

export const apiClient = new ApiClient();
export const api = apiClient.api;
