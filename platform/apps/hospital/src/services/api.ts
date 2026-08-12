import { openDB, type IDBPDatabase } from 'idb';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://api.gula.health/api/v1';

interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
  offlinePriority?: 'high' | 'normal' | 'low';
  timeout?: number;
}

// Authentication is carried only by server-issued HttpOnly cookies.
export function setAuthToken(_token: string | null, _refresh?: string | null) {
  return undefined;
}

export function getAuthToken(): string | null {
  return null;
}

let offlineDB: IDBPDatabase | null = null;

async function getOfflineDB(): Promise<IDBPDatabase> {
  if (offlineDB) return offlineDB;
  offlineDB = await openDB('gula-hospital-offline', 1, {
    upgrade(db) {
      if (!db.objectStoreNames.contains('requests')) {
        db.createObjectStore('requests', { keyPath: 'id', autoIncrement: true });
      }
      if (!db.objectStoreNames.contains('cache')) {
        db.createObjectStore('cache', { keyPath: 'key' });
      }
    },
  });
  return offlineDB;
}

async function tryRefreshToken(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    });
    return response.ok;
  } catch {
    return false;
  }
}

export async function apiRequest<T = unknown>(
  endpoint: string,
  options: RequestOptions = {},
): Promise<T> {
  const {
    skipAuth = false,
    timeout = 30000,
    ...fetchOptions
  } = options;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Client-Type': 'hospital-app',
    ...(fetchOptions.headers as Record<string, string>),
  };

  // Do not construct Authorization headers in the browser; cookies are HttpOnly.
  void skipAuth;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    let response = await fetch(`${API_BASE}${endpoint}`, {
      ...fetchOptions,
      credentials: 'include',
      headers,
      signal: controller.signal,
    });

    if (response.status === 401 && !skipAuth && endpoint !== '/auth/refresh') {
      clearTimeout(timeoutId);
      const refreshed = await tryRefreshToken();
      if (refreshed) {
        const retryController = new AbortController();
        const retryTimeout = setTimeout(() => retryController.abort(), timeout);
        response = await fetch(`${API_BASE}${endpoint}`, {
          ...fetchOptions,
          credentials: 'include',
          headers,
          signal: retryController.signal,
        });
        clearTimeout(retryTimeout);
      }
    }

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorBody = await response.text();
      let errorData: Record<string, unknown> = {};
      try {
        errorData = JSON.parse(errorBody);
      } catch {}
      throw new ApiError(
        response.status,
        (errorData as any).message || (errorData as any).error || response.statusText,
        errorData,
      );
    }

    const data = await response.json();
    return data as T;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof ApiError) throw error;
    throw new ApiError(0, 'فشل الاتصال بالخادم');
  }
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: Record<string, unknown>,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}
