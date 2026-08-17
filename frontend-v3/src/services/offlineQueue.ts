export type OfflineOperation = {
  operation_id: string;
  idempotency_key: string;
  operation_type: string;
  entity_type: string;
  entity_id?: string;
  base_version?: number;
  priority: string;
  payload: Record<string, unknown>;
  device_id: string;
  created_at: string;
  status?: "queued" | "conflict" | "failed";
};

const DB_NAME = "gula-emergency-offline";
const DB_VERSION = 1;
const STORE = "operations";

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE)) {
        const store = db.createObjectStore(STORE, { keyPath: "operation_id" });
        store.createIndex("created_at", "created_at");
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error ?? new Error("IndexedDB unavailable"));
  });
}

export async function enqueueOfflineOperation(operation: OfflineOperation): Promise<void> {
  const db = await openDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).put({ ...operation, status: operation.status ?? "queued" });
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error ?? new Error("Could not queue operation"));
  });
  db.close();
}

export async function listOfflineOperations(): Promise<OfflineOperation[]> {
  const db = await openDb();
  const rows = await new Promise<OfflineOperation[]>((resolve, reject) => {
    const tx = db.transaction(STORE, "readonly");
    const request = tx.objectStore(STORE).index("created_at").getAll();
    request.onsuccess = () => resolve(request.result as OfflineOperation[]);
    request.onerror = () => reject(request.error ?? new Error("Could not read offline queue"));
  });
  db.close();
  return rows;
}

export async function removeOfflineOperation(operationId: string): Promise<void> {
  const db = await openDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).delete(operationId);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error ?? new Error("Could not remove offline operation"));
  });
  db.close();
}

export async function markOfflineOperation(operationId: string, status: OfflineOperation["status"]): Promise<void> {
  const db = await openDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    const store = tx.objectStore(STORE);
    const request = store.get(operationId);
    request.onsuccess = () => {
      if (request.result) store.put({ ...request.result, status });
    };
    request.onerror = () => reject(request.error ?? new Error("Could not update offline operation"));
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error ?? new Error("Could not update offline operation"));
  });
  db.close();
}

export async function clearOfflineQueue(): Promise<void> {
  const db = await openDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).clear();
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error ?? new Error("Could not clear offline queue"));
  });
  db.close();
}
