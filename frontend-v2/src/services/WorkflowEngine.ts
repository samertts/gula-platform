import { apiGet, apiPost, apiPut } from '../api/client';
import { Task } from '../types/domain';
import { AuditService } from './AuditService';

export const WorkflowEngine = {
  async createTask(params: Omit<Task, 'id' | 'createdAt' | 'updatedAt'>) {
    try {
      const result = await apiPost<{ id: string }>('/tasks', params);
      await AuditService.log({
        action: 'TASK_CREATED',
        resource: 'task',
        resourceId: result.id,
        severity: 'info',
      });
      return result.id;
    } catch (error) {
      console.error('Failed to create task:', error);
      throw error;
    }
  },

  async updateTaskStatus(taskId: string, status: Task['status'], userId?: string) {
    try {
      await apiPut(`/tasks/${taskId}/status`, { status, assigned_to: userId });
      await AuditService.log({
        action: 'TASK_STATUS_UPDATED',
        resource: 'task',
        resourceId: taskId,
        changes: { before: null, after: { status } },
        severity: 'info',
      });
    } catch (error) {
      console.error('Failed to update task:', error);
    }
  },

  async bulkUpdateTasks(taskIds: string[], updates: Partial<Task>) {
    try {
      await apiPost('/tasks/bulk', { task_ids: taskIds, updates });
    } catch (error) {
      console.error('Failed to bulk update tasks:', error);
    }
  },

  subscribeToEntityTasks(entityId: string, callback: (tasks: Task[]) => void) {
    const poll = async () => {
      try {
        const result = await apiGet<{ data: Task[] }>('/tasks', { entity_id: entityId });
        callback(result.data || []);
      } catch {
        callback([]);
      }
    };
    poll();
    const interval = setInterval(poll, 30000);
    return () => clearInterval(interval);
  },

  subscribeToLabTasks(labId: string, callback: (tasks: Task[]) => void) {
    const poll = async () => {
      try {
        const result = await apiGet<{ data: Task[] }>('/tasks', { lab_id: labId });
        callback(result.data || []);
      } catch {
        callback([]);
      }
    };
    poll();
    const interval = setInterval(poll, 30000);
    return () => clearInterval(interval);
  },
};
