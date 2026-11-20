import {
  GulsFailure,
  type InstalledPackRecord,
  type StagingRecord,
  type StorageDriver,
} from "./types";

const DATABASE_NAME = "guls-offline";
const DATABASE_VERSION = 1;
export const ACTIVE_STORE = "active";
export const PREVIOUS_STORE = "previous";
export const STAGING_STORE = "staging";
export const META_STORE = "meta";

function request<T>(
  source: IDBObjectStore,
  operation: () => IDBRequest<T>,
): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const handle = operation();
    handle.onsuccess = () => resolve(handle.result);
    handle.onerror = () =>
      reject(handle.error ?? new Error("IndexedDB request failed"));
    void source;
  });
}

function transactionDone(transaction: IDBTransaction): Promise<void> {
  return new Promise<void>((resolve, reject) => {
    transaction.oncomplete = () => resolve();
    transaction.onabort = () =>
      reject(transaction.error ?? new Error("IndexedDB transaction aborted"));
    transaction.onerror = () =>
      reject(transaction.error ?? new Error("IndexedDB transaction failed"));
  });
}

/** Native IndexedDB driver. No third-party storage dependency. */
export class IndexedDbPackStorage implements StorageDriver {
  private databasePromise: Promise<IDBDatabase> | undefined;

  constructor(
    private readonly factory: IDBFactory | undefined = typeof indexedDB ===
    "undefined"
      ? undefined
      : indexedDB,
  ) {}

  private open(): Promise<IDBDatabase> {
    if (!this.factory) throw new GulsFailure("GULS_PACK_UNSUPPORTED");
    if (!this.databasePromise) {
      this.databasePromise = new Promise<IDBDatabase>((resolve, reject) => {
        const open = this.factory!.open(DATABASE_NAME, DATABASE_VERSION);
        open.onupgradeneeded = () => {
          const database = open.result;
          for (const name of [
            ACTIVE_STORE,
            PREVIOUS_STORE,
            STAGING_STORE,
            META_STORE,
          ]) {
            const keyPath =
              name === STAGING_STORE
                ? "downloadId"
                : name === META_STORE
                  ? "key"
                  : "languageId";
            if (!database.objectStoreNames.contains(name))
              database.createObjectStore(name, { keyPath });
          }
        };
        open.onsuccess = () => resolve(open.result);
        open.onerror = () =>
          reject(
            open.error ?? new Error("Unable to open GULS offline database"),
          );
        open.onblocked = () =>
          reject(new Error("GULS offline database upgrade blocked"));
      });
    }
    return this.databasePromise;
  }

  private async read<T>(
    storeName: string,
    key: string,
  ): Promise<T | undefined> {
    const database = await this.open();
    const transaction = database.transaction(storeName, "readonly");
    const value = await request<T | undefined>(
      transaction.objectStore(storeName),
      () =>
        transaction.objectStore(storeName).get(key) as IDBRequest<
          T | undefined
        >,
    );
    return value;
  }

  getActive(languageId: string): Promise<InstalledPackRecord | undefined> {
    return this.read<InstalledPackRecord>(ACTIVE_STORE, languageId);
  }

  getPrevious(languageId: string): Promise<InstalledPackRecord | undefined> {
    return this.read<InstalledPackRecord>(PREVIOUS_STORE, languageId);
  }

  getStaging(downloadId: string): Promise<StagingRecord | undefined> {
    return this.read<StagingRecord>(STAGING_STORE, downloadId);
  }

  getMeta(key: string): Promise<string | undefined> {
    return this.read<string>(META_STORE, key);
  }

  async listReady(): Promise<string[]> {
    const database = await this.open();
    const transaction = database.transaction(ACTIVE_STORE, "readonly");
    const keys = await request<IDBValidKey[]>(
      transaction.objectStore(ACTIVE_STORE),
      () => transaction.objectStore(ACTIVE_STORE).getAllKeys(),
    );
    const ready: string[] = [];
    for (const key of keys) {
      const state = await this.getMeta(`state.${String(key)}`);
      if (state !== "DISABLED" && state !== "ROLLBACK_REQUIRED")
        ready.push(String(key));
    }
    return ready;
  }

  async putStaging(record: StagingRecord): Promise<void> {
    const database = await this.open();
    const transaction = database.transaction(STAGING_STORE, "readwrite");
    transaction.objectStore(STAGING_STORE).put(record);
    await transactionDone(transaction);
  }

  async deleteStaging(downloadId: string): Promise<void> {
    const database = await this.open();
    const transaction = database.transaction(STAGING_STORE, "readwrite");
    transaction.objectStore(STAGING_STORE).delete(downloadId);
    await transactionDone(transaction);
  }

  async setMeta(key: string, value: string): Promise<void> {
    const database = await this.open();
    const transaction = database.transaction(META_STORE, "readwrite");
    transaction.objectStore(META_STORE).put({ key, value });
    await transactionDone(transaction);
  }

  /** Atomically replace the active record and keep the previous valid version. */
  async activate(record: InstalledPackRecord): Promise<void> {
    const database = await this.open();
    const transaction = database.transaction(
      [ACTIVE_STORE, PREVIOUS_STORE, META_STORE],
      "readwrite",
    );
    const active = transaction.objectStore(ACTIVE_STORE);
    const previous = transaction.objectStore(PREVIOUS_STORE);
    const meta = transaction.objectStore(META_STORE);
    const old = await request<InstalledPackRecord | undefined>(
      active,
      () =>
        active.get(record.languageId) as IDBRequest<
          InstalledPackRecord | undefined
        >,
    );
    if (old && old.packVersion !== record.packVersion) previous.put(old);
    active.put(record);
    meta.put({ key: `state.${record.languageId}`, value: "READY" });
    meta.put({
      key: `activatedAt.${record.languageId}`,
      value: record.installedAt,
    });
    await transactionDone(transaction);
  }

  /** Restore the previous valid version in one transaction. */
  async rollback(languageId: string): Promise<boolean> {
    const database = await this.open();
    const transaction = database.transaction(
      [ACTIVE_STORE, PREVIOUS_STORE, META_STORE],
      "readwrite",
    );
    const active = transaction.objectStore(ACTIVE_STORE);
    const previous = transaction.objectStore(PREVIOUS_STORE);
    const meta = transaction.objectStore(META_STORE);
    const old = await request<InstalledPackRecord | undefined>(
      previous,
      () =>
        previous.get(languageId) as IDBRequest<InstalledPackRecord | undefined>,
    );
    if (!old) {
      meta.put({ key: `state.${languageId}`, value: "ROLLBACK_REQUIRED" });
      await transactionDone(transaction);
      return false;
    }
    active.put(old);
    previous.delete(languageId);
    meta.put({ key: `state.${languageId}`, value: "READY" });
    await transactionDone(transaction);
    return true;
  }

  async disable(languageId: string): Promise<void> {
    await this.setMeta(`state.${languageId}`, "DISABLED");
  }
}

/** In-memory driver for tests and restricted browsers. Not durable across restarts. */
export class MemoryPackStorage implements StorageDriver {
  readonly active = new Map<string, InstalledPackRecord>();
  readonly previous = new Map<string, InstalledPackRecord>();
  readonly staging = new Map<string, StagingRecord>();
  readonly meta = new Map<string, string>();

  getActive(languageId: string): Promise<InstalledPackRecord | undefined> {
    return Promise.resolve(this.active.get(languageId));
  }

  getPrevious(languageId: string): Promise<InstalledPackRecord | undefined> {
    return Promise.resolve(this.previous.get(languageId));
  }

  getStaging(downloadId: string): Promise<StagingRecord | undefined> {
    return Promise.resolve(this.staging.get(downloadId));
  }

  putStaging(record: StagingRecord): Promise<void> {
    this.staging.set(record.downloadId, record);
    return Promise.resolve();
  }

  deleteStaging(downloadId: string): Promise<void> {
    this.staging.delete(downloadId);
    return Promise.resolve();
  }

  getMeta(key: string): Promise<string | undefined> {
    return Promise.resolve(this.meta.get(key));
  }

  setMeta(key: string, value: string): Promise<void> {
    this.meta.set(key, value);
    return Promise.resolve();
  }

  async listReady(): Promise<string[]> {
    const result: string[] = [];
    for (const languageId of this.active.keys()) {
      const state = await this.getMeta(`state.${languageId}`);
      if (state !== "DISABLED" && state !== "ROLLBACK_REQUIRED")
        result.push(languageId);
    }
    return result;
  }

  async activate(record: InstalledPackRecord): Promise<void> {
    const old = this.active.get(record.languageId);
    if (old && old.packVersion !== record.packVersion)
      this.previous.set(record.languageId, old);
    this.active.set(record.languageId, record);
    await this.setMeta(`state.${record.languageId}`, "READY");
  }

  async rollback(languageId: string): Promise<boolean> {
    const old = this.previous.get(languageId);
    if (!old) {
      await this.setMeta(`state.${languageId}`, "ROLLBACK_REQUIRED");
      return false;
    }
    this.active.set(languageId, old);
    this.previous.delete(languageId);
    await this.setMeta(`state.${languageId}`, "READY");
    return true;
  }

  disable(languageId: string): Promise<void> {
    return this.setMeta(`state.${languageId}`, "DISABLED");
  }
}
