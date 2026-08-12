import { openDB, type IDBPDatabase } from 'idb';
import { createApiClient } from '@gula/ui-platform';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://api.gula.health/api/v1';
const backend = createApiClient({
  baseUrl: API_BASE,
  clientName: 'hospital-app',
  refreshPath: '/auth/refresh',
});

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

export async function apiRequest<T = unknown>(
  endpoint: string,
  options: RequestOptions = {},
): Promise<T> {
  const { skipAuth: _skipAuth, timeout: _timeout, offlinePriority: _offlinePriority, ...requestOptions } = options;
  void _skipAuth;
  void _timeout;
  void _offlinePriority;
  try {
    return await backend.request<T>(endpoint, requestOptions);
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof Error) throw new ApiError(0, error.message);
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
