import { api } from './api';
import type { NursingTask, TaskStatus } from '@/utils/types';

export const tasksService = {
  getList: async (ward?: string) => {
    const params = ward ? `?ward=${ward}` : '';
    return api.get<NursingTask[]>(`/nurse/tasks${params}`);
  },

  getById: async (id: string) => {
    return api.get<NursingTask>(`/nurse/tasks/${id}`);
  },

  getByPatient: async (patientId: string) => {
    return api.get<NursingTask[]>(`/nurse/tasks/by-patient/${patientId}`);
  },

  create: async (data: Partial<NursingTask>) => {
    return api.post<NursingTask>('/nurse/tasks', data);
  },

  updateStatus: async (id: string, status: TaskStatus, notes?: string) => {
    return api.patch<NursingTask>(`/nurse/tasks/${id}`, { status, notes });
  },

  getPriorityCount: async (ward?: string) => {
    const params = ward ? `?ward=${ward}` : '';
    return api.get<{ urgent: number; high: number; medium: number; low: number }>(`/nurse/tasks/priority-count${params}`);
  },

  getOverdue: async (ward?: string) => {
    const params = ward ? `?ward=${ward}` : '';
    return api.get<NursingTask[]>(`/nurse/tasks/overdue${params}`);
  },

  assignTo: async (id: string, userId: string) => {
    return api.patch<NursingTask>(`/nurse/tasks/${id}/assign`, { userId });
  },

  complete: async (id: string, data: { outcome?: string; notes?: string }) => {
    return api.post<NursingTask>(`/nurse/tasks/${id}/complete`, data);
  },
};
