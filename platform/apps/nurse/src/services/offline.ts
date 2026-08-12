import { openDB, type IDBPDatabase } from 'idb';
import type { OfflineQueueItem } from '@/utils/types';
import {
  createQueueEnvelope,
  inspectQueuePayload,
  nextQueueEnvelopeState,
  type OfflineQueueEnvelope,
} from '@gula/ui-platform';

const DB_NAME = 'gula-nurse-offline';
const DB_VERSION = 2;

let dbPromise: Promise<IDBPDatabase> | null = null;

function getDb(): Promise<IDBPDatabase> {
  if (!dbPromise) {
    dbPromise = openDB(DB_NAME, DB_VERSION, {
      upgrade(db) {
        if (!db.objectStoreNames.contains('queue')) {
          const store = db.createObjectStore('queue', { keyPath: 'id' });
          store.createIndex('synced', 'synced');
          store.createIndex('type', 'type');
        }
        if (!db.objectStoreNames.contains('cache')) {
          db.createObjectStore('cache', { keyPath: 'key' });
        }
        if (!db.objectStoreNames.contains('queue_rejections')) {
          db.createObjectStore('queue_rejections', { keyPath: 'id', autoIncrement: true });
        }
      },
    }).then(async (database) => {
      const pending = await database.getAll('queue');
      for (const item of pending) {
        const result = inspectQueuePayload(item);
        if (!result.safe) {
          await database.add('queue_rejections', {
            source: 'gula-nurse-offline.queue',
            requestId: item.id,
            reason: result.reason,
            rejectedAt: Date.now(),
          });
          await database.delete('queue', item.id);
        }
      }
      return database;
    });
  }
  return dbPromise;
}

export const offlineService = {
  enqueue: async (item: Omit<OfflineQueueItem, 'id' | 'createdAt' | 'synced'>) => {
    const db = await getDb();
    const result = inspectQueuePayload(item);
    if (!result.safe) {
      await db.add('queue_rejections', {
        source: 'gula-nurse-offline.queue',
        reason: result.reason,
        rejectedAt: Date.now(),
      });
      throw new Error('تم رفض تخزين عنصر غير متصل يحتوي بيانات اعتماد');
    }
    const envelope = await createQueueEnvelope({
      url: `/nurse/${item.type}`,
      method: 'POST',
      entityType: item.type,
      action: item.action,
      body: item.payload,
    });
    const entry: OfflineQueueItem = {
      ...item,
      id: crypto.randomUUID(),
      createdAt: envelope.createdAt,
      synced: false,
      schemaVersion: envelope.schemaVersion,
      operationId: envelope.operationId,
      idempotencyKey: envelope.idempotencyKey,
      requestFingerprint: envelope.requestFingerprint,
      state: envelope.state,
      attempt: envelope.attempt,
      maxAttempts: envelope.maxAttempts,
      updatedAt: envelope.updatedAt,
    };
    await db.add('queue', entry);
    return entry;
  },

  getPending: async () => {
    const db = await getDb();
    const index = db.transaction('queue').store.index('synced');
    return index.getAll(0);
  },

  getPendingCount: async () => {
    const items = await offlineService.getPending();
    return items.length;
  },

  markSynced: async (id: string) => {
    const db = await getDb();
    const tx = db.transaction('queue', 'readwrite');
    const item = await tx.store.get(id);
    if (item) {
      item.synced = true;
      item.state = 'synced';
      item.updatedAt = new Date().toISOString();
      await tx.store.put(item);
    }
    await tx.done;
  },

  clearSynced: async () => {
    const db = await getDb();
    const index = db.transaction('queue').store.index('synced');
    const syncedItems = await index.getAll(1);
    const tx = db.transaction('queue', 'readwrite');
    for (const item of syncedItems) {
      await tx.store.delete(item.id);
    }
    await tx.done;
  },

  cacheData: async (key: string, data: unknown) => {
    const db = await getDb();
    await db.put('cache', { key, data, timestamp: Date.now() });
  },

  getCachedData: async <T>(key: string): Promise<T | null> => {
    const db = await getDb();
    const entry = await db.get('cache', key);
    return entry?.data ?? null;
  },

  clearExpiredCache: async (maxAgeMs: number = 1000 * 60 * 60) => {
    const db = await getDb();
    const tx = db.transaction('cache', 'readwrite');
    let cursor = await tx.store.openCursor();
    const now = Date.now();
    while (cursor) {
      if (now - cursor.value.timestamp > maxAgeMs) {
        await cursor.delete();
      }
      cursor = await cursor.continue();
    }
    await tx.done;
  },

  syncAll: async (syncFn: (item: OfflineQueueItem) => Promise<void>) => {
    const pending = await offlineService.getPending();
    for (const item of pending) {
      const result = inspectQueuePayload(item);
      if (!result.safe) {
        const db = await getDb();
        await db.add('queue_rejections', {
          source: 'gula-nurse-offline.queue',
          requestId: item.id,
          reason: result.reason,
          rejectedAt: Date.now(),
        });
        await db.delete('queue', item.id);
        continue;
      }
      try {
        await syncFn(item);
        await offlineService.markSynced(item.id);
      } catch (error) {
        const database = await getDb();
        const current = await database.get('queue', item.id);
        if (current) {
          const next = nextQueueEnvelopeState(
            {
              schemaVersion: 1,
              operationId: current.operationId || current.id,
              idempotencyKey: current.idempotencyKey || current.operationId || current.id,
              requestFingerprint: current.requestFingerprint || 'legacy',
              entityType: current.type,
              entityId: typeof current.payload?.id === 'string' ? current.payload.id : undefined,
              action: current.action,
              url: `/nurse/${current.type}`,
              method: 'POST',
              headers: {},
              body: JSON.stringify(current.payload),
              createdAt: current.createdAt,
              updatedAt: current.updatedAt || current.createdAt,
              attempt: current.attempt || 0,
              maxAttempts: current.maxAttempts || 5,
              state: current.state || 'pending',
            } as OfflineQueueEnvelope,
            'retry',
            error instanceof Error ? error.message : 'sync-failed',
          );
          await database.put('queue', { ...current, ...next, id: current.id, payload: current.payload, synced: false });
        }
        console.error('[Offline] Sync failed for item:', item.id, error);
      }
    }
  },

  clearAll: async () => {
    const db = await getDb();
    await db.clear('queue');
    await db.clear('cache');
  },
};
