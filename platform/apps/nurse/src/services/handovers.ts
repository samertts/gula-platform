import { api } from './api';

export type HandoverShift = 'morning' | 'evening' | 'night';

export interface HandoverRecord {
  id: string;
  shift: HandoverShift;
  date: string;
  fromNurse: string;
  toNurse: string;
  patientCount: number;
  criticalCount: number;
  notes: string;
  completed: boolean;
}

type BackendHandover = Record<string, unknown>;

type HandoverListResponse = {
  items?: BackendHandover[];
};

function text(value: unknown, fallback = ''): string {
  return typeof value === 'string' || typeof value === 'number' ? String(value) : fallback;
}

function listLength(value: unknown): number {
  return Array.isArray(value) ? value.length : 0;
}

function normalizeShift(value: unknown): HandoverShift {
  const raw = text(value);
  return raw === 'evening' || raw === 'night' ? raw : 'morning';
}

function normalizeHandover(value: BackendHandover): HandoverRecord {
  return {
    id: text(value.id),
    shift: normalizeShift(value.handover_type ?? value.shift),
    date: text(value.shift_date ?? value.date),
    fromNurse: text(value.from_nurse_id ?? value.fromNurse),
    toNurse: text(value.to_nurse_id ?? value.toNurse),
    patientCount: listLength(value.patient_summaries),
    criticalCount: listLength(value.critical_alerts),
    notes: text(value.notes),
    completed: Boolean(value.is_completed ?? value.completed),
  };
}

export interface CreateHandoverInput {
  from_nurse_id: string;
  to_nurse_id: string;
  handover_type: HandoverShift;
  shift_date: string;
  notes?: string;
}

export const handoversService = {
  async list(): Promise<HandoverRecord[]> {
    const response = await api.get<HandoverListResponse>('/nursing/handover');
    return (response.items || []).map(normalizeHandover);
  },
  async create(input: CreateHandoverInput): Promise<HandoverRecord> {
    const response = await api.post<BackendHandover>('/nursing/handover', {
      ...input,
      patient_summaries: [],
      pending_tasks: [],
      critical_alerts: [],
      medication_changes: [],
      equipment_issues: [],
    });
    return normalizeHandover(response);
  },
};
