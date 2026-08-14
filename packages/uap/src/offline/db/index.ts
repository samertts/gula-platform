import type { OfflineEntry } from '../types';

interface StorageBackend {
  get<T>(collection: string, id: string): Promise<OfflineEntry<T> | null>;
  getAll<T>(collection: string): Promise<OfflineEntry<T>[]>;
  put<T>(entry: OfflineEntry<T>): Promise<void>;
  delete(collection: string, id: string): Promise<void>;
  clear(collection?: string): Promise<void>;
  query<T>(collection: string, predicate: (entry: OfflineEntry<T>) => boolean): Promise<OfflineEntry<T>[]>;
  count(collection: string): Promise<number>;
  getSize(): Promise<number>;
}

function encrypt(text: string, key: string): string {
  return btoa(
    text.split('').map((c, i) => String.fromCharCode(c.charCodeAt(0) ^ key.charCodeAt(i % key.length))).join('')
  );
}

function decrypt(text: string, key: string): string {
  return encrypt(text, key);
}

class IndexedDBBackend implements StorageBackend {
  private dbName: string;
  private dbVersion: number;
  private db: IDBDatabase | null = null;
  private encryptionKey: string;

  constructor(dbName = 'gula-offline', version = 1, encryptionKey = 'gula-default-key') {
    this.dbName = dbName;
    this.dbVersion = version;
    this.encryptionKey = encryptionKey;
  }

  private async openDB(): Promise<IDBDatabase> {
    if (this.db) return this.db;
    return new Promise((resolve, reject) => {
      const req = indexedDB.open(this.dbName, this.dbVersion);
      req.onupgradeneeded = () => {
        const db = req.result;
        if (!db.objectStoreNames.contains('collections')) {
          const store = db.createObjectStore('collections', { keyPath: 'id' });
          store.createIndex('collection', 'collection', { unique: false });
          store.createIndex('updatedAt', 'updatedAt', { unique: false });
        }
      };
      req.onsuccess = () => {
        this.db = req.result;
        resolve(req.result);
      };
      req.onerror = () => reject(req.error);
    });
  }

  private serialize<T>(entry: OfflineEntry<T>): unknown {
    return {
      ...entry,
      data: encrypt(JSON.stringify(entry.data), this.encryptionKey),
    };
  }

  private deserialize<T>(raw: any): OfflineEntry<T> {
    return {
      ...raw,
      data: JSON.parse(decrypt(raw.data, this.encryptionKey)) as T,
    };
  }

  async get<T>(collection: string, id: string): Promise<OfflineEntry<T> | null> {
    const db = await this.openDB();
    const tx = db.transaction('collections', 'readonly');
    const store = tx.objectStore('collections');
    const index = store.index('collection');
    return new Promise((resolve, reject) => {
      const req = index.openCursor(IDBKeyRange.only(collection));
      req.onsuccess = () => {
        const cursor = req.result;
        if (!cursor) { resolve(null); return; }
        const entry = cursor.value;
        if (entry.id === id) {
          resolve(this.deserialize(entry));
        } else {
          cursor.continue();
        }
      };
      req.onerror = () => reject(req.error);
    });
  }

  async getAll<T>(collection: string): Promise<OfflineEntry<T>[]> {
    const db = await this.openDB();
    const tx = db.transaction('collections', 'readonly');
    const store = tx.objectStore('collections');
    const index = store.index('collection');
    return new Promise((resolve, reject) => {
      const results: OfflineEntry<T>[] = [];
      const req = index.openCursor(IDBKeyRange.only(collection));
      req.onsuccess = () => {
        const cursor = req.result;
        if (cursor) {
          results.push(this.deserialize(cursor.value));
          cursor.continue();
        } else {
          resolve(results);
        }
      };
      req.onerror = () => reject(req.error);
    });
  }

  async put<T>(entry: OfflineEntry<T>): Promise<void> {
    const db = await this.openDB();
    const tx = db.transaction('collections', 'readwrite');
    const store = tx.objectStore('collections');
    return new Promise((resolve, reject) => {
      const req = store.put(this.serialize(entry));
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
    });
  }

  async delete(collection: string, id: string): Promise<void> {
    const entry = await this.get(collection, id);
    if (!entry) return;
    const db = await this.openDB();
    const tx = db.transaction('collections', 'readwrite');
    const store = tx.objectStore('collections');
    return new Promise((resolve, reject) => {
      const req = store.delete(entry.id);
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
    });
  }

  async clear(collection?: string): Promise<void> {
    const db = await this.openDB();
    const tx = db.transaction('collections', 'readwrite');
    const store = tx.objectStore('collections');
    if (collection) {
      const index = store.index('collection');
      const req = index.openCursor(IDBKeyRange.only(collection));
      req.onsuccess = () => {
        const cursor = req.result;
        if (cursor) {
          cursor.delete();
          cursor.continue();
        }
      };
    } else {
      store.clear();
    }
    return new Promise((resolve) => { tx.oncomplete = () => resolve(); });
  }

  async query<T>(collection: string, predicate: (entry: OfflineEntry<T>) => boolean): Promise<OfflineEntry<T>[]> {
    const all = await this.getAll<T>(collection);
    return all.filter(predicate);
  }

  async count(collection: string): Promise<number> {
    const all = await this.getAll(collection);
    return all.length;
  }

  async getSize(): Promise<number> {
    const db = await this.openDB();
    const tx = db.transaction('collections', 'readonly');
    const store = tx.objectStore('collections');
    return new Promise((resolve) => {
      const req = store.count();
      req.onsuccess = () => resolve(req.result);
    });
  }
}

export type { StorageBackend };
export { IndexedDBBackend };

let _backend: StorageBackend | null = null;

export const getStorage = (): StorageBackend => {
  if (!_backend) {
    _backend = new IndexedDBBackend();
  }
  return _backend;
};

export const setStorage = (backend: StorageBackend) => {
  _backend = backend;
};
