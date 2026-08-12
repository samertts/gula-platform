import { openDB, type IDBPDatabase } from 'idb';
import {
  buildQueueRequestInit,
  classifyQueueResponse,
  createQueueEnvelope,
  inspectQueuePayload,
  nextQueueEnvelopeState,
  sanitizeQueueHeaders,
  type OfflineQueueEnvelope,
} from '@gula/ui-platform';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://api.gula.health/api/v1';

interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
  offlinePriority?: 'high' | 'normal' | 'low';
  entityType?: string;
  entityId?: string;
  action?: string;
  expectedVersion?: number;
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
    skipAuth = false,
    offlinePriority = 'normal',
    entityType: _entityType,
    entityId: _entityId,
    action: _action,
    expectedVersion: _expectedVersion,
    ...fetchOptions
  } = options;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    ...(fetchOptions.headers as Record<string, string>),
  };

  // Do not construct Authorization headers in the browser; authentication uses HttpOnly cookies.
  void skipAuth;
  void _entityType;
  void _entityId;
  void _action;
  void _expectedVersion;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000);

  const isOnline = navigator.onLine;

  if (!isOnline && offlinePriority !== 'high') {
    const cache = await getFromCache<T>(endpoint, options.method || 'GET');
    if (cache !== null) {
      return cache;
    }
    if (options.method && options.method !== 'GET') {
      await queueOfflineRequest(endpoint, options);
      throw new OfflineQueuedError('تمت إضافة الطلب إلى قائمة الانتظار غير المتصلة');
    }
    throw new OfflineError('لا يوجد اتصال بالإنترنت');
  }

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...fetchOptions,
      credentials: 'include',
      headers,
      signal: controller.signal,
    });

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

    if (options.method === 'GET' || !options.method) {
      await cacheResponse(endpoint, data);
    }

    return data as T;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof ApiError || error instanceof OfflineQueuedError) {
      throw error;
    }
    if (!navigator.onLine) {
      const cache = await getFromCache<T>(endpoint, options.method || 'GET');
      if (cache !== null) return cache;
      if (options.method && options.method !== 'GET') {
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
    url: `${API_BASE}${endpoint}`,
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
    xhr.open('POST', `${API_BASE}${endpoint}`);
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
