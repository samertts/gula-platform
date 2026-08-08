import { apiRequest } from './api';
import type { Analyzer, AnalyzerStatus } from '@/utils/types';

export const analyzersService = {
  async list(params: {
    labId?: string;
    status?: AnalyzerStatus;
    isActive?: boolean;
  } = {}): Promise<Analyzer[]> {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => { if (v !== undefined) query.set(k, String(v)); });
    return apiRequest<Analyzer[]>(`/analyzers?${query.toString()}`);
  },

  async getById(id: string): Promise<Analyzer> {
    return apiRequest<Analyzer>(`/analyzers/${id}`);
  },

  async register(data: Partial<Analyzer>): Promise<Analyzer> {
    return apiRequest<Analyzer>('/analyzers', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async update(id: string, data: Partial<Analyzer>): Promise<Analyzer> {
    return apiRequest<Analyzer>(`/analyzers/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  async setStatus(id: string, status: AnalyzerStatus): Promise<Analyzer> {
    return apiRequest<Analyzer>(`/analyzers/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  },

  async calibrate(id: string, data: {
    performedBy: string;
    calibratorLot?: string;
    notes?: string;
  }): Promise<Analyzer> {
    return apiRequest<Analyzer>(`/analyzers/${id}/calibrate`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async getMetrics(id: string): Promise<{
    testsPerHour: number;
    totalTests: number;
    uptimePercent: number;
    errorCount: number;
    lastMaintenance: string;
    nextMaintenance: string;
  }> {
    return apiRequest(`/analyzers/${id}/metrics`);
  },

  async getRealTimeStatus(id: string): Promise<{
    status: AnalyzerStatus;
    currentTest?: string;
    queueLength: number;
    temperature?: number;
    humidity?: number;
    reagentLevels: { name: string; level: number; status: 'ok' | 'low' | 'empty' }[];
    lastResult?: string;
  }> {
    return apiRequest(`/analyzers/${id}/realtime`);
  },

  async queueTest(id: string, data: {
    sampleId: string;
    testName: string;
    priority?: string;
  }): Promise<void> {
    return apiRequest(`/analyzers/${id}/queue`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async getDashboardStats(): Promise<{
    total: number;
    online: number;
    offline: number;
    maintenance: number;
    error: number;
    calibrating: number;
    qcFailed: number;
  }> {
    return apiRequest('/analyzers/dashboard-stats');
  },
};
