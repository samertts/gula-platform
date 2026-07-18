import { openDB, type IDBPDatabase } from 'idb';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
  offlinePriority?: 'high' | 'normal' | 'low';
  timeout?: number;
}

let authToken: string | null = localStorage.getItem('gula_lab_token');
let refreshToken: string | null = localStorage.getItem('gula_lab_refresh_token');

export function setAuthToken(token: string | null) {
  authToken = token;
  if (token) localStorage.setItem('gula_lab_token', token);
  else localStorage.removeItem('gula_lab_token');
}

export function getAuthToken(): string | null {
  return authToken;
}

export function setRefreshToken(token: string | null) {
  refreshToken = token;
  if (token) localStorage.setItem('gula_lab_refresh_token', token);
  else localStorage.removeItem('gula_lab_refresh_token');
}

let offlineDB: IDBPDatabase | null = null;

async function getOfflineDB(): Promise<IDBPDatabase> {
  if (offlineDB) return offlineDB;
  offlineDB = await openDB('gula-lab-cache', 1, {
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
  const { skipAuth = false, offlinePriority = 'normal', timeout = 30000, ...fetchOptions } = options;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Client-Type': 'laboratory-app',
    'X-Client-Version': '2.1.0',
    ...(fetchOptions.headers as Record<string, string>),
  };

  if (!skipAuth && authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  const isOnline = navigator.onLine;

  if (!isOnline && offlinePriority !== 'high') {
    const cached = await getFromCache<T>(endpoint, options.method || 'GET');
    if (cached !== null) return cached;

    if (options.method && options.method !== 'GET') {
      await queueOfflineRequest(endpoint, options);
      throw new OfflineQueuedError('تمت إضافة الطلب إلى قائمة الانتظار');
    }

    throw new OfflineError('لا يوجد اتصال بالإنترنت');
  }

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...fetchOptions,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (response.status === 401 && refreshToken) {
      const refreshed = await tryRefreshToken();
      if (refreshed) {
        headers['Authorization'] = `Bearer ${authToken}`;
        const retryResponse = await fetch(`${API_BASE}${endpoint}`, {
          ...fetchOptions,
          headers,
          signal: AbortSignal.timeout(timeout),
        });
        return handleResponse<T>(retryResponse, endpoint, options);
      }
    }

    return handleResponse<T>(response, endpoint, options);
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof ApiError || error instanceof OfflineQueuedError) {
      throw error;
    }
    if (!navigator.onLine) {
      const cached = await getFromCache<T>(endpoint, options.method || 'GET');
      if (cached !== null) return cached;
      if (options.method && options.method !== 'GET') {
        await queueOfflineRequest(endpoint, options);
        throw new OfflineQueuedError('تمت إضافة الطلب إلى قائمة الانتظار');
      }
      throw new OfflineError('لا يوجد اتصال بالإنترنت');
    }
    throw new ApiError(0, 'فشل الاتصال بالخادم');
  }
}

async function handleResponse<T>(
  response: Response,
  endpoint: string,
  options: RequestOptions,
): Promise<T> {
  if (!response.ok) {
    const errorBody = await response.text();
    let errorData: Record<string, unknown> = {};
    try { errorData = JSON.parse(errorBody); } catch { /* ignore */ }
    throw new ApiError(
      response.status,
      (errorData as any).message || (errorData as any).error || response.statusText,
      errorData,
    );
  }

  const data = await response.json();

  if (options.method === 'GET' || !options.method) {
    await cacheResponse(endpoint, data);
  }

  return data as T;
}

async function tryRefreshToken(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refreshToken }),
    });
    if (response.ok) {
      const data = await response.json();
      setAuthToken(data.accessToken);
      setRefreshToken(data.refreshToken);
      return true;
    }
    setAuthToken(null);
    setRefreshToken(null);
    return false;
  } catch {
    return false;
  }
}

async function queueOfflineRequest(endpoint: string, options: RequestOptions) {
  const db = await getOfflineDB();
  const cacheKey = `${options.method || 'GET'}:${endpoint}`;
  const cached = await db.get('cache', cacheKey);
  await db.add('requests', {
    url: `${API_BASE}${endpoint}`,
    method: options.method || 'GET',
    headers: options.headers as Record<string, string>,
    body: options.body,
    timestamp: Date.now(),
    retryCount: 0,
    maxRetries: 5,
    cachedData: cached?.data || null,
  });
  if ('serviceWorker' in navigator && 'sync' in navigator.serviceWorker) {
    try {
      const registration = await navigator.serviceWorker.ready;
      await (registration as any).sync.register('gula-lab-sync');
    } catch { /* ignore */ }
  }
}

async function cacheResponse(key: string, data: unknown) {
  try {
    const db = await getOfflineDB();
    await db.put('cache', { key: `GET:${key}`, data, timestamp: Date.now() });
  } catch { /* ignore */ }
}

async function getFromCache<T>(key: string, method: string): Promise<T | null> {
  try {
    const db = await getOfflineDB();
    const cached = await db.get('cache', `${method}:${key}`);
    if (cached && Date.now() - cached.timestamp < 1000 * 60 * 30) {
      return cached.data as T;
    }
    return null;
  } catch {
    return null;
  }
}

export async function processOfflineQueue() {
  const db = await getOfflineDB();
  const requests = await db.getAll('requests');

  for (const req of requests) {
    if (req.retryCount >= req.maxRetries) {
      if (req.id) await db.delete('requests', req.id);
      continue;
    }

    try {
      const response = await fetch(req.url, {
        method: req.method,
        headers: { ...req.headers, 'Content-Type': 'application/json' },
        body: req.body,
      });

      if (response.ok) {
        if (req.id) await db.delete('requests', req.id);
      } else {
        if (req.id) await db.put('requests', { ...req, retryCount: req.retryCount + 1, error: `${response.status}` });
      }
    } catch (e) {
      if (req.id) await db.put('requests', { ...req, retryCount: req.retryCount + 1, error: (e as Error).message });
    }
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

export class OfflineError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'OfflineError';
  }
}

export class OfflineQueuedError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'OfflineQueuedError';
  }
}

export async function uploadFile(
  endpoint: string,
  file: File,
  onProgress?: (progress: number) => void,
): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE}${endpoint}`);
    if (authToken) xhr.setRequestHeader('Authorization', `Bearer ${authToken}`);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) onProgress(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) resolve(JSON.parse(xhr.responseText));
      else reject(new ApiError(xhr.status, xhr.responseText));
    };
    xhr.onerror = () => reject(new Error('Upload failed'));
    xhr.send(formData(file));
  });
}

function formData(file: File): FormData {
  const fd = new FormData();
  fd.append('file', file);
  return fd;
}
