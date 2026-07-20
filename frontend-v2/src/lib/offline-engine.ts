import { openDB, IDBPDatabase, DBSchema } from 'idb';

const DB_NAME = 'gula-offline';
const DB_VERSION = 3;

interface SyncQueueItem {
  id: string;
  operation: 'create' | 'update' | 'delete';
  collection: string;
  documentId: string;
  payload: unknown;
  timestamp: number;
  retryCount: number;
  maxRetries: number;
  lastError?: string;
}

interface CachedDocument {
  id: string;
  collection: string;
  data: unknown;
  syncedAt: number;
  checksum: string;
  version: number;
}

interface SyncLog {
  id: string;
  type: 'push' | 'pull' | 'conflict' | 'error';
  collection: string;
  documentId: string;
  timestamp: number;
  details: string;
}

interface GulaOfflineDB extends DBSchema {
  patients: {
    key: string;
    value: CachedDocument;
    indexes: { 'by-synced': number; 'by-collection': string };
  };
  orders: {
    key: string;
    value: CachedDocument;
    indexes: { 'by-synced': number; 'by-collection': string };
  };
  samples: {
    key: string;
    value: CachedDocument;
    indexes: { 'by-synced': number; 'by-collection': string };
  };
  results: {
    key: string;
    value: CachedDocument;
    indexes: { 'by-synced': number; 'by-collection': string };
  };
  sync_queue: {
    key: string;
    value: SyncQueueItem;
    indexes: { 'by-timestamp': number; 'by-retry': number };
  };
  sync_log: {
    key: string;
    value: SyncLog;
    indexes: { 'by-timestamp': number };
  };
  metadata: {
    key: string;
    value: { key: string; value: string };
  };
}

let dbInstance: IDBPDatabase<GulaOfflineDB> | null = null;

async function getDB(): Promise<IDBPDatabase<GulaOfflineDB>> {
  if (dbInstance) return dbInstance;
  dbInstance = await openDB<GulaOfflineDB>(DB_NAME, DB_VERSION, {
    upgrade(db, oldVersion) {
      if (oldVersion < 1) {
        const patients = db.createObjectStore('patients', { keyPath: 'id' });
        patients.createIndex('by-synced', 'syncedAt');
        patients.createIndex('by-collection', 'collection');

        const orders = db.createObjectStore('orders', { keyPath: 'id' });
        orders.createIndex('by-synced', 'syncedAt');
        orders.createIndex('by-collection', 'collection');

        const samples = db.createObjectStore('samples', { keyPath: 'id' });
        samples.createIndex('by-synced', 'syncedAt');
        samples.createIndex('by-collection', 'collection');

        const results = db.createObjectStore('results', { keyPath: 'id' });
        results.createIndex('by-synced', 'syncedAt');
        results.createIndex('by-collection', 'collection');

        db.createObjectStore('sync_queue', { keyPath: 'id' });
        db.createObjectStore('sync_log', { keyPath: 'id' });
        db.createObjectStore('metadata', { keyPath: 'key' });
      }
      if (oldVersion < 2) {
        const queue: any = db.transaction('sync_queue').objectStore('sync_queue');
        queue.createIndex('by-timestamp', 'timestamp');
        queue.createIndex('by-retry', 'retryCount');
        const log: any = db.transaction('sync_log').objectStore('sync_log');
        log.createIndex('by-timestamp', 'timestamp');
      }
      if (oldVersion < 3) {
        const classes: string[] = ['patients', 'orders', 'samples', 'results'];
        for (const cls of classes) {
          if (!db.objectStoreNames.contains(cls as any)) {
            const store: any = db.createObjectStore(cls as any, { keyPath: 'id' });
            store.createIndex('by-synced', 'syncedAt');
            store.createIndex('by-collection', 'collection');
          }
        }
      }
    },
  });
  return dbInstance;
}

function computeChecksum(data: unknown): string {
  const str = JSON.stringify(data);
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash |= 0;
  }
  return Math.abs(hash).toString(36);
}

function compress(data: string): string {
  try {
    if (typeof btoa === 'undefined') return data;
    const enc = new TextEncoder();
    const buf = enc.encode(data);
    const compressed = [];
    let i = 0;
    while (i < buf.length) {
      let count = 1;
      while (i + count < buf.length && buf[i + count] === buf[i] && count < 255) {
        count++;
      }
      compressed.push(count, buf[i]);
      i += count;
    }
    return btoa(String.fromCharCode(...compressed));
  } catch {
    return data;
  }
}

function decompress(data: string): string {
  try {
    if (typeof atob === 'undefined') return data;
    const binary = atob(data);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    const result: number[] = [];
    for (let i = 0; i < bytes.length; i += 2) {
      const count = bytes[i];
      const value = bytes[i + 1];
      for (let j = 0; j < count; j++) result.push(value);
    }
    return new TextDecoder().decode(new Uint8Array(result));
  } catch {
    return data;
  }
}

async function isCompressed(data: unknown): Promise<boolean> {
  if (typeof data !== 'string') return false;
  const size = new Blob([data]).size;
  return size > 10240;
}

export class OfflineEngine {
  private static instance: OfflineEngine;
  private pendingSync = false;
  private syncCallbacks: Array<(status: SyncStatus) => void> = [];

  static getInstance(): OfflineEngine {
    if (!this.instance) this.instance = new OfflineEngine();
    return this.instance;
  }

  onSyncStatusChange(cb: (status: SyncStatus) => void): () => void {
    this.syncCallbacks.push(cb);
    return () => {
      this.syncCallbacks = this.syncCallbacks.filter(c => c !== cb);
    };
  }

  private notify(status: SyncStatus): void {
    for (const cb of this.syncCallbacks) cb(status);
  }

  async cacheDocument(
    collection: 'patients' | 'orders' | 'samples' | 'results',
    id: string,
    data: unknown,
  ): Promise<void> {
    const db = await getDB();
    const checksum = computeChecksum(data);
    const existing = await db.get(collection, id);
    await db.put(collection, {
      id,
      collection,
      data,
      syncedAt: Date.now(),
      checksum,
      version: (existing?.version ?? 0) + 1,
    });
  }

  async getDocument(collection: 'patients' | 'orders' | 'samples' | 'results', id: string): Promise<CachedDocument | undefined> {
    const db = await getDB();
    return db.get(collection, id);
  }

  async getAllDocuments(collection: 'patients' | 'orders' | 'samples' | 'results'): Promise<CachedDocument[]> {
    const db = await getDB();
    return db.getAll(collection);
  }

  async deleteDocument(collection: 'patients' | 'orders' | 'samples' | 'results', id: string): Promise<void> {
    const db = await getDB();
    await db.delete(collection, id);
  }

  async enqueue(operation: SyncQueueItem['operation'], collection: string, documentId: string, payload: unknown): Promise<string> {
    const db = await getDB();
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
    const item: SyncQueueItem = {
      id,
      operation,
      collection,
      documentId,
      payload,
      timestamp: Date.now(),
      retryCount: 0,
      maxRetries: 5,
    };
    await db.add('sync_queue', item);
    await this.log('push', collection, documentId, `Queued ${operation}`);
    return id;
  }

  async getPendingOperations(): Promise<SyncQueueItem[]> {
    const db = await getDB();
    const all = await db.getAll('sync_queue');
    return all.sort((a, b) => a.timestamp - b.timestamp);
  }

  async getPendingCount(): Promise<number> {
    const db = await getDB();
    return (await db.getAllKeys('sync_queue')).length;
  }

  async processQueue(syncFn: (item: SyncQueueItem) => Promise<boolean>): Promise<SyncResult> {
    if (this.pendingSync) return { success: 0, failed: 0, skipped: 0, conflicts: 0 };
    this.pendingSync = true;
    this.notify({ status: 'syncing', pending: await this.getPendingCount(), lastSync: Date.now() });

    const result: SyncResult = { success: 0, failed: 0, skipped: 0, conflicts: 0 };
    const db = await getDB();
    const queue = await db.getAll('sync_queue');
    const sorted = queue.sort((a, b) => a.timestamp - b.timestamp);

    for (const item of sorted) {
      const backoff = Math.pow(2, item.retryCount) * 1000;
      if (item.retryCount > 0 && Date.now() - item.timestamp < backoff) {
        result.skipped++;
        continue;
      }
      try {
        const success = await syncFn(item);
        if (success) {
          await db.delete('sync_queue', item.id);
          result.success++;
          await this.log('push', item.collection, item.documentId, `Processed ${item.operation}`);
        } else {
          result.conflicts++;
          await this.log('conflict', item.collection, item.documentId, `Conflict on ${item.operation}`);
        }
      } catch (err) {
        const updated: SyncQueueItem = {
          ...item,
          retryCount: item.retryCount + 1,
          lastError: err instanceof Error ? err.message : String(err),
        };
        if (updated.retryCount >= updated.maxRetries) {
          await db.delete('sync_queue', item.id);
          result.failed++;
          await this.log('error', item.collection, item.documentId, `Failed after ${item.maxRetries} retries: ${updated.lastError}`);
        } else {
          await db.put('sync_queue', updated);
          result.failed++;
        }
      }
    }

    this.pendingSync = false;
    this.notify({ status: 'idle', pending: await this.getPendingCount(), lastSync: Date.now() });
    return result;
  }

  private async log(type: SyncLog['type'], collection: string, documentId: string, details: string): Promise<void> {
    const db = await getDB();
    await db.add('sync_log', {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
      type,
      collection,
      documentId,
      timestamp: Date.now(),
      details,
    });
  }

  async getSyncLogs(limit = 50): Promise<SyncLog[]> {
    const db = await getDB();
    const logs = await db.getAll('sync_log');
    return logs.sort((a, b) => b.timestamp - a.timestamp).slice(0, limit);
  }

  async clearSyncLogs(): Promise<void> {
    const db = await getDB();
    await db.clear('sync_log');
  }

  async purgeOldData(maxAgeMs = 30 * 24 * 60 * 60 * 1000): Promise<number> {
    const db = await getDB();
    const cutoff = Date.now() - maxAgeMs;
    let purged = 0;
    for (const store of ['patients', 'orders', 'samples', 'results'] as const) {
      const docs = await db.getAll(store);
      for (const doc of docs) {
        if (doc.syncedAt < cutoff) {
          await db.delete(store, doc.id);
          purged++;
        }
      }
    }
    return purged;
  }

  async getStorageEstimate(): Promise<{ used: number; quota: number; percentage: number }> {
    if ('storage' in navigator && 'estimate' in navigator.storage) {
      const est = await navigator.storage.estimate();
      const used = (est as unknown as { used?: number }).used ?? est.usage ?? 0;
      const quota = est.quota ?? 0;
      return {
        used,
        quota,
        percentage: quota ? (used / quota) * 100 : 0,
      };
    }
    return { used: 0, quota: 0, percentage: 0 };
  }
}

export interface SyncStatus {
  status: 'idle' | 'syncing' | 'error' | 'offline';
  pending: number;
  lastSync: number;
}

export interface SyncResult {
  success: number;
  failed: number;
  skipped: number;
  conflicts: number;
}

export type { SyncQueueItem, CachedDocument, SyncLog };
