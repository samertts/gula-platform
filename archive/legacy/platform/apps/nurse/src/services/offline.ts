import { openDB, type IDBPDatabase } from 'idb';
import type { OfflineQueueItem } from '@/utils/types';

const DB_NAME = 'gula-nurse-offline';
const DB_VERSION = 1;

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
      },
    });
  }
  return dbPromise;
}

export const offlineService = {
  enqueue: async (item: Omit<OfflineQueueItem, 'id' | 'createdAt' | 'synced'>) => {
    const db = await getDb();
    const entry: OfflineQueueItem = {
      ...item,
      id: crypto.randomUUID(),
      createdAt: new Date().toISOString(),
      synced: false,
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
      try {
        await syncFn(item);
        await offlineService.markSynced(item.id);
      } catch (error) {
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
