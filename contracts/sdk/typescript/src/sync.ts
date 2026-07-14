const STORAGE_KEY = 'gula_sync_queue';
const MAX_QUEUE_SIZE = 1000;

export interface SyncMutation {
  id: string;
  type: string;
  url: string;
  method: 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  data?: unknown;
  idempotencyKey?: string;
  createdAt: string;
  retryCount: number;
  maxRetries: number;
}

export type SyncConflictStrategy = 'remote-wins' | 'local-wins' | 'manual';

export interface SyncOptions {
  maxRetries?: number;
  conflictStrategy?: SyncConflictStrategy;
  onProcess?: (mutation: SyncMutation) => Promise<void>;
  onConflict?: (mutation: SyncMutation, error: Error) => SyncConflictStrategy;
  onComplete?: (mutation: SyncMutation) => void;
  onError?: (mutation: SyncMutation, error: Error) => void;
}

type StorageBackend = 'localStorage' | 'indexedDB' | 'memory';

function isOnline(): boolean {
  if (typeof navigator === 'undefined') return true;
  return navigator.onLine;
}

export class SyncEngine {
  private queue: SyncMutation[] = [];
  private processing = false;
  private storageBackend: StorageBackend;
  private options: Required<SyncOptions>;
  private dbName = 'gula-sync';
  private storeName = 'mutations';
  private listeners: Array<(online: boolean) => void> = [];

  constructor(options: SyncOptions = {}) {
    this.options = {
      maxRetries: options.maxRetries ?? 5,
      conflictStrategy: options.conflictStrategy ?? 'remote-wins',
      onProcess: options.onProcess ?? (async () => {}),
      onConflict: options.onConflict ?? (() => 'remote-wins'),
      onComplete: options.onComplete ?? (() => {}),
      onError: options.onError ?? (() => {}),
    };
    this.storageBackend = this.detectStorage();
    this.loadQueue();

    if (typeof window !== 'undefined') {
      window.addEventListener('online', () => this.handleOnline());
      window.addEventListener('offline', () => this.notifyListeners(false));
    }
  }

  private detectStorage(): StorageBackend {
    if (typeof localStorage !== 'undefined') {
      try {
        localStorage.setItem('__test', '1');
        localStorage.removeItem('__test');
        return 'localStorage';
      } catch {
      }
    }
    if (typeof indexedDB !== 'undefined') {
      return 'indexedDB';
    }
    return 'memory';
  }

  private async loadQueue(): Promise<void> {
    if (this.storageBackend === 'localStorage') {
      try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (raw) {
          this.queue = JSON.parse(raw);
        }
      } catch {
        this.queue = [];
      }
    } else if (this.storageBackend === 'indexedDB') {
      this.queue = await this.indexedDBGetAll();
    }
  }

  private async saveQueue(): Promise<void> {
    if (this.queue.length > MAX_QUEUE_SIZE) {
      this.queue = this.queue.slice(-MAX_QUEUE_SIZE);
    }
    if (this.storageBackend === 'localStorage') {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(this.queue));
      } catch {
        if (this.queue.length > 100) {
          this.queue = this.queue.slice(-100);
          localStorage.setItem(STORAGE_KEY, JSON.stringify(this.queue));
        }
      }
    } else if (this.storageBackend === 'indexedDB') {
      await this.indexedDBPutAll(this.queue);
    }
  }

  private async indexedDBGetAll(): Promise<SyncMutation[]> {
    try {
      const db = await this.openIndexedDB();
      const tx = db.transaction(this.storeName, 'readonly');
      const store = tx.objectStore(this.storeName);
      const items = await new Promise<SyncMutation[]>((resolve, reject) => {
        const req = store.getAll();
        req.onsuccess = () => resolve(req.result ?? []);
        req.onerror = () => reject(req.error);
      });
      db.close();
      return items;
    } catch {
      return [];
    }
  }

  private async indexedDBPutAll(items: SyncMutation[]): Promise<void> {
    try {
      const db = await this.openIndexedDB();
      const tx = db.transaction(this.storeName, 'readwrite');
      const store = tx.objectStore(this.storeName);
      store.clear();
      for (const item of items) {
        store.put(item);
      }
      await new Promise<void>((resolve, reject) => {
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error);
      });
      db.close();
    } catch {
    }
  }

  private openIndexedDB(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
      const req = indexedDB.open(this.dbName, 1);
      req.onupgradeneeded = () => {
        const db = req.result;
        if (!db.objectStoreNames.contains(this.storeName)) {
          db.createObjectStore(this.storeName, { keyPath: 'id' });
        }
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }

  private generateId(): string {
    const ts = Date.now().toString(36);
    const rand = Math.random().toString(36).substring(2, 10);
    return `${ts}-${rand}`;
  }

  enqueue(mutation: Omit<SyncMutation, 'id' | 'createdAt' | 'retryCount'>): string {
    const id = this.generateId();
    this.queue.push({
      ...mutation,
      id,
      createdAt: new Date().toISOString(),
      retryCount: 0,
    });
    this.saveQueue();
    if (isOnline()) {
      this.processQueue();
    }
    return id;
  }

  remove(id: string): void {
    this.queue = this.queue.filter((m) => m.id !== id);
    this.saveQueue();
  }

  clear(): void {
    this.queue = [];
    this.saveQueue();
  }

  getQueue(): SyncMutation[] {
    return [...this.queue];
  }

  getQueueSize(): number {
    return this.queue.length;
  }

  isOnline(): boolean {
    return isOnline();
  }

  onOnlineChange(listener: (online: boolean) => void): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== listener);
    };
  }

  private notifyListeners(online: boolean): void {
    for (const listener of this.listeners) {
      listener(online);
    }
  }

  private async handleOnline(): Promise<void> {
    this.notifyListeners(true);
    await this.processQueue();
  }

  async processQueue(): Promise<void> {
    if (this.processing || !isOnline() || this.queue.length === 0) {
      return;
    }
    this.processing = true;

    const batch = [...this.queue];
    for (const mutation of batch) {
      if (!isOnline()) break;

      try {
        await this.options.onProcess(mutation);
        this.options.onComplete(mutation);
        this.remove(mutation.id);
      } catch (error: unknown) {
        const err = error instanceof Error ? error : new Error(String(error));

        if (err.message.includes('409') || err.message.includes('CONFLICT')) {
          const strategy = this.options.onConflict(mutation, err);
          if (strategy === 'local-wins') {
            mutation.retryCount += 1;
            if (mutation.retryCount >= this.options.maxRetries) {
              this.options.onError(mutation, err);
              this.remove(mutation.id);
            } else {
              await this.saveQueue();
            }
          } else {
            this.remove(mutation.id);
          }
        } else if (err.message.includes('401') || err.message.includes('403')) {
          this.options.onError(mutation, err);
          this.remove(mutation.id);
        } else {
          mutation.retryCount += 1;
          if (mutation.retryCount >= this.options.maxRetries) {
            this.options.onError(mutation, err);
            this.remove(mutation.id);
          } else {
            const delay = Math.min(1000 * Math.pow(2, mutation.retryCount), 30_000);
            await new Promise((r) => setTimeout(r, delay));
            await this.saveQueue();
          }
        }
      }
    }

    this.processing = false;
  }
}
