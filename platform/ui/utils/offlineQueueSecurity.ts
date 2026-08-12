export interface SanitizedHeaders {
  headers: Record<string, string>;
  hadSensitiveHeader: boolean;
}

export interface QueueSecurityCheck {
  safe: boolean;
  reason?: 'sensitive-header' | 'sensitive-payload';
}

const SENSITIVE_KEY_PARTS = [
  'authorization',
  'accesstoken',
  'refreshtoken',
  'idtoken',
  'jwttoken',
  'bearer',
  'password',
  'secret',
  'apikey',
  'cookie',
  'session',
];

function normalizedKey(key: string): string {
  return key.toLowerCase().replace(/[^a-z0-9]/g, '');
}

export function isSensitiveQueueKey(key: string): boolean {
  const normalized = normalizedKey(key);
  return SENSITIVE_KEY_PARTS.includes(normalized)
    || normalized === 'token'
    || normalized.endsWith('token')
    || normalized.endsWith('password')
    || normalized.endsWith('secret')
    || normalized.endsWith('apikey')
    || normalized.endsWith('authorization')
    || normalized.endsWith('cookie');
}

export function sanitizeQueueHeaders(
  headers: HeadersInit | Record<string, unknown> | undefined,
): SanitizedHeaders {
  const output: Record<string, string> = {};
  let hadSensitiveHeader = false;

  if (!headers) return { headers: output, hadSensitiveHeader };

  const entries = typeof Headers !== 'undefined' && headers instanceof Headers
    ? Array.from(headers.entries())
    : Array.isArray(headers)
      ? headers
      : Object.entries(headers);

  for (const [key, value] of entries) {
    if (isSensitiveQueueKey(key)) {
      hadSensitiveHeader = true;
      continue;
    }
    if (value !== undefined && value !== null) {
      output[key] = String(value);
    }
  }

  return { headers: output, hadSensitiveHeader };
}

function hasSensitivePayloadValue(value: unknown, seen: Set<unknown>): boolean {
  if (value === null || value === undefined) return false;
  if (typeof value === 'string') {
    return /\bBearer\s+[A-Za-z0-9._-]+/i.test(value)
      || /(?:access|refresh|id|jwt)[_-]?token\s*[:=]/i.test(value);
  }
  if (typeof value !== 'object') return false;
  if (seen.has(value)) return false;
  seen.add(value);

  if (Array.isArray(value)) {
    return value.some((entry) => hasSensitivePayloadValue(entry, seen));
  }

  return Object.entries(value as Record<string, unknown>).some(([key, entry]) =>
    isSensitiveQueueKey(key) || hasSensitivePayloadValue(entry, seen),
  );
}

export function inspectQueuePayload(payload: unknown): QueueSecurityCheck {
  if (typeof payload === 'string') {
    try {
      return inspectQueuePayload(JSON.parse(payload));
    } catch {
      return hasSensitivePayloadValue(payload, new Set())
        ? { safe: false, reason: 'sensitive-payload' }
        : { safe: true };
    }
  }

  return hasSensitivePayloadValue(payload, new Set())
    ? { safe: false, reason: 'sensitive-payload' }
    : { safe: true };
}

export function inspectQueueRecord(record: {
  headers?: HeadersInit | Record<string, unknown>;
  body?: unknown;
  payload?: unknown;
}): QueueSecurityCheck {
  const headerResult = sanitizeQueueHeaders(record.headers);
  if (headerResult.hadSensitiveHeader) {
    return { safe: false, reason: 'sensitive-header' };
  }

  return inspectQueuePayload(record.body ?? record.payload);
}

/**
 * Removes the legacy Workbox Background Sync database. It contains only
 * generated request queues, not application caches or clinical stores.
 */
export async function purgeLegacyWorkboxQueue(): Promise<boolean> {
  if (typeof indexedDB === 'undefined') return false;

  return new Promise((resolve) => {
    const request = indexedDB.deleteDatabase('workbox-background-sync');
    request.onsuccess = () => resolve(true);
    request.onerror = () => resolve(false);
    request.onblocked = () => resolve(false);
  });
}
