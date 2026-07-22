import {
  collection,
  doc,
  onSnapshot,
  getDocs,
  setDoc,
  deleteDoc,
  query,
  where,
  orderBy,
  limit,
  Timestamp,
  serverTimestamp,
  QuerySnapshot,
  writeBatch,
} from 'firebase/firestore';
import { db } from '../firebase';
import { OfflineEngine } from './offline-engine';
interface SyncConfig {
  collections: string[];
  batchSize: number;
  pushIntervalMs: number;
  pullIntervalMs: number;
  conflictStrategy: 'server-wins' | 'client-wins' | 'last-write-wins' | 'manual';
}
interface SyncState {
  lastSyncTimestamp: number;
  syncVersion: number;
  isSyncing: boolean;
  errors: Array<{ collection: string; error: string; timestamp: number }>;
}
type SyncDirection = 'bidirectional' | 'firebase-to-api' | 'api-to-firebase';
const DEFAULT_CONFIG: SyncConfig = {
  collections: ['patients', 'orders', 'samples', 'results', 'users'],
  batchSize: 50,
  pushIntervalMs: 30000,
  pullIntervalMs: 60000,
  conflictStrategy: 'last-write-wins',
};
const SYNC_STATE_KEY = 'gula_firebase_sync_state';
export class FirebaseSyncEngine {
  private static instance: FirebaseSyncEngine;
  private engine: OfflineEngine;
  private config: SyncConfig;
  private state: SyncState;
  private pushInterval: ReturnType<typeof setInterval> | null = null;
  private pullInterval: ReturnType<typeof setInterval> | null = null;
  private snapshots: Array<() => void> = [];
  private apiBaseUrl: string;
  private authTokenGetter: () => Promise<string | null>;
  private constructor() {
    this.engine = OfflineEngine.getInstance();
    this.config = { ...DEFAULT_CONFIG };
    this.state = this.loadState();
    this.apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1';
    this.authTokenGetter = async () => null;
  }
  static getInstance(): FirebaseSyncEngine {
    if (!this.instance) this.instance = new FirebaseSyncEngine();
    return this.instance;
  }
  configure(config: Partial<SyncConfig>): void {
    this.config = { ...this.config, ...config };
  }
  setAuthTokenGetter(fn: () => Promise<string | null>): void {
    this.authTokenGetter = fn;
  }
  private loadState(): SyncState {
    try {
      const saved = localStorage.getItem(SYNC_STATE_KEY);
      if (saved) return JSON.parse(saved);
    } catch { /* ignore */ }
    return { lastSyncTimestamp: 0, syncVersion: 0, isSyncing: false, errors: [] };
  }
  private saveState(): void {
    localStorage.setItem(SYNC_STATE_KEY, JSON.stringify(this.state));
  }
  async start(): Promise<void> {
    this.stop();
    await this.pullFromFirebase();
    this.startListening();
    this.pushInterval = setInterval(() => this.pushToAPI(), this.config.pushIntervalMs);
    this.pullInterval = setInterval(() => this.pullFromFirebase(), this.config.pullIntervalMs);
  }
  stop(): void {
    this.snapshots.forEach(unsub => unsub());
    this.snapshots = [];
    if (this.pushInterval) { clearInterval(this.pushInterval); this.pushInterval = null; }
    if (this.pullInterval) { clearInterval(this.pullInterval); this.pullInterval = null; }
  }
  private startListening(): void {
    for (const col of this.config.collections) {
      const q = query(
        collection(db, col),
        where('updatedAt', '>', Timestamp.fromMillis(this.state.lastSyncTimestamp || 1)),
        orderBy('updatedAt', 'asc'),
        limit(this.config.batchSize),
      );
      const unsub = onSnapshot(q, (snapshot: QuerySnapshot) => {
        this.handleFirestoreChanges(col, snapshot);
      }, (error) => {
        this.state.errors.push({ collection: col, error: error.message, timestamp: Date.now() });
        this.saveState();
      });
      this.snapshots.push(unsub);
    }
  }
  private async handleFirestoreChanges(collectionName: string, snapshot: QuerySnapshot): Promise<void> {
    for (const change of snapshot.docChanges()) {
      const data = { id: change.doc.id, ...change.doc.data() };
      if (change.type === 'removed') {
        await this.engine.deleteDocument(collectionName as any, change.doc.id);
      } else {
        await this.engine.cacheDocument(collectionName as any, change.doc.id, data);
      }
    }
  }
  async pushToAPI(): Promise<{ success: number; failed: number }> {
    const token = await this.authTokenGetter();
    if (!token) return { success: 0, failed: 0 };
    const operations = await this.engine.getPendingOperations();
    let success = 0;
    let failed = 0;
    for (const op of operations) {
      try {
        const endpoint = `${this.apiBaseUrl}/${op.collection}/${op.documentId}`;
        const response = await fetch(endpoint, {
          method: op.operation === 'create' ? 'POST' : op.operation === 'update' ? 'PUT' : 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: op.operation !== 'delete' ? JSON.stringify(op.payload) : undefined,
        });
        if (response.ok) {
          success++;
        } else if (response.status === 409) {
          const resolution = await this.resolveConflict(op, await response.json());
          if (resolution) {
            success++;
            await this.writeToFirebase(op.collection, op.documentId, resolution);
          }
        } else {
          failed++;
        }
      } catch {
        failed++;
      }
    }
    return { success, failed };
  }
  async pullFromFirebase(): Promise<void> {
    for (const col of this.config.collections) {
      try {
        const q = query(
          collection(db, col),
          where('updatedAt', '>', Timestamp.fromMillis(this.state.lastSyncTimestamp || 1)),
          orderBy('updatedAt', 'asc'),
          limit(this.config.batchSize),
        );
        const snapshot = await getDocs(q);
        for (const docSnap of snapshot.docs) {
          const data = { id: docSnap.id, ...docSnap.data() };
          await this.engine.cacheDocument(col as any, docSnap.id, data);
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        this.state.errors.push({ collection: col, error: msg, timestamp: Date.now() });
      }
    }
    this.state.lastSyncTimestamp = Date.now();
    this.state.syncVersion++;
    this.saveState();
  }
  private async resolveConflict(local: any, server: any): Promise<Record<string, unknown> | null> {
    switch (this.config.conflictStrategy) {
      case 'server-wins':
        return server.data;
      case 'client-wins':
        return local.payload;
      case 'last-write-wins':
        return (local.timestamp || 0) > (server.updatedAt?.seconds * 1000 || 0) ? local.payload : server.data;
      case 'manual':
        await this.engine.enqueue('update', local.collection, local.documentId, {
          _conflict: true,
          local: local.payload,
          server: server.data,
        });
        return null;
      default:
        return server.data;
    }
  }
  async writeToFirebase(collectionName: string, documentId: string, data: Record<string, unknown>): Promise<void> {
    const ref = doc(db, collectionName, documentId);
    await setDoc(ref, { ...data, updatedAt: serverTimestamp() }, { merge: true });
    await this.engine.cacheDocument(collectionName as any, documentId, data);
  }
  async deleteFromFirebase(collectionName: string, documentId: string): Promise<void> {
    await deleteDoc(doc(db, collectionName, documentId));
    await this.engine.deleteDocument(collectionName as any, documentId);
  }
  async batchSyncFromAPI(endpoint: string, collectionName: string, token: string): Promise<number> {
    const response = await fetch(`${this.apiBaseUrl}/${endpoint}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error(`API sync failed: ${response.status}`);
    const data = await response.json();
    const items = Array.isArray(data) ? data : data.data || data.items || [];
    const batch = writeBatch(db);
    for (const item of items) {
      const ref = doc(db, collectionName, item.id);
      batch.set(ref, { ...item, updatedAt: serverTimestamp() }, { merge: true });
    }
    await batch.commit();
    for (const item of items) {
      await this.engine.cacheDocument(collectionName as any, item.id, item);
    }
    return items.length;
  }
  async getDeltaSync(token: string, lastSyncTimestamp?: number): Promise<Record<string, unknown[]>> {
    const since = lastSyncTimestamp || this.state.lastSyncTimestamp || 0;
    const response = await fetch(`${this.apiBaseUrl}/sync/delta?since=${since}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error(`Delta sync failed: ${response.status}`);
    const data = await response.json();
    return data.changes || {};
  }
  getState(): SyncState {
    return { ...this.state };
  }
  getErrors(): Array<{ collection: string; error: string; timestamp: number }> {
    return [...this.state.errors];
  }
  clearErrors(): void {
    this.state.errors = [];
    this.saveState();
  }
  async forceFullSync(): Promise<void> {
    this.state.lastSyncTimestamp = 0;
    await this.pullFromFirebase();
    await this.pushToAPI();
  }
}
export type { SyncConfig, SyncState, SyncDirection };