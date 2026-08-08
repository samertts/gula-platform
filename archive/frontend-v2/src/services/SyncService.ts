import { apiPost } from '../api/client';

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
      timestamp: Date.now(),
    });
    this.saveQueue(queue);
  },

  async processQueue(): Promise<void> {
    if (!navigator.onLine) return;

    const queue = this.getQueue();
    if (queue.length === 0) return;

    const remaining: SyncAction[] = [];
    const sortedQueue = [...queue].sort((a, b) => a.timestamp - b.timestamp);

    for (const action of sortedQueue) {
      try {
        switch (action.type) {
          case 'UPDATE_PROFILE':
            await apiPost('/sync/profile', action.payload);
            break;
          case 'LOG_ACTIVITY':
            await apiPost('/sync/activity', action.payload);
            break;
          case 'UPDATE_TASK':
            await apiPost(`/sync/tasks/${action.payload.taskId}`, action.payload.updates);
            break;
          case 'BULK_UPDATE_TASKS':
            await apiPost('/sync/tasks/bulk', action.payload);
            break;
        }
      } catch (error) {
        console.error('Sync failed for action:', action.type, error);
        remaining.push(action);
      }
    }

    this.saveQueue(remaining);
  },
};
