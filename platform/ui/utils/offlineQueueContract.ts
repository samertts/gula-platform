import { inspectQueueRecord, sanitizeQueueHeaders } from './offlineQueueSecurity';

export type QueueState = 'pending' | 'syncing' | 'synced' | 'conflict' | 'rejected' | 'failed';

export interface OfflineQueueEnvelope {
  schemaVersion: 1;
  operationId: string;
  idempotencyKey: string;
  requestFingerprint: string;
  entityType: string;
  entityId?: string;
  action: string;
  url: string;
  method: string;
  headers: Record<string, string>;
  body?: string;
  expectedVersion?: number;
  createdAt: string;
  updatedAt: string;
  attempt: number;
  maxAttempts: number;
  state: QueueState;
  lastError?: string;
  conflict?: {
    status: 409 | 412;
    serverBody?: unknown;
    detectedAt: string;
  };
}

export interface QueueEnvelopeInput {
  url: string;
  method?: string;
  headers?: HeadersInit | Record<string, unknown>;
  body?: unknown;
  entityType: string;
  entityId?: string;
  action: string;
  expectedVersion?: number;
  operationId?: string;
  idempotencyKey?: string;
  maxAttempts?: number;
  now?: string;
}

export type QueueResponseDisposition = 'synced' | 'conflict' | 'rejected' | 'retry';

function randomOperationId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `offline-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function normalizeForFingerprint(value: unknown): unknown {
  if (typeof value === 'string') {
    try {
      return normalizeForFingerprint(JSON.parse(value));
    } catch {
      return value;
    }
  }
  if (Array.isArray(value)) return value.map(normalizeForFingerprint);
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, entry]) => [key, normalizeForFingerprint(entry)]),
    );
  }
  return value;
}

function stableSerialize(value: unknown): string {
  return JSON.stringify(normalizeForFingerprint(value));
}

async function sha256Hex(value: string): Promise<string> {
  if (typeof crypto !== 'undefined' && crypto.subtle) {
    const encoded = new TextEncoder().encode(value);
    const digest = await crypto.subtle.digest('SHA-256', encoded);
    return Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
  }
  // Browsers supported by GULA expose Web Crypto; this fallback keeps the
  // contract deterministic in restricted test environments without claiming
  // cryptographic strength.
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return `fallback-${(hash >>> 0).toString(16).padStart(8, '0')}`;
}

export function serializeQueueBody(body: unknown): string | undefined {
  if (body === undefined || body === null) return undefined;
  return typeof body === 'string' ? body : JSON.stringify(body);
}

export function parseQueueBody(body?: string): unknown {
  if (body === undefined) return undefined;
  try {
    return JSON.parse(body);
  } catch {
    return body;
  }
}

export async function createQueueEnvelope(input: QueueEnvelopeInput): Promise<OfflineQueueEnvelope> {
  const headerResult = sanitizeQueueHeaders(input.headers);
  const body = serializeQueueBody(input.body);
  const security = inspectQueueRecord({ headers: input.headers, body });
  if (headerResult.hadSensitiveHeader || !security.safe) {
    throw new Error(`Unsafe offline queue record: ${headerResult.hadSensitiveHeader ? 'sensitive-header' : security.reason}`);
  }

  if (!input.entityType.trim() || !input.action.trim()) {
    throw new Error('Offline queue entityType and action are required');
  }
  if (input.expectedVersion !== undefined && (!Number.isInteger(input.expectedVersion) || input.expectedVersion < 0)) {
    throw new Error('Offline queue expectedVersion must be a non-negative integer');
  }

  const operationId = input.operationId ?? randomOperationId();
  const idempotencyKey = input.idempotencyKey ?? operationId;
  const createdAt = input.now ?? new Date().toISOString();
  const fingerprintMaterial = stableSerialize({
    url: input.url,
    method: (input.method ?? 'POST').toUpperCase(),
    entityType: input.entityType,
    entityId: input.entityId,
    action: input.action,
    expectedVersion: input.expectedVersion,
    body: parseQueueBody(body),
  });

  return {
    schemaVersion: 1,
    operationId,
    idempotencyKey,
    requestFingerprint: await sha256Hex(fingerprintMaterial),
    entityType: input.entityType,
    entityId: input.entityId,
    action: input.action,
    url: input.url,
    method: (input.method ?? 'POST').toUpperCase(),
    headers: headerResult.headers,
    body,
    expectedVersion: input.expectedVersion,
    createdAt,
    updatedAt: createdAt,
    attempt: 0,
    maxAttempts: input.maxAttempts ?? 5,
    state: 'pending',
  };
}

export function buildQueueRequestInit(envelope: OfflineQueueEnvelope): RequestInit {
  const headers: Record<string, string> = {
    ...envelope.headers,
    'Idempotency-Key': envelope.idempotencyKey,
    'X-GULA-Operation-ID': envelope.operationId,
    'X-GULA-Request-Fingerprint': envelope.requestFingerprint,
  };
  if (envelope.expectedVersion !== undefined) {
    headers['If-Match'] = String(envelope.expectedVersion);
  }
  return {
    method: envelope.method,
    credentials: 'include',
    headers,
    body: envelope.body,
  };
}

export function classifyQueueResponse(status: number): QueueResponseDisposition {
  if (status >= 200 && status < 300) return 'synced';
  if (status === 409 || status === 412) return 'conflict';
  if (status >= 400 && status < 500) return 'rejected';
  return 'retry';
}

export function nextQueueEnvelopeState(
  envelope: OfflineQueueEnvelope,
  disposition: QueueResponseDisposition,
  error?: string,
  conflict?: OfflineQueueEnvelope['conflict'],
): OfflineQueueEnvelope {
  const now = new Date().toISOString();
  if (disposition === 'synced') return { ...envelope, state: 'synced', updatedAt: now, lastError: undefined, conflict: undefined };
  if (disposition === 'conflict') return { ...envelope, state: 'conflict', updatedAt: now, lastError: error, conflict };
  if (disposition === 'rejected') return { ...envelope, state: 'rejected', updatedAt: now, lastError: error };
  const attempt = envelope.attempt + 1;
  return {
    ...envelope,
    attempt,
    state: attempt >= envelope.maxAttempts ? 'failed' : 'pending',
    updatedAt: now,
    lastError: error,
  };
}
