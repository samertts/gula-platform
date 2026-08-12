import { openDB, type IDBPDatabase } from 'idb';
import { ApiClientError, createApiClient, inspectQueuePayload, sanitizeQueueHeaders } from '@gula/ui-platform';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const backend = createApiClient({
  baseUrl: API_BASE,
  clientName: 'laboratory-app',
  refreshPath: '/auth/refresh',
});

interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
  offlinePriority?: 'high' | 'normal' | 'low';
  timeout?: number;
}

// Authentication is carried only by the server-issued HttpOnly cookies.
// Keep these compatibility exports for existing callers without retaining secrets.
export function setAuthToken(_token: string | null) {
  return undefined;
}

export function getAuthToken(): string | null {
  return null;
}

export function setRefreshToken(_token: string | null) {
  return undefined;
}

let offlineDB: IDBPDatabase | null = null;
let queueCleanup: Promise<void> | null = null;

async function getOfflineDB(): Promise<IDBPDatabase> {
  if (offlineDB) return offlineDB;
  offlineDB = await openDB('gula-lab-cache', 2, {
    upgrade(db) {
      if (!db.objectStoreNames.contains('requests')) {
        db.createObjectStore('requests', { keyPath: 'id', autoIncrement: true });
      }
      if (!db.objectStoreNames.contains('cache')) {
        db.createObjectStore('cache', { keyPath: 'key' });
      }
      if (!db.objectStoreNames.contains('queue_rejections')) {
        db.createObjectStore('queue_rejections', { keyPath: 'id', autoIncrement: true });
      }
    },
  });
  queueCleanup = queueCleanup ?? cleanLegacyQueue(offlineDB);
  await queueCleanup;
  return offlineDB;
}

async function cleanLegacyQueue(db: IDBPDatabase): Promise<void> {
  const requests = await db.getAll('requests');
  const tx = db.transaction(['requests', 'queue_rejections'], 'readwrite');
  for (const request of requests) {
    const headerResult = sanitizeQueueHeaders(request.headers);
    const payloadResult = inspectQueuePayload(request.body);
    if (headerResult.hadSensitiveHeader || !payloadResult.safe) {
      await tx.objectStore('queue_rejections').add({
        source: 'gula-lab-cache.requests',
        requestId: request.id,
        url: request.url,
        method: request.method,
        reason: headerResult.hadSensitiveHeader ? 'sensitive-header' : payloadResult.reason,
        rejectedAt: Date.now(),
      });
      await tx.objectStore('requests').delete(request.id);
      continue;
    }
    await tx.objectStore('requests').put({ ...request, headers: headerResult.headers });
  }
  await tx.done;
}

export async function apiRequest<T = unknown>(
  endpoint: string,
  options: RequestOptions = {},
): Promise<T> {
  const { skipAuth: _skipAuth, offlinePriority = 'normal', timeout: _timeout, ...fetchOptions } = options;
  void _timeout;
  const method = options.method || 'GET';
  const isOnline = navigator.onLine;

  if (!isOnline && offlinePriority !== 'high') {
    const cached = await getFromCache<T>(endpoint, method);
    if (cached !== null) return cached;
    if (method !== 'GET') {
      await queueOfflineRequest(endpoint, options);
      throw new OfflineQueuedError('تمت إضافة الطلب إلى قائمة الانتظار');
    }
    throw new OfflineError('لا يوجد اتصال بالإنترنت');
  }

  try {
    const data = await backend.request<T>(endpoint, {
      ...fetchOptions,
      method,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Client-Version': '2.1.0',
        ...(fetchOptions.headers as Record<string, string>),
      },
      skipRefresh: Boolean(_skipAuth) || endpoint === '/auth/refresh',
    });
    if (method === 'GET') await cacheResponse(endpoint, data);
    return data;
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw new ApiError(error.status, error.message, error.contract as Record<string, unknown> | undefined);
    }
    if (error instanceof ApiError || error instanceof OfflineQueuedError) throw error;
    if (!navigator.onLine) {
      const cached = await getFromCache<T>(endpoint, method);
      if (cached !== null) return cached;
      if (method !== 'GET') {
        await queueOfflineRequest(endpoint, options);
        throw new OfflineQueuedError('تمت إضافة الطلب إلى قائمة الانتظار');
      }
      throw new OfflineError('لا يوجد اتصال بالإنترنت');
    }
    throw new ApiError(0, 'فشل الاتصال بالخادم');
  }
}

async function queueOfflineRequest(endpoint: string, options: RequestOptions) {
  const db = await getOfflineDB();
  const cacheKey = `${options.method || 'GET'}:${endpoint}`;
  const cached = await db.get('cache', cacheKey);
  const headerResult = sanitizeQueueHeaders(options.headers as Record<string, string>);
  const payloadResult = inspectQueuePayload(options.body);
  if (headerResult.hadSensitiveHeader || !payloadResult.safe) {
    throw new OfflineError('تم رفض تخزين طلب غير متصل يحتوي بيانات اعتماد');
  }
  await db.add('requests', {
    url: `${API_BASE}${endpoint}`,
    method: options.method || 'GET',
    headers: headerResult.headers,
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
      const headerResult = sanitizeQueueHeaders(req.headers);
      const payloadResult = inspectQueuePayload(req.body);
      if (headerResult.hadSensitiveHeader || !payloadResult.safe) {
        if (req.id) await db.delete('requests', req.id);
        continue;
      }
      const response = await fetch(req.url, {
        method: req.method,
        credentials: 'include',
        headers: { ...headerResult.headers, 'Content-Type': 'application/json' },
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
    xhr.withCredentials = true;
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
