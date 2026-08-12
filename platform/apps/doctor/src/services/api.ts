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
  timeout?: number;
  entityType?: string;
  entityId?: string;
  action?: string;
  expectedVersion?: number;
}

// Authentication is carried only by server-issued HttpOnly cookies.
// Keep the compatibility export without retaining any token in browser storage.
export function setAuthToken(_token: string | null, _refresh?: string | null) {
  return undefined;
}

export function getAuthToken(): string | null {
  return null;
}

let offlineDB: IDBPDatabase | null = null;
let queueCleanup: Promise<void> | null = null;

async function getOfflineDB(): Promise<IDBPDatabase> {
  if (offlineDB) return offlineDB;
  offlineDB = await openDB('gula-doctor-offline', 3, {
    upgrade(db, oldVersion) {
      if (!db.objectStoreNames.contains('requests')) {
        db.createObjectStore('requests', { keyPath: 'id', autoIncrement: true });
      }
      if (!db.objectStoreNames.contains('cache')) {
        db.createObjectStore('cache', { keyPath: 'key' });
      }
      if (!db.objectStoreNames.contains('patients')) {
        db.createObjectStore('patients', { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains('clinicalData')) {
        db.createObjectStore('clinicalData', { keyPath: 'id' });
      }
      if (oldVersion < 2) {
        if (!db.objectStoreNames.contains('pendingSignatures')) {
          db.createObjectStore('pendingSignatures', { keyPath: 'id', autoIncrement: true });
        }
        if (!db.objectStoreNames.contains('voiceNotes')) {
          db.createObjectStore('voiceNotes', { keyPath: 'id', autoIncrement: true });
        }
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
        source: 'gula-doctor-offline.requests',
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
    offlinePriority = 'normal',
    timeout = 30000,
    entityType: _entityType,
    entityId: _entityId,
    action: _action,
    expectedVersion: _expectedVersion,
    ...fetchOptions
  } = options;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Client-Type': 'doctor-app',
    ...(fetchOptions.headers as Record<string, string>),
  };

  // Browser clients never construct Authorization headers; cookies are HttpOnly.
  void skipAuth;
  void _entityType;
  void _entityId;
  void _action;
  void _expectedVersion;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  const isOnline = navigator.onLine;

  if (!isOnline && offlinePriority !== 'high') {
    const cache = await getFromCache<T>(endpoint, options.method || 'GET');
    if (cache !== null) return cache;

    if (options.method && options.method !== 'GET') {
      await queueOfflineRequest(endpoint, options);
      throw new OfflineQueuedError('تمت إضافة الطلب إلى قائمة الانتظار غير المتصلة');
    }
    throw new OfflineError('لا يوجد اتصال بالإنترنت');
  }

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
    entityType: options.entityType || endpoint.split('/').filter(Boolean)[0] || 'doctor',
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
  const requests = await db.getAll('requests');

  for (const stored of requests) {
    const req = stored as OfflineQueueEnvelope & { id?: number; retryCount?: number; maxRetries?: number };
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
      await db.put('requests', { ...envelope, id: req.id, state: 'failed' });
      continue;
    }

    try {
      const headerResult = sanitizeQueueHeaders(envelope.headers);
      const payloadResult = inspectQueuePayload(envelope.body);
      if (headerResult.hadSensitiveHeader || !payloadResult.safe) {
        await db.put('requests', { ...envelope, id: req.id, state: 'rejected', lastError: headerResult.hadSensitiveHeader ? 'sensitive-header' : payloadResult.reason });
        continue;
      }
      const response = await fetch(envelope.url, buildQueueRequestInit(envelope));
      const disposition = classifyQueueResponse(response.status);
      if (disposition === 'synced') {
        await db.delete('requests', req.id);
      } else if (disposition === 'conflict') {
        let serverBody: unknown;
        try { serverBody = await response.json(); } catch { /* no JSON body */ }
        await db.put('requests', {
          ...nextQueueEnvelopeState(envelope, disposition, `HTTP ${response.status}`, {
            status: response.status as 409 | 412,
            serverBody,
            detectedAt: new Date().toISOString(),
          }),
          id: req.id,
        });
      } else {
        await db.put('requests', { ...nextQueueEnvelopeState(envelope, disposition, `HTTP ${response.status}`), id: req.id });
      }
    } catch (error) {
      await db.put('requests', { ...nextQueueEnvelopeState(envelope, 'retry', error instanceof Error ? error.message : 'network-error'), id: req.id });
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

export async function cachePatientData(patientId: string, data: unknown) {
  const db = await getOfflineDB();
  await db.put('patients', { id: patientId, data, timestamp: Date.now() });
}

export async function getCachedPatientData(patientId: string): Promise<unknown | null> {
  try {
    const db = await getOfflineDB();
    const cached = await db.get('patients', patientId);
    if (cached && Date.now() - cached.timestamp < 1000 * 60 * 60 * 24) {
      return cached.data;
    }
    return null;
  } catch {
    return null;
  }
}

export async function cacheClinicalData(key: string, data: unknown) {
  const db = await getOfflineDB();
  await db.put('clinicalData', { id: key, data, timestamp: Date.now() });
}

export async function getCachedClinicalData(key: string): Promise<unknown | null> {
  try {
    const db = await getOfflineDB();
    const cached = await db.get('clinicalData', key);
    if (cached && Date.now() - cached.timestamp < 1000 * 60 * 60 * 12) {
      return cached.data;
    }
    return null;
  } catch {
    return null;
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
    xhr.setRequestHeader('X-Client-Type', 'doctor-app');
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
