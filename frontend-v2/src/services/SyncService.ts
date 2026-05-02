import { db } from '../firebase';
import { doc, setDoc, updateDoc, writeBatch, serverTimestamp } from 'firebase/firestore';

export type SyncAction = {
  id: string;
  type: 'UPDATE_PROFILE' | 'LOG_ACTIVITY' | 'UPDATE_TASK' | 'BULK_UPDATE_TASKS';
  payload: any;
  timestamp: number;
};

const SYNC_QUEUE_KEY = 'gula_sync_queue';

export const SyncService = {
  getQueue(): SyncAction[] {
    const stored = localStorage.getItem(SYNC_QUEUE_KEY);
    return stored ? JSON.parse(stored) : [];
  },

  saveQueue(queue: SyncAction[]): void {
    localStorage.setItem(SYNC_QUEUE_KEY, JSON.stringify(queue));
  },

  enqueue(type: SyncAction['type'], payload: any): void {
    const queue = this.getQueue();
    queue.push({
      id: Math.random().toString(36).substring(7),
      type,
      payload,
      timestamp: Date.now()
    });
    this.saveQueue(queue);
    console.log(`[SyncService] Action enqueued (offline): ${type}`);
  },

  async processQueue(): Promise<void> {
    if (!navigator.onLine) return;
    
    const queue = this.getQueue();
    if (queue.length === 0) return;

    console.log(`[SyncService] Online. Processing ${queue.length} pending actions...`);
    
    const remaining: SyncAction[] = [];
    const sortedQueue = [...queue].sort((a, b) => a.timestamp - b.timestamp);

    for (const action of sortedQueue) {
      try {
        switch (action.type) {
          case 'UPDATE_PROFILE':
            await updateDoc(doc(db, 'users', action.payload.uid), {
              ...action.payload,
              updatedAt: serverTimestamp()
            });
            break;
          case 'LOG_ACTIVITY':
            // Assuming an activity_logs collection
            const logRef = doc(db, 'activity_logs', action.id);
            await setDoc(logRef, {
              ...action.payload,
              timestamp: serverTimestamp()
            });
            break;
          case 'UPDATE_TASK':
            await updateDoc(doc(db, 'tasks', action.payload.taskId), {
              ...action.payload.updates,
              updatedAt: serverTimestamp()
            });
            break;
          case 'BULK_UPDATE_TASKS':
            const batch = writeBatch(db);
            action.payload.taskIds.forEach((id: string) => {
              batch.update(doc(db, 'tasks', id), {
                ...action.payload.updates,
                updatedAt: serverTimestamp()
              });
            });
            await batch.commit();
            break;
        }
      } catch (error) {
        console.error(`[SyncService] Failed to process action ${action.id}:`, error);
        remaining.push(action);
      }
    }

    this.saveQueue(remaining);
    if (remaining.length === 0) {
      console.log('[SyncService] Sync complete.');
    }
  }
};

if (typeof window !== 'undefined') {
  window.addEventListener('online', () => SyncService.processQueue());
}
