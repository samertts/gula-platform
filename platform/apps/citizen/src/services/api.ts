import { openDB, type IDBPDatabase } from 'idb';
import {
  ApiClientError,
  DemoIsolationError,
  buildQueueRequestInit,
  createApiClient,
  classifyQueueResponse,
  createQueueEnvelope,
  inspectQueuePayload,
  nextQueueEnvelopeState,
  sanitizeQueueHeaders,
  type OfflineQueueEnvelope,
} from '@gula/ui-platform';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://api.gula.health/api/v1';
const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';
const DEMO_API_BASE_URL = import.meta.env.VITE_DEMO_API_BASE_URL;
const backend = createApiClient({
  baseUrl: API_BASE,
  clientName: 'citizen-app',
  refreshPath: '/auth/refresh',
  demoMode: DEMO_MODE,
  demoBaseUrl: DEMO_API_BASE_URL,
});

function requestBaseUrl(): string {
  if (DEMO_MODE) {
    if (!DEMO_API_BASE_URL) throw new DemoIsolationError('الوضع التجريبي غير مهيأ بعنوان Backend معزول.');
    return DEMO_API_BASE_URL;
  }
  return API_BASE;
}

function assertQueuedUrlAllowed(url: string): void {
  if (!DEMO_MODE) return;
  const queuedOrigin = new URL(url, window.location.origin).origin;
  const demoOrigin = new URL(requestBaseUrl(), window.location.origin).origin;
  if (queuedOrigin !== demoOrigin) throw new DemoIsolationError('تم رفض طلب Demo قديم يشير إلى أصل غير معزول.');
}

interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
  offlinePriority?: 'high' | 'normal' | 'low';
  entityType?: string;
  entityId?: string;
  action?: string;
  expectedVersion?: number;
  timeout?: number;
}

// Browser authentication is carried only by the server-issued HttpOnly cookie.
// These compatibility functions deliberately do not retain or return credentials.
export function setAuthToken(_token: string | null) {
  return undefined;
}

export function getAuthToken(): string | null {
  return null;
}

let offlineDB: IDBPDatabase | null = null;
let queueCleanup: Promise<void> | null = null;

async function getOfflineDB(): Promise<IDBPDatabase> {
  if (offlineDB) return offlineDB;
  offlineDB = await openDB('gula-citizen-offline', 2, {
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
        source: 'gula-citizen-offline.requests',
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
  const {
    skipAuth: _skipAuth,
    offlinePriority = 'normal',
    timeout: _timeout,
    entityType: _entityType,
    entityId: _entityId,
    action: _action,
    expectedVersion,
    ...fetchOptions
  } = options;
  void _timeout;
  void _entityType;
  void _entityId;
  void _action;
  const method = options.method || 'GET';
  const isOnline = navigator.onLine;

  if (!isOnline && offlinePriority !== 'high') {
    const cache = await getFromCache<T>(endpoint, method);
    if (cache !== null) return cache;
    if (method !== 'GET') {
      await queueOfflineRequest(endpoint, options);
      throw new OfflineQueuedError('تمت إضافة الطلب إلى قائمة الانتظار غير المتصلة');
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
        ...(fetchOptions.headers as Record<string, string>),
      },
      expectedVersion,
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
      const cache = await getFromCache<T>(endpoint, method);
      if (cache !== null) return cache;
      if (method !== 'GET') {
        await queueOfflineRequest(endpoint, options);
        throw new OfflineQueuedError('تمت إضافة الطلب إلى قائمة الانتظار غير المتصلة');
      }
      throw new OfflineError('لا يوجد اتصال بالإنترنت');
    }
    throw new ApiError(0, 'فشل الاتصال بالخادم');
  }
}

async function queueOfflineRequest(endpoint: string, options: RequestOptions) {
  const db = await getOfflineDB();
  const envelope = await createQueueEnvelope({
    url: `${requestBaseUrl()}${endpoint}`,
    method: options.method || 'POST',
    headers: options.headers,
    body: options.body,
    entityType: options.entityType || endpoint.split('/').filter(Boolean)[0] || 'unknown',
    entityId: options.entityId,
    action: options.action || (options.method || 'POST').toLowerCase(),
    expectedVersion: options.expectedVersion,
  });
  await db.add('requests', envelope);
  if ('serviceWorker' in navigator && 'sync' in navigator.serviceWorker) {
    try {
      const registration = await navigator.serviceWorker.ready;
      await (registration as any).sync.register('sync-offline-queue');
    } catch {}
  }
}

async function cacheResponse(key: string, data: unknown) {
  try {
    const db = await getOfflineDB();
    await db.put('cache', { key: `GET:${key}`, data, timestamp: Date.now() });
  } catch {}
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
  const [requests, requestKeys] = await Promise.all([
    db.getAll('requests'),
    db.getAllKeys('requests'),
  ]);

  for (const [index, stored] of requests.entries()) {
    const req = stored as OfflineQueueEnvelope & { id?: number; retryCount?: number; maxRetries?: number };
    const requestKey = req.id ?? requestKeys[index];
    if (requestKey === undefined) {
      // A queue record without an IndexedDB key cannot be reconciled safely.
      // Leave it untouched for explicit recovery rather than deleting or replaying it.
      console.error('[CitizenOfflineQueue] missing IndexedDB request key', { index });
      continue;
    }
    const envelope: OfflineQueueEnvelope = req.schemaVersion === 1
      ? req
      : await createQueueEnvelope({
        url: req.url,
        method: req.method,
        headers: req.headers,
        body: req.body,
        entityType: req.entityType || 'legacy',
        action: req.action || req.method.toLowerCase(),
        operationId: req.operationId,
        idempotencyKey: req.idempotencyKey,
        expectedVersion: req.expectedVersion,
      });

    if (envelope.state === 'conflict' || envelope.state === 'rejected' || envelope.state === 'synced') continue;
    if (envelope.attempt >= envelope.maxAttempts) {
      await db.put('requests', { ...envelope, id: requestKey, state: 'failed' });
      continue;
    }

    try {
      const security = inspectQueuePayload(envelope.body);
      const headerResult = sanitizeQueueHeaders(envelope.headers);
      if (headerResult.hadSensitiveHeader || !security.safe) {
        await db.put('requests', { ...envelope, id: requestKey, state: 'rejected', lastError: headerResult.hadSensitiveHeader ? 'sensitive-header' : security.reason });
        continue;
      }
      assertQueuedUrlAllowed(envelope.url);
      const response = await fetch(envelope.url, buildQueueRequestInit(envelope));
      const disposition = classifyQueueResponse(response.status);
      if (disposition === 'synced') {
        await db.delete('requests', requestKey);
      } else if (disposition === 'conflict') {
        let serverBody: unknown;
        try { serverBody = await response.json(); } catch { /* response may have no JSON body */ }
        await db.put('requests', {
          ...nextQueueEnvelopeState(envelope, disposition, `HTTP ${response.status}`, {
            status: response.status as 409 | 412,
            serverBody,
            detectedAt: new Date().toISOString(),
          }),
          id: requestKey,
        });
      } else if (disposition === 'rejected') {
        await db.put('requests', { ...nextQueueEnvelopeState(envelope, disposition, `HTTP ${response.status}`), id: requestKey });
      } else {
        await db.put('requests', { ...nextQueueEnvelopeState(envelope, disposition, `HTTP ${response.status}`), id: requestKey });
      }
    } catch (error) {
      await db.put('requests', { ...nextQueueEnvelopeState(envelope, 'retry', error instanceof Error ? error.message : 'network-error'), id: requestKey });
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
  const formData = new FormData();
  formData.append('file', file);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const uploadBaseUrl = requestBaseUrl();
    xhr.open('POST', `${uploadBaseUrl}${endpoint}`);
    xhr.withCredentials = true;
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        reject(new ApiError(xhr.status, xhr.responseText));
      }
    };
    xhr.onerror = () => reject(new Error('Upload failed'));
    xhr.send(formData);
  });
}
