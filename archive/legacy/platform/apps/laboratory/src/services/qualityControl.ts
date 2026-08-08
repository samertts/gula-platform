import { apiRequest } from './api';
import type { QCData, QCStatus } from '@/utils/types';

export interface QCSummary {
  total: number;
  inControl: number;
  warning: number;
  outOfControl: number;
  notRun: number;
}

export const qualityControlService = {
  async list(params: {
    labId?: string;
    deviceId?: string;
    status?: QCStatus;
    dateFrom?: string;
    dateTo?: string;
  } = {}): Promise<QCData[]> {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => { if (v) query.set(k, String(v)); });
    return apiRequest<QCData[]>(`/quality-control?${query.toString()}`);
  },

  async getById(id: string): Promise<QCData> {
    return apiRequest<QCData>(`/quality-control/${id}`);
  },

  async record(data: {
    testName: string;
    level: string;
    value: number;
    deviceId?: string;
    lotNumber?: string;
    performedBy: string;
  }): Promise<QCData> {
    return apiRequest<QCData>('/quality-control', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async getSummary(params: {
    labId?: string;
    dateFrom?: string;
    dateTo?: string;
  } = {}): Promise<QCSummary> {
    const query = new URLSearchParams();
    if (params.labId) query.set('lab_id', params.labId);
    if (params.dateFrom) query.set('date_from', params.dateFrom);
    if (params.dateTo) query.set('date_to', params.dateTo);
    return apiRequest<QCSummary>(`/quality-control/summary?${query.toString()}`);
  },

  async getLeveyJennings(testName: string, level: string, params: {
    labId?: string;
    days?: number;
  } = {}): Promise<{
    mean: number;
    sd: number;
    cv: number;
    points: { date: string; value: number }[];
    limits: { warning: [number, number]; action: [number, number] };
  }> {
    const query = new URLSearchParams({ test_name: testName, level });
    if (params.labId) query.set('lab_id', params.labId);
    if (params.days) query.set('days', String(params.days));
    return apiRequest(`/quality-control/levey-jennings?${query.toString()}`);
  },

  async getWestgardRules(): Promise<{ rule: string; description: string; active: boolean }[]> {
    return apiRequest('/quality-control/westgard-rules');
  },

  async updateWestgardRule(rule: string, active: boolean): Promise<void> {
    return apiRequest(`/quality-control/westgard-rules/${rule}`, {
      method: 'PUT',
      body: JSON.stringify({ active }),
    });
  },

  async getEQA(params: {
    labId?: string;
    scheme?: string;
    year?: number;
  } = {}): Promise<{
    id: string;
    scheme: string;
    analyte: string;
    assignedValue: number;
    labValue: number;
    targetRange: [number, number];
    zScore: number;
    acceptable: boolean;
    date: string;
  }[]> {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => { if (v) query.set(k, String(v)); });
    return apiRequest(`/quality-control/eqa?${query.toString()}`);
  },
};
