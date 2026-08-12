import { inspectQueuePayload } from '../../../ui/utils/offlineQueueSecurity'
import { createQueueEnvelope } from '../../../ui/utils/offlineQueueContract'

const DB_NAME = 'gula-pharmacy-offline'
const DB_VERSION = 2

let db: IDBDatabase | null = null

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (db) return resolve(db)

    const request = indexedDB.open(DB_NAME, DB_VERSION)

    request.onupgradeneeded = (event) => {
      const database = (event.target as IDBOpenDBRequest).result

      if (!database.objectStoreNames.contains('pending_dispenses')) {
        const store = database.createObjectStore('pending_dispenses', {
          keyPath: 'id',
          autoIncrement: true,
        })
        store.createIndex('status', 'status', { unique: false })
        store.createIndex('created_at', 'created_at', { unique: false })
      }

      if (!database.objectStoreNames.contains('cached_inventory')) {
        const cache = database.createObjectStore('cached_inventory', {
          keyPath: 'id',
        })
        cache.createIndex('drug_code', 'drug_code', { unique: true })
        cache.createIndex('drug_name', 'drug_name', { unique: false })
      }

      if (!database.objectStoreNames.contains('cached_prescriptions')) {
        database.createObjectStore('cached_prescriptions', {
          keyPath: 'id',
        })
      }

      if (!database.objectStoreNames.contains('cached_patients')) {
        const patients = database.createObjectStore('cached_patients', {
          keyPath: 'id',
        })
        patients.createIndex('patient_id', 'patient_id', { unique: true })
        patients.createIndex('full_name', 'full_name', { unique: false })
      }

      if (!database.objectStoreNames.contains('sync_log')) {
        const sync = database.createObjectStore('sync_log', {
          keyPath: 'id',
          autoIncrement: true,
        })
        sync.createIndex('status', 'status', { unique: false })
      }

      if (!database.objectStoreNames.contains('queue_rejections')) {
        database.createObjectStore('queue_rejections', {
          keyPath: 'id',
          autoIncrement: true,
        })
      }
    }

    request.onsuccess = async (event) => {
      db = (event.target as IDBOpenDBRequest).result
      try {
        await purgeLegacyPendingDispenses(db!)
        resolve(db!)
      } catch (error) {
        reject(error)
      }
    }

    request.onerror = (event) => {
      reject((event.target as IDBOpenDBRequest).error)
    }
  })
}

function getStore(storeName: string, mode: IDBTransactionMode = 'readonly'): Promise<IDBObjectStore> {
  return openDB().then((database) => {
    const transaction = database.transaction(storeName, mode)
    return transaction.objectStore(storeName)
  })
}

export async function savePendingDispense(data: Record<string, unknown>): Promise<number> {
  const database = await openDB()
  const security = inspectQueuePayload(data)
  if (!security.safe) {
    await addQueueRejection(database, {
      source: 'gula-pharmacy-offline.pending_dispenses',
      reason: security.reason,
      rejectedAt: new Date().toISOString(),
    })
    throw new Error('تم رفض تخزين عملية صرف غير متصلة تحتوي بيانات اعتماد')
  }
  const envelope = await createQueueEnvelope({
    url: '/pharmacy/dispense',
    method: 'POST',
    entityType: 'dispense',
    entityId: typeof data.prescription_id === 'string' ? data.prescription_id : undefined,
    action: 'create',
    body: data,
  })
  const store = database.transaction('pending_dispenses', 'readwrite').objectStore('pending_dispenses')
  return new Promise((resolve, reject) => {
    const request = store.add({
      ...data,
      ...envelope,
      status: 'pending',
      created_at: envelope.createdAt,
      synced_at: null,
    })
    request.onsuccess = () => resolve(request.result as number)
    request.onerror = () => reject(request.error)
  })
}

async function addQueueRejection(database: IDBDatabase, entry: Record<string, unknown>): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    const transaction = database.transaction('queue_rejections', 'readwrite')
    const request = transaction.objectStore('queue_rejections').add(entry)
    request.onsuccess = () => resolve()
    request.onerror = () => reject(request.error)
  })
}

async function purgeLegacyPendingDispenses(database: IDBDatabase): Promise<void> {
  const entries = await new Promise<Record<string, unknown>[]>((resolve, reject) => {
    const request = database.transaction('pending_dispenses').objectStore('pending_dispenses').getAll()
    request.onsuccess = () => resolve(request.result as Record<string, unknown>[])
    request.onerror = () => reject(request.error)
  })

  for (const entry of entries) {
    const security = inspectQueuePayload(entry)
    if (!security.safe) {
      await addQueueRejection(database, {
        source: 'gula-pharmacy-offline.pending_dispenses',
        requestId: entry.id,
        reason: security.reason,
        rejectedAt: new Date().toISOString(),
      })
      await new Promise<void>((resolve, reject) => {
        const transaction = database.transaction('pending_dispenses', 'readwrite')
        const request = transaction.objectStore('pending_dispenses').delete(entry.id)
        request.onsuccess = () => resolve()
        request.onerror = () => reject(request.error)
      })
    }
  }
}

export async function getPendingDispenses(): Promise<Record<string, unknown>[]> {
  const store = await getStore('pending_dispenses')
  return new Promise((resolve, reject) => {
    const request = store.getAll()
    request.onsuccess = () => resolve(request.result as Record<string, unknown>[])
    request.onerror = () => reject(request.error)
  })
}

export async function markDispenseSynced(id: number) {
  const store = await getStore('pending_dispenses', 'readwrite')
  return new Promise((resolve, reject) => {
    const getRequest = store.get(id)
    getRequest.onsuccess = () => {
      const data = getRequest.result
      if (data) {
        data.status = 'synced'
        data.state = 'synced'
        data.updatedAt = new Date().toISOString()
        data.synced_at = new Date().toISOString()
        const putRequest = store.put(data)
        putRequest.onsuccess = () => resolve(true)
        putRequest.onerror = () => reject(putRequest.error)
      }
    }
    getRequest.onerror = () => reject(getRequest.error)
  })
}

export async function clearSyncedDispenses() {
  const store = await getStore('pending_dispenses', 'readwrite')
  const index = store.index('status')
  return new Promise((resolve, reject) => {
    const request = index.getAll('synced')
    request.onsuccess = () => {
      const items = request.result as { id: number }[]
      if (items.length === 0) return resolve(0)
      let deleted = 0
      items.forEach((item) => {
        const delReq = store.delete(item.id)
        delReq.onsuccess = () => {
          deleted++
          if (deleted === items.length) resolve(deleted)
        }
      })
    }
    request.onerror = () => reject(request.error)
  })
}

export async function cacheInventory(items: Record<string, unknown>[]) {
  const store = await getStore('cached_inventory', 'readwrite')
  return Promise.all(
    items.map(
      (item) =>
        new Promise<void>((resolve, reject) => {
          const request = store.put(item)
          request.onsuccess = () => resolve()
          request.onerror = () => reject(request.error)
        }),
    ),
  )
}

export async function getCachedInventory(): Promise<Record<string, unknown>[]> {
  const store = await getStore('cached_inventory')
  return new Promise((resolve, reject) => {
    const request = store.getAll()
    request.onsuccess = () => resolve(request.result as Record<string, unknown>[])
    request.onerror = () => reject(request.error)
  })
}

export async function getCachedInventoryItem(drugCode: string): Promise<Record<string, unknown> | null> {
  const store = await getStore('cached_inventory')
  const index = store.index('drug_code')
  return new Promise((resolve, reject) => {
    const request = index.get(drugCode)
    request.onsuccess = () => resolve((request.result as Record<string, unknown>) || null)
    request.onerror = () => reject(request.error)
  })
}

export async function cachePatients(patients: Record<string, unknown>[]) {
  const store = await getStore('cached_patients', 'readwrite')
  return Promise.all(
    patients.map(
      (patient) =>
        new Promise<void>((resolve, reject) => {
          const request = store.put(patient)
          request.onsuccess = () => resolve()
          request.onerror = () => reject(request.error)
        }),
    ),
  )
}

export async function searchCachedPatients(query: string): Promise<Record<string, unknown>[]> {
  const store = await getStore('cached_patients')
  const index = store.index('full_name')
  return new Promise((resolve, reject) => {
    const results: Record<string, unknown>[] = []
    const request = index.openCursor()
    request.onsuccess = (event) => {
      const cursor = (event.target as IDBRequest<IDBCursorWithValue>).result
      if (cursor) {
        const name = (cursor.value.full_name as string) || ''
        if (name.toLowerCase().includes(query.toLowerCase())) {
          results.push(cursor.value as Record<string, unknown>)
        }
        cursor.continue()
      } else {
        resolve(results)
      }
    }
    request.onerror = () => reject(request.error)
  })
}

export async function addSyncLog(entry: { action: string; entity_type: string; entity_id: string; status: string; error?: string }) {
  const store = await getStore('sync_log', 'readwrite')
  return new Promise((resolve, reject) => {
    const request = store.add({
      ...entry,
      created_at: new Date().toISOString(),
    })
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}

export async function getSyncLogs(): Promise<Record<string, unknown>[]> {
  const store = await getStore('sync_log')
  return new Promise((resolve, reject) => {
    const request = store.getAll()
    request.onsuccess = () => resolve(request.result as Record<string, unknown>[])
    request.onerror = () => reject(request.error)
  })
}

export async function clearCache() {
  const database = await openDB()
  const storeNames = Array.from(database.objectStoreNames)
  return Promise.all(
    storeNames.map(
      (name) =>
        new Promise<void>((resolve, reject) => {
          const transaction = database.transaction(name, 'readwrite')
          const store = transaction.objectStore(name)
          const request = store.clear()
          request.onsuccess = () => resolve()
          request.onerror = () => reject(request.error)
        }),
    ),
  )
}

export async function getOfflineStats() {
  const pending = await getPendingDispenses()
  const inventory = await getCachedInventory()
  const logs = await getSyncLogs()
  return {
    pending_count: pending.filter((d) => d.status === 'pending').length,
    synced_count: pending.filter((d) => d.status === 'synced').length,
    cached_inventory: inventory.length,
    sync_log_count: logs.length,
  }
}
