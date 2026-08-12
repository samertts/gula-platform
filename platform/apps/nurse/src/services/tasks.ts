import { api } from './api';
import type { NursingTask, TaskStatus, Priority, TaskType } from '@/utils/types';

type BackendTask = Record<string, unknown>;

type TaskListResponse = {
  items?: BackendTask[];
  total?: number;
};

function text(value: unknown, fallback = ''): string {
  return typeof value === 'string' || typeof value === 'number' ? String(value) : fallback;
}

function status(value: unknown): TaskStatus {
  const raw = text(value).replace('_', '-');
  if (raw === 'in-progress' || raw === 'completed' || raw === 'cancelled' || raw === 'delayed') return raw;
  return 'pending';
}

function priority(value: unknown): Priority {
  const raw = text(value) as Priority;
  return ['low', 'medium', 'high', 'urgent', 'stat'].includes(raw) ? raw : 'medium';
}

function taskType(value: unknown): TaskType {
  const raw = text(value) as TaskType;
  return ['medication', 'vitals', 'wound_care', 'catheter', 'dressing', 'observation', 'feeding', 'mobilization', 'education', 'assessment', 'other'].includes(raw)
    ? raw
    : 'other';
}

function normalizeTask(value: BackendTask): NursingTask {
  return {
    id: text(value.id),
    patientId: text(value.patient_id ?? value.patientId),
    patientName: text(value.patient_name ?? value.patientName, 'مريض غير معرّف'),
    bed: text(value.bed),
    type: taskType(value.task_type ?? value.type),
    description: text(value.description),
    priority: priority(value.priority),
    status: status(value.status),
    due: text(value.due_time ?? value.due),
    assignedTo: text(value.assigned_to ?? value.assignedTo),
    createdAt: text(value.created_at ?? value.createdAt),
    notes: text(value.notes),
  };
}

function query(params: Record<string, string | undefined>): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) search.set(key, value);
  });
  const encoded = search.toString();
  return encoded ? `?${encoded}` : '';
}

async function listBackendTasks(params: Record<string, string | undefined> = {}): Promise<NursingTask[]> {
  const response = await api.get<TaskListResponse>(`/nursing/tasks${query(params)}`);
  return (response.items || []).map(normalizeTask);
}

export const tasksService = {
  getList: (ward?: string) => listBackendTasks({ ward }),
  getById: async (id: string) => normalizeTask(await api.get<BackendTask>(`/nursing/tasks/${encodeURIComponent(id)}`)),
  getByPatient: async (patientId: string) => {
    const response = await api.get<{ items?: BackendTask[] }>(`/nursing/tasks/patient/${encodeURIComponent(patientId)}`);
    return (response.items || []).map(normalizeTask);
  },
  create: async (data: Partial<NursingTask>) => normalizeTask(await api.post<BackendTask>('/nursing/tasks', data)),
  updateStatus: async (id: string, nextStatus: TaskStatus, notes?: string) => normalizeTask(await api.put<BackendTask>(`/nursing/tasks/${encodeURIComponent(id)}`, {
    status: nextStatus.replace('-', '_'),
    notes,
  })),
  getPriorityCount: async (ward?: string) => {
    const tasks = await listBackendTasks({ ward });
    return tasks.reduce((counts, task) => {
      const key = task.priority === 'stat' ? 'urgent' : task.priority;
      counts[key] = (counts[key] || 0) + 1;
      return counts;
    }, { urgent: 0, high: 0, medium: 0, low: 0 } as { urgent: number; high: number; medium: number; low: number });
  },
  getOverdue: async (ward?: string) => listBackendTasks({ ward }),
  assignTo: async (id: string, userId: string) => normalizeTask(await api.put<BackendTask>(`/nursing/tasks/${encodeURIComponent(id)}`, { assigned_to: userId })),
  complete: async (id: string, data: { outcome?: string; notes?: string }) => normalizeTask(await api.put<BackendTask>(`/nursing/tasks/${encodeURIComponent(id)}/complete`, {
    patient_response: data.outcome,
    notes: data.notes,
  })),
};
