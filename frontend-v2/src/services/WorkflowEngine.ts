import { 
  collection, 
  addDoc, 
  updateDoc, 
  doc, 
  serverTimestamp, 
  query, 
  where, 
  onSnapshot,
  writeBatch
} from 'firebase/firestore';
import { db, handleFirestoreError } from '../firebase';
import { Task } from '../types/domain';
import { AuditService } from './AuditService';
import { SyncService } from './SyncService';

export const WorkflowEngine = {
  async createTask(params: Omit<Task, 'id' | 'createdAt' | 'updatedAt'>) {
    if (!navigator.onLine) {
      SyncService.enqueue('LOG_ACTIVITY', { action: 'CREATE_TASK_OFFLINE', payload: params });
      return 'queued';
    }

    try {
      const docRef = await addDoc(collection(db, 'tasks'), {
        ...params,
        createdAt: serverTimestamp(),
        updatedAt: serverTimestamp(),
      });

      await AuditService.log({
        action: 'TASK_CREATED',
        resource: 'task',
        resourceId: docRef.id,
        severity: 'info'
      });

      return docRef.id;
    } catch (error) {
      handleFirestoreError(error, 'create', 'tasks');
    }
  },

  async updateTaskStatus(taskId: string, status: Task['status'], userId?: string) {
    if (!navigator.onLine) {
      SyncService.enqueue('UPDATE_TASK', { taskId, updates: { status, assignedTo: userId } });
      return;
    }

    try {
      const taskRef = doc(db, 'tasks', taskId);
      const updates: any = { 
        status, 
        updatedAt: serverTimestamp() 
      };
      
      if (userId) updates.assignedTo = userId;

      await updateDoc(taskRef, updates);

      await AuditService.log({
        action: 'TASK_STATUS_UPDATED',
        resource: 'task',
        resourceId: taskId,
        changes: { before: null, after: { status } },
        severity: 'info'
      });
    } catch (error) {
      handleFirestoreError(error, 'update', `tasks/${taskId}`);
    }
  },

  async bulkUpdateTasks(taskIds: string[], updates: Partial<Task>) {
    if (!navigator.onLine) {
      SyncService.enqueue('BULK_UPDATE_TASKS', { taskIds, updates });
      return;
    }

    try {
      const batch = writeBatch(db);
      const timestamp = serverTimestamp();

      taskIds.forEach(id => {
        const ref = doc(db, 'tasks', id);
        batch.update(ref, { 
          ...updates, 
          updatedAt: timestamp 
        });
      });

      await batch.commit();

      await AuditService.log({
        action: 'BULK_TASK_UPDATE',
        resource: 'task',
        resourceId: 'batch',
        changes: { before: { count: taskIds.length }, after: updates },
        severity: 'info'
      });
    } catch (error) {
      handleFirestoreError(error, 'write', 'tasks/batch');
    }
  },

  subscribeToEntityTasks(entityId: string, callback: (tasks: Task[]) => void) {
    const q = query(
      collection(db, 'tasks'), 
      where('entityId', '==', entityId)
    );

    return onSnapshot(q, (snapshot) => {
      const tasks = snapshot.docs.map(doc => ({ 
        id: doc.id, 
        ...doc.data() 
      } as Task));
      callback(tasks);
    }, (error) => {
      console.error("Error subscribing to entity tasks:", error);
    });
  }
};
