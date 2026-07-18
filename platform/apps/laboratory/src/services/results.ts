import { apiRequest } from './api';
import type { TestResult, AutoverificationRule } from '@/utils/types';

export interface ResultsListParams {
  page?: number;
  perPage?: number;
  status?: string;
  flag?: string;
  sampleId?: string;
  category?: string;
  testName?: string;
  dateFrom?: string;
  dateTo?: string;
  labId?: string;
}

export const resultsService = {
  async list(params: ResultsListParams = {}): Promise<{ data: TestResult[]; total: number }> {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => { if (v) query.set(k, String(v)); });
    return apiRequest(`/results?${query.toString()}`);
  },

  async getById(id: string): Promise<TestResult> {
    return apiRequest<TestResult>(`/results/${id}`);
  },

  async getBySample(sampleId: string): Promise<TestResult[]> {
    return apiRequest<TestResult[]>(`/results/sample/${sampleId}`);
  },

  async create(data: Partial<TestResult>): Promise<TestResult> {
    return apiRequest<TestResult>('/results', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async update(id: string, data: Partial<TestResult>): Promise<TestResult> {
    return apiRequest<TestResult>(`/results/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  async submitForReview(id: string): Promise<TestResult> {
    return apiRequest<TestResult>(`/results/${id}/submit-review`, { method: 'POST' });
  },

  async validate(id: string, data: {
    verifiedBy: string;
    action: 'approve' | 'reject' | 'flag';
    notes?: string;
  }): Promise<TestResult> {
    return apiRequest<TestResult>(`/results/${id}/validate`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async batchValidate(ids: string[], data: {
    verifiedBy: string;
    action: 'approve' | 'reject';
  }): Promise<{ validated: number; failed: number }> {
    return apiRequest('/results/batch-validate', {
      method: 'POST',
      body: JSON.stringify({ ids, ...data }),
    });
  },

  async autoverify(sampleId: string): Promise<{
    verified: TestResult[];
    flagged: TestResult[];
    rejected: TestResult[];
  }> {
    return apiRequest(`/results/${sampleId}/autoverify`, { method: 'POST' });
  },

  async getAutoverificationRules(): Promise<AutoverificationRule[]> {
    return apiRequest<AutoverificationRule[]>('/results/autoverification-rules');
  },

  async updateAutoverificationRule(id: string, data: Partial<AutoverificationRule>): Promise<AutoverificationRule> {
    return apiRequest<AutoverificationRule>(`/results/autoverification-rules/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  async createAutoverificationRule(data: Partial<AutoverificationRule>): Promise<AutoverificationRule> {
    return apiRequest<AutoverificationRule>('/results/autoverification-rules', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async getDeltaCheck(sampleId: string, testName: string): Promise<{
    previousValue: number;
    currentValue: number;
    deltaPercent: number;
    passed: boolean;
  } | null> {
    return apiRequest(`/results/delta-check?sample_id=${sampleId}&test_name=${encodeURIComponent(testName)}`);
  },

  async getCriticalAlerts(params: {
    labId?: string;
    acknowledged?: boolean;
  } = {}): Promise<{ id: string; resultId: string; testName: string; value: string; flag: string; patientName: string; acknowledged: boolean; createdAt: string }[]> {
    const query = new URLSearchParams();
    if (params.labId) query.set('lab_id', params.labId);
    if (params.acknowledged !== undefined) query.set('acknowledged', String(params.acknowledged));
    return apiRequest(`/results/critical-alerts?${query.toString()}`);
  },

  async acknowledgeCriticalAlert(id: string): Promise<void> {
    return apiRequest(`/results/critical-alerts/${id}/acknowledge`, { method: 'POST' });
  },

  async getStats(params: {
    labId?: string;
    dateFrom?: string;
    dateTo?: string;
  } = {}): Promise<{
    total: number;
    verified: number;
    pending: number;
    flagged: number;
    critical: number;
    avgTurnaroundHours: number;
  }> {
    const query = new URLSearchParams();
    if (params.labId) query.set('lab_id', params.labId);
    if (params.dateFrom) query.set('date_from', params.dateFrom);
    if (params.dateTo) query.set('date_to', params.dateTo);
    return apiRequest(`/results/stats?${query.toString()}`);
  },
};
