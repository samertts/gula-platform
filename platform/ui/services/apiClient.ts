export type ApiPrimitive = string | number | boolean;
export type ApiQueryValue = ApiPrimitive | null | undefined;

export interface ApiClientOptions {
  baseUrl: string;
  clientName: string;
  timeoutMs?: number;
  maxGetRetries?: number;
  refreshPath?: string;
  demoMode?: boolean;
  demoBaseUrl?: string;
}

export interface ApiRequestOptions extends Omit<RequestInit, 'body' | 'headers'> {
  body?: unknown;
  headers?: HeadersInit;
  query?: Record<string, ApiQueryValue>;
  idempotencyKey?: string;
  requestFingerprint?: string;
  expectedVersion?: number;
  operationId?: string;
  skipRefresh?: boolean;
}

export interface ErrorContract {
  code: string;
  message: string;
  details: Record<string, unknown>;
  request_id: string;
  timestamp: string;
  detail?: string;
  detail_ar?: string;
}

export class ApiClientError extends Error {
  readonly name: string = 'ApiClientError';

  constructor(
    public readonly status: number,
    message: string,
    public readonly contract?: Partial<ErrorContract>,
  ) {
    super(message);
  }

  get code(): string {
    return this.contract?.code || (this.status === 0 ? 'NETWORK_ERROR' : 'HTTP_ERROR');
  }

  get requestId(): string | undefined {
    return this.contract?.request_id;
  }

  get isConflict(): boolean {
    return this.status === 409 || this.status === 412;
  }

  get isAuthError(): boolean {
    return this.status === 401 || this.status === 403;
  }
}

export class DemoIsolationError extends ApiClientError {
  readonly name = 'DemoIsolationError';

  constructor(message = 'الوضع التجريبي معزول ولا يسمح بالاتصال ببيانات الإنتاج.') {
    super(0, message, {
      code: 'DEMO_LIVE_API_BLOCKED',
      message,
      details: {},
      request_id: 'client-demo-isolation',
      timestamp: new Date().toISOString(),
    });
  }
}

const RETRYABLE_STATUS = new Set([408, 425, 429, 502, 503, 504]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function getMessage(value: unknown, fallback: string): string {
  if (!isRecord(value)) return fallback;
  const message = value.message ?? value.detail_ar ?? value.detail ?? value.error;
  return typeof message === 'string' && message.trim() ? message : fallback;
}

function toContract(value: unknown): Partial<ErrorContract> | undefined {
  if (!isRecord(value)) return undefined;
  return {
    code: typeof value.code === 'string' ? value.code : undefined,
    message: typeof value.message === 'string' ? value.message : undefined,
    details: isRecord(value.details) ? value.details : {},
    request_id: typeof value.request_id === 'string' ? value.request_id : 'unknown',
    timestamp: typeof value.timestamp === 'string' ? value.timestamp : new Date().toISOString(),
    detail: typeof value.detail === 'string' ? value.detail : undefined,
    detail_ar: typeof value.detail_ar === 'string' ? value.detail_ar : undefined,
  };
}

function makeRequestId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID();
  return `gula-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function buildUrl(baseUrl: string, path: string, query?: Record<string, ApiQueryValue>): string {
  const url = new URL(`${baseUrl.replace(/\/$/, '')}/${path.replace(/^\//, '')}`, window.location.origin);
  Object.entries(query || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null) url.searchParams.set(key, String(value));
  });
  return url.toString();
}

function isRetryableMethod(method: string): boolean {
  return ['GET', 'HEAD', 'OPTIONS'].includes(method.toUpperCase());
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function createApiClient(options: ApiClientOptions) {
  const timeoutMs = options.timeoutMs ?? 30_000;
  const maxGetRetries = options.maxGetRetries ?? 2;
  const baseUrl = options.baseUrl || '/api';
  const demoMode = options.demoMode ?? import.meta.env.VITE_DEMO_MODE === 'true';
  const demoBaseUrl = options.demoBaseUrl || import.meta.env.VITE_DEMO_API_BASE_URL;

  function assertDemoIsolation(url: string): void {
    if (!demoMode) return;
    if (!demoBaseUrl) {
      throw new DemoIsolationError('الوضع التجريبي غير مهيأ بعنوان Backend تجريبي معزول.');
    }
    const liveOrigin = new URL(url, window.location.origin).origin;
    const demoOrigin = new URL(demoBaseUrl, window.location.origin).origin;
    if (liveOrigin !== demoOrigin) throw new DemoIsolationError();
  }

  async function parseResponseBody(response: Response): Promise<unknown> {
    if (response.status === 204) return undefined;
    const text = await response.text();
    if (!text) return undefined;
    try {
      return JSON.parse(text);
    } catch {
      return text;
    }
  }

  async function request<T = unknown>(path: string, requestOptions: ApiRequestOptions = {}): Promise<T> {
    const method = (requestOptions.method || 'GET').toUpperCase();
    const requestBaseUrl = demoMode ? (demoBaseUrl || baseUrl) : baseUrl;
    const url = buildUrl(requestBaseUrl, path, requestOptions.query);
    assertDemoIsolation(url);

    const headers = new Headers(requestOptions.headers);
    headers.set('Accept', 'application/json');
    headers.set('X-Client-Type', options.clientName);
    headers.set('X-GULA-Request-ID', makeRequestId());
    if (requestOptions.body !== undefined && !(requestOptions.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
    }
    if (requestOptions.idempotencyKey) headers.set('Idempotency-Key', requestOptions.idempotencyKey);
    if (requestOptions.requestFingerprint) headers.set('X-GULA-Request-Fingerprint', requestOptions.requestFingerprint);
    if (requestOptions.expectedVersion !== undefined) headers.set('If-Match', String(requestOptions.expectedVersion));
    if (requestOptions.operationId) headers.set('X-GULA-Operation-ID', requestOptions.operationId);

    const body = requestOptions.body instanceof FormData || typeof requestOptions.body === 'string'
      ? requestOptions.body
      : requestOptions.body === undefined ? undefined : JSON.stringify(requestOptions.body);
    const fetchOptions: RequestInit = {
      ...requestOptions,
      method,
      credentials: 'include',
      headers,
      body,
    };
    delete (fetchOptions as Record<string, unknown>).query;
    delete (fetchOptions as Record<string, unknown>).idempotencyKey;
    delete (fetchOptions as Record<string, unknown>).requestFingerprint;
    delete (fetchOptions as Record<string, unknown>).expectedVersion;
    delete (fetchOptions as Record<string, unknown>).operationId;
    delete (fetchOptions as Record<string, unknown>).skipRefresh;

    let attempt = 0;
    let refreshed = false;
    while (true) {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
      try {
        const response = await fetch(url, { ...fetchOptions, signal: requestOptions.signal || controller.signal });
        clearTimeout(timeoutId);

        if (response.status === 401 && options.refreshPath && !requestOptions.skipRefresh && !refreshed && path !== options.refreshPath) {
          refreshed = true;
          await request(options.refreshPath, { method: 'POST', body: {}, skipRefresh: true });
          continue;
        }

        const payload = await parseResponseBody(response);
        if (!response.ok) {
          throw new ApiClientError(response.status, getMessage(payload, response.statusText || 'فشل الطلب'), toContract(payload));
        }
        return payload as T;
      } catch (error) {
        clearTimeout(timeoutId);
        if (error instanceof ApiClientError) {
          if (isRetryableMethod(method) && RETRYABLE_STATUS.has(error.status) && attempt < maxGetRetries) {
            await sleep(250 * 2 ** attempt);
            attempt += 1;
            continue;
          }
          throw error;
        }
        if (requestOptions.signal?.aborted) throw error;
        if (isRetryableMethod(method) && attempt < maxGetRetries) {
          await sleep(250 * 2 ** attempt);
          attempt += 1;
          continue;
        }
        throw new ApiClientError(0, 'تعذر الاتصال بالخادم. تحقق من الاتصال وحاول مرة أخرى.');
      }
    }
  }

  return {
    request,
    get<T = unknown>(path: string, query?: Record<string, ApiQueryValue>, signal?: AbortSignal) {
      return request<T>(path, { method: 'GET', query, signal });
    },
    post<T = unknown>(path: string, body?: unknown, requestOptions: Omit<ApiRequestOptions, 'method' | 'body'> = {}) {
      return request<T>(path, { ...requestOptions, method: 'POST', body });
    },
    put<T = unknown>(path: string, body?: unknown, requestOptions: Omit<ApiRequestOptions, 'method' | 'body'> = {}) {
      return request<T>(path, { ...requestOptions, method: 'PUT', body });
    },
    patch<T = unknown>(path: string, body?: unknown, requestOptions: Omit<ApiRequestOptions, 'method' | 'body'> = {}) {
      return request<T>(path, { ...requestOptions, method: 'PATCH', body });
    },
    delete<T = unknown>(path: string, requestOptions: Omit<ApiRequestOptions, 'method'> = {}) {
      return request<T>(path, { ...requestOptions, method: 'DELETE' });
    },
  };
}

export type ApiClient = ReturnType<typeof createApiClient>;
