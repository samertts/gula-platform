import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from 'axios';
import { errorFromStatus, GulaError } from './errors';

export interface GulaClientConfig {
  baseURL: string;
  accessToken?: string;
  refreshToken?: string;
  timeout?: number;
  maxRetries?: number;
  enableLogging?: boolean;
  onTokenRefresh?: () => Promise<string | null>;
  idempotencyKeyProvider?: () => string | undefined;
}

const DEFAULT_TIMEOUT = 30_000;
const DEFAULT_MAX_RETRIES = 3;

const METHODS_WITH_IDEMPOTENCY = ['POST', 'PUT', 'PATCH', 'DELETE'];

export class GulaClient {
  private readonly http: AxiosInstance;
  private accessToken?: string;
  private readonly maxRetries: number;
  private readonly enableLogging: boolean;
  private readonly onTokenRefresh?: () => Promise<string | null>;
  private readonly idempotencyKeyProvider?: () => string | undefined;

  constructor(config: GulaClientConfig) {
    this.accessToken = config.accessToken;
    this.maxRetries = config.maxRetries ?? DEFAULT_MAX_RETRIES;
    this.enableLogging = config.enableLogging ?? false;
    this.onTokenRefresh = config.onTokenRefresh;
    this.idempotencyKeyProvider = config.idempotencyKeyProvider;

    let normalizedBaseURL = config.baseURL;
    while (normalizedBaseURL.endsWith('/')) {
      normalizedBaseURL = normalizedBaseURL.slice(0, -1);
    }
    this.http = axios.create({
      baseURL: normalizedBaseURL,
      timeout: config.timeout ?? DEFAULT_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
    });

    this.http.interceptors.request.use(
      (cfg: InternalAxiosRequestConfig) => {
        if (this.accessToken && cfg.headers) {
          cfg.headers.Authorization = `Bearer ${this.accessToken}`;
        }
        if (cfg.headers) {
          const method = (cfg.method ?? 'get').toUpperCase();
          if (METHODS_WITH_IDEMPOTENCY.includes(method)) {
            const key = this.idempotencyKeyProvider?.();
            if (key) {
              cfg.headers['Idempotency-Key'] = key;
            }
          }
        }
        if (this.enableLogging) {
          console.log(`[GULA] → ${cfg.method?.toUpperCase()} ${cfg.url}`);
        }
        return cfg;
      },
      (error) => Promise.reject(error),
    );

    this.http.interceptors.response.use(
      (response: AxiosResponse) => {
        if (this.enableLogging) {
          console.log(
            `[GULA] ← ${response.status} ${response.config.url} (${response.config.method?.toUpperCase()})`,
          );
        }
        return response;
      },
      async (error) => {
        const original = error.config as InternalAxiosRequestConfig & {
          _retryCount?: number;
          _retry?: boolean;
        };

        if (!original) {
          return Promise.reject(errorFromStatus(0, {}));
        }

        const status = error.response?.status;

        if (status === 401 && !original._retry && this.onTokenRefresh) {
          original._retry = true;
          try {
            const newToken = await this.onTokenRefresh();
            if (newToken) {
              this.accessToken = newToken;
              original.headers.Authorization = `Bearer ${newToken}`;
              return this.http(original);
            }
          } catch {
          }
        }

        const retryCount = original._retryCount ?? 0;
        if (
          retryCount < this.maxRetries &&
          (status === 429 || status === 500 || status === 502 || status === 503 || !status)
        ) {
          original._retryCount = retryCount + 1;
          const delay = Math.min(1000 * Math.pow(2, retryCount), 10_000);
          if (this.enableLogging) {
            console.log(
              `[GULA] ⟳ retry ${retryCount + 1}/${this.maxRetries} after ${delay}ms (${status ?? 'network'})`,
            );
          }
          await new Promise((r) => setTimeout(r, delay));
          return this.http(original);
        }

        if (error.response) {
          throw errorFromStatus(status, error.response.data);
        }
        if (error.code === 'ECONNABORTED') {
          throw new GulaError('Request timeout', 408, 'TIMEOUT');
        }
        throw new GulaError(error.message || 'Network error', 0, 'NETWORK_ERROR');
      },
    );
  }

  setAccessToken(token: string): void {
    this.accessToken = token;
  }

  setRefreshToken(_token: string): void {
  }

  clearTokens(): void {
    this.accessToken = undefined;
  }

  async request<T>(config: AxiosRequestConfig): Promise<T> {
    const response = await this.http.request<T>(config);
    return response.data;
  }

  async get<T>(url: string, params?: Record<string, unknown>): Promise<T> {
    return this.request<T>({ method: 'GET', url, params });
  }

  async post<T>(url: string, data?: unknown): Promise<T> {
    return this.request<T>({ method: 'POST', url, data });
  }

  async put<T>(url: string, data?: unknown): Promise<T> {
    return this.request<T>({ method: 'PUT', url, data });
  }

  async patch<T>(url: string, data?: unknown): Promise<T> {
    return this.request<T>({ method: 'PATCH', url, data });
  }

  async delete<T>(url: string): Promise<T> {
    return this.request<T>({ method: 'DELETE', url });
  }

  async upload<T>(url: string, formData: FormData): Promise<T> {
    return this.request<T>({
      method: 'POST',
      url,
      data: formData,
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  }

  async download(url: string, filename?: string): Promise<Blob> {
    const response = await this.http.get(url, { responseType: 'blob' });
    const blob = response.data as Blob;
    if (filename && typeof window !== 'undefined') {
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = filename;
      link.click();
      URL.revokeObjectURL(link.href);
    }
    return blob;
  }
}
