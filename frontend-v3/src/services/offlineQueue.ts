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

type StoredEnvelope = {
  operation_id: string;
  created_at: string;
  status: OfflineOperation["status"];
  iv: ArrayBuffer;
  ciphertext: ArrayBuffer;
};

const DB_NAME = "gula-emergency-offline";
const DB_VERSION = 2;
const STORE = "operations";
const META_STORE = "meta";
const KEY_NAME = "aes-gcm-key";
export const MAX_QUEUE_SIZE = 5000;

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE)) {
        const store = db.createObjectStore(STORE, { keyPath: "operation_id" });
        store.createIndex("created_at", "created_at");
      }
      if (!db.objectStoreNames.contains(META_STORE)) db.createObjectStore(META_STORE);
    };
    request.onsuccess = async () => {
      const db = request.result;
      try {
        await migrateLegacyRows(db);
        resolve(db);
      } catch (error) {
        db.close();
        reject(error);
      }
    };
    request.onerror = () => reject(request.error ?? new Error("IndexedDB unavailable"));
  });
}

async function getKey(db: IDBDatabase): Promise<CryptoKey> {
  const existing = await new Promise<CryptoKey | undefined>((resolve, reject) => {
    const request = db.transaction(META_STORE, "readonly").objectStore(META_STORE).get(KEY_NAME);
    request.onsuccess = () => resolve(request.result as CryptoKey | undefined);
    request.onerror = () => reject(request.error ?? new Error("Could not read offline encryption key"));
  });
  if (existing) return existing;
  const key = await crypto.subtle.generateKey({ name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]);
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(META_STORE, "readwrite");
    tx.objectStore(META_STORE).put(key, KEY_NAME);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error ?? new Error("Could not persist offline encryption key"));
  });
  return key;
}

async function encryptOperation(db: IDBDatabase, operation: OfflineOperation): Promise<StoredEnvelope> {
  const key = await getKey(db);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const plaintext = new TextEncoder().encode(JSON.stringify({ ...operation, status: undefined }));
  const ciphertext = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, plaintext);
  return { operation_id: operation.operation_id, created_at: operation.created_at, status: operation.status ?? "queued", iv: iv.buffer, ciphertext };
}

async function migrateLegacyRows(db: IDBDatabase): Promise<void> {
  const rows = await new Promise<unknown[]>((resolve, reject) => {
    const request = db.transaction(STORE, "readonly").objectStore(STORE).getAll();
    request.onsuccess = () => resolve(request.result as unknown[]);
    request.onerror = () => reject(request.error ?? new Error("Could not inspect legacy offline queue"));
  });
  const legacyRows = rows.filter((row): row is OfflineOperation & { status?: OfflineOperation["status"] } => {
    const candidate = row as Partial<StoredEnvelope>;
    return !candidate.ciphertext || !candidate.iv;
  });
  for (const legacyRow of legacyRows) {
    const envelope = await encryptOperation(db, { ...legacyRow, status: legacyRow.status ?? "queued" });
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, "readwrite");
      tx.objectStore(STORE).put(envelope);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error ?? new Error("Could not migrate legacy offline operation"));
    });
  }
}

async function decryptOperation(db: IDBDatabase, envelope: StoredEnvelope): Promise<OfflineOperation> {
  const key = await getKey(db);
  const plaintext = await crypto.subtle.decrypt({ name: "AES-GCM", iv: envelope.iv }, key, envelope.ciphertext);
  const operation = JSON.parse(new TextDecoder().decode(plaintext)) as OfflineOperation;
  return { ...operation, status: envelope.status };
}

export async function enqueueOfflineOperation(operation: OfflineOperation): Promise<void> {
  const db = await openDb();
  try {
    const envelope = await encryptOperation(db, operation);
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, "readwrite");
      let queueFull = false;
      const countRequest = tx.objectStore(STORE).count();
      countRequest.onsuccess = () => {
        if (countRequest.result >= MAX_QUEUE_SIZE) {
          queueFull = true;
          tx.abort();
          return;
        }
        tx.objectStore(STORE).put(envelope);
      };
      countRequest.onerror = () => tx.abort();
      tx.oncomplete = () => resolve();
      tx.onabort = () => reject(queueFull ? new Error("Offline queue is full; use the institution fallback procedure") : (tx.error ?? new Error("Could not queue operation")));
      tx.onerror = () => reject(tx.error ?? new Error("Could not queue operation"));
    });
  } finally {
    db.close();
  }
}

export async function listOfflineOperations(): Promise<OfflineOperation[]> {
  const db = await openDb();
  try {
    const envelopes = await new Promise<StoredEnvelope[]>((resolve, reject) => {
      const request = db.transaction(STORE, "readonly").objectStore(STORE).index("created_at").getAll();
      request.onsuccess = () => resolve(request.result as StoredEnvelope[]);
      request.onerror = () => reject(request.error ?? new Error("Could not read offline queue"));
    });
    const rows: OfflineOperation[] = [];
    for (const envelope of envelopes) rows.push(await decryptOperation(db, envelope));
    return rows;
  } finally {
    db.close();
  }
}

export async function removeOfflineOperation(operationId: string): Promise<void> {
  const db = await openDb();
  try {
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, "readwrite");
      tx.objectStore(STORE).delete(operationId);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error ?? new Error("Could not remove offline operation"));
    });
  } finally {
    db.close();
  }
}

export async function markOfflineOperation(operationId: string, status: OfflineOperation["status"]): Promise<void> {
  const db = await openDb();
  try {
    const envelope = await new Promise<StoredEnvelope | undefined>((resolve, reject) => {
      const request = db.transaction(STORE, "readonly").objectStore(STORE).get(operationId);
      request.onsuccess = () => resolve(request.result as StoredEnvelope | undefined);
      request.onerror = () => reject(request.error ?? new Error("Could not read offline operation"));
    });
    if (!envelope) return;
    envelope.status = status;
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, "readwrite");
      tx.objectStore(STORE).put(envelope);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error ?? new Error("Could not update offline operation"));
    });
  } finally {
    db.close();
  }
}

export async function clearOfflineQueue(): Promise<void> {
  const db = await openDb();
  try {
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, "readwrite");
      tx.objectStore(STORE).clear();
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error ?? new Error("Could not clear offline queue"));
    });
  } finally {
    db.close();
  }
}
