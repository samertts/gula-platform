import { openDB, type IDBPDatabase } from 'idb';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://api.gula.health/api/v1';

interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
  offlinePriority?: 'high' | 'normal' | 'low';
  timeout?: number;
}

let authToken: string | null = localStorage.getItem('gula_hospital_token');
let refreshTokenValue: string | null = localStorage.getItem('gula_hospital_refresh');

export function setAuthToken(token: string | null, refresh?: string | null) {
  authToken = token;
  if (token) {
    localStorage.setItem('gula_hospital_token', token);
  } else {
    localStorage.removeItem('gula_hospital_token');
  }
  if (refresh !== undefined) {
    refreshTokenValue = refresh;
    if (refresh) {
      localStorage.setItem('gula_hospital_refresh', refresh);
    } else {
      localStorage.removeItem('gula_hospital_refresh');
    }
  }
}

export function getAuthToken(): string | null {
  return authToken;
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
  if (!refreshTokenValue) return false;
  try {
    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refreshToken: refreshTokenValue }),
    });
    if (response.ok) {
      const data = await response.json();
      setAuthToken(data.accessToken, data.refreshToken);
      return true;
    }
    return false;
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

  if (!skipAuth && authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    let response = await fetch(`${API_BASE}${endpoint}`, {
      ...fetchOptions,
      headers,
      signal: controller.signal,
    });

    if (response.status === 401 && !skipAuth && authToken) {
      clearTimeout(timeoutId);
      const refreshed = await tryRefreshToken();
      if (refreshed) {
        headers['Authorization'] = `Bearer ${authToken}`;
        const retryController = new AbortController();
        const retryTimeout = setTimeout(() => retryController.abort(), timeout);
        response = await fetch(`${API_BASE}${endpoint}`, {
          ...fetchOptions,
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
