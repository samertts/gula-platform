const API_BASE = import.meta.env.VITE_API_BASE || '/api';

let accessToken: string | null = localStorage.getItem('gula_access_token');
let refreshToken: string | null = localStorage.getItem('gula_refresh_token');
let refreshPromise: Promise<boolean> | null = null;

export function setTokens(access: string, refresh: string) {
  accessToken = access;
  refreshToken = refresh;
  localStorage.setItem('gula_access_token', access);
  localStorage.setItem('gula_refresh_token', refresh);
}

export function clearTokens() {
  accessToken = null;
  refreshToken = null;
  localStorage.removeItem('gula_access_token');
  localStorage.removeItem('gula_refresh_token');
}

export function getAccessToken(): string | null {
  return accessToken;
}

async function attemptRefresh(): Promise<boolean> {
  if (!refreshToken) return false;
  if (refreshPromise) return refreshPromise;
  refreshPromise = (async () => {
    try {
        const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!res.ok) {
        clearTokens();
        return false;
      }
      const data = await res.json();
      setTokens(data.token, data.refresh_token);
      return true;
    } catch {
      clearTokens();
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

  if (!skipAuth && accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  let res = await fetch(buildUrl(path, params), {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    signal,
  });

  if (res.status === 401 && !skipAuth && refreshToken) {
    const refreshed = await attemptRefresh();
    if (refreshed) {
      headers['Authorization'] = `Bearer ${accessToken}`;
      res = await fetch(buildUrl(path, params), {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
        signal,
      });
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
