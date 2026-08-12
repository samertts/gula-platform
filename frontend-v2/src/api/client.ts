const API_BASE = import.meta.env.VITE_API_BASE || '/api';

// Web sessions are cookie-only. Tokens must never be persisted in browser storage
// or attached as bearer headers by this legacy client.
let refreshPromise: Promise<boolean> | null = null;

/** @deprecated Web clients receive HttpOnly cookies from the backend. */
export function setTokens(_access?: string, _refresh?: string) {
  // Kept as a no-op for legacy callers while the backend owns session cookies.
}

/** Clear the server-side cookie session through the normal logout endpoint. */
export function clearTokens() {
  // Intentionally no localStorage/sessionStorage access. Callers should invoke
  // the logout API when they need to invalidate the server-side session.
}

/** @deprecated Access tokens are HttpOnly and are not readable by JavaScript. */
export function getAccessToken(): string | null {
  return null;
}

async function attemptRefresh(): Promise<boolean> {
  if (refreshPromise) return refreshPromise;
  refreshPromise = (async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({}),
      });
      return res.ok;
    } catch {
      return false;
    } finally {
      refreshPromise = null;
    }
  })();
  return refreshPromise;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public detailAr?: string,
    public requestId?: string,
  ) {
    super(detail);
    this.name = 'ApiError';
  }
}

export class UnauthorizedError extends ApiError {
  constructor(detail = 'Unauthorized', detailAr?: string) {
    super(401, detail, detailAr);
    this.name = 'UnauthorizedError';
  }
}

export class ForbiddenError extends ApiError {
  constructor(detail = 'Forbidden', detailAr?: string) {
    super(403, detail, detailAr);
    this.name = 'ForbiddenError';
  }
}

export class NotFoundError extends ApiError {
  constructor(detail = 'Not found', detailAr?: string) {
    super(404, detail, detailAr);
    this.name = 'NotFoundError';
  }
}

export class ValidationError extends ApiError {
  constructor(public errors: Record<string, string[]>, detail = 'Validation error') {
    super(422, detail);
    this.name = 'ValidationError';
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  params?: Record<string, string | number | boolean | undefined | null>;
  headers?: Record<string, string>;
  signal?: AbortSignal;
  skipAuth?: boolean;
}

function buildUrl(path: string, params?: Record<string, string | number | boolean | undefined | null>): string {
  const url = new URL(`${API_BASE}${path}`, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, String(value));
      }
    });
  }
  return url.toString();
}

async function handleResponse(res: Response): Promise<any> {
  if (res.status === 204) return null;

  const text = await res.text();
  let body: any;
  try {
    body = JSON.parse(text);
  } catch {
    body = { detail: text };
  }

  if (!res.ok) {
    switch (res.status) {
      case 401:
        throw new UnauthorizedError(body.detail, body.detail_ar);
      case 403:
        throw new ForbiddenError(body.detail, body.detail_ar);
      case 404:
        throw new NotFoundError(body.detail, body.detail_ar);
      case 422: {
        const errors: Record<string, string[]> = {};
        if (body.errors) {
          Object.entries(body.errors).forEach(([k, v]) => {
            errors[k] = Array.isArray(v) ? v : [String(v)];
          });
        }
        throw new ValidationError(errors, body.detail);
      }
      default:
        throw new ApiError(res.status, body.detail || res.statusText, body.detail_ar, body.request_id);
    }
  }

  return body;
}

export async function apiRequest<T = any>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, params, headers: extraHeaders, signal, skipAuth } = options;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...extraHeaders,
  };
  const requestInit: RequestInit = {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    signal,
    credentials: 'include',
  };

  let res = await fetch(buildUrl(path, params), requestInit);

  if (res.status === 401 && !skipAuth) {
    const refreshed = await attemptRefresh();
    if (refreshed) {
      res = await fetch(buildUrl(path, params), requestInit);
    }
  }

  return handleResponse(res);
}

export async function apiGet<T = any>(path: string, params?: Record<string, any>, options?: RequestOptions): Promise<T> {
  return apiRequest<T>(path, { ...options, method: 'GET', params });
}

export async function apiPost<T = any>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
  return apiRequest<T>(path, { ...options, method: 'POST', body });
}

export async function apiPut<T = any>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
  return apiRequest<T>(path, { ...options, method: 'PUT', body });
}

export async function apiPatch<T = any>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
  return apiRequest<T>(path, { ...options, method: 'PATCH', body });
}

export async function apiDelete<T = any>(path: string, options?: RequestOptions): Promise<T> {
  return apiRequest<T>(path, { ...options, method: 'DELETE' });
}
