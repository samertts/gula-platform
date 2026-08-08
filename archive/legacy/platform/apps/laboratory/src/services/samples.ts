import { apiRequest } from './api';
import type { Sample } from '@/utils/types';

export interface SamplesListParams {
  page?: number;
  perPage?: number;
  status?: string;
  priority?: string;
  search?: string;
  dateFrom?: string;
  dateTo?: string;
  labId?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  perPage: number;
  totalPages: number;
}

export const samplesService = {
  async list(params: SamplesListParams = {}): Promise<PaginatedResponse<Sample>> {
    const query = new URLSearchParams();
    if (params.page) query.set('page', String(params.page));
    if (params.perPage) query.set('per_page', String(params.perPage));
    if (params.status) query.set('status', params.status);
    if (params.priority) query.set('priority', params.priority);
    if (params.search) query.set('search', params.search);
    if (params.dateFrom) query.set('date_from', params.dateFrom);
    if (params.dateTo) query.set('date_to', params.dateTo);
    if (params.labId) query.set('lab_id', params.labId);
    return apiRequest<PaginatedResponse<Sample>>(`/samples?${query.toString()}`);
  },

  async getById(id: string): Promise<Sample> {
    return apiRequest<Sample>(`/samples/${id}`);
  },

  async getByBarcode(barcode: string): Promise<Sample> {
    return apiRequest<Sample>(`/samples/barcode/${barcode}`);
  },

  async create(data: Partial<Sample>): Promise<Sample> {
    return apiRequest<Sample>('/samples', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async update(id: string, data: Partial<Sample>): Promise<Sample> {
    return apiRequest<Sample>(`/samples/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  async registerSample(data: {
    sampleId?: string;
    patientId: string;
    patientName: string;
    specimenType: string;
    tests: string[];
    priority?: string;
    notes?: string;
  }): Promise<Sample> {
    return apiRequest<Sample>('/samples/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async collectSample(id: string, data: {
    collectedBy: string;
    volume?: number;
    container?: string;
    notes?: string;
  }): Promise<Sample> {
    return apiRequest<Sample>(`/samples/${id}/collect`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async receiveSample(id: string, data: {
    receivedBy: string;
    condition?: string;
    rejectReason?: string;
    notes?: string;
  }): Promise<Sample> {
    return apiRequest<Sample>(`/samples/${id}/receive`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async acceptSample(id: string, data: { acceptedBy: string; notes?: string }): Promise<Sample> {
    return apiRequest<Sample>(`/samples/${id}/accept`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async rejectSample(id: string, data: {
    rejectedBy: string;
    reason: string;
    notes?: string;
  }): Promise<Sample> {
    return apiRequest<Sample>(`/samples/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async getTimeline(id: string): Promise<{ status: string; timestamp: string; by: string }[]> {
    return apiRequest(`/samples/${id}/timeline`);
  },

  async getStats(params: { labId?: string; dateFrom?: string; dateTo?: string } = {}): Promise<{
    total: number;
    pending: number;
    collected: number;
    received: number;
    processing: number;
    completed: number;
    rejected: number;
    avgTurnaround: number;
  }> {
    const query = new URLSearchParams();
    if (params.labId) query.set('lab_id', params.labId);
    if (params.dateFrom) query.set('date_from', params.dateFrom);
    if (params.dateTo) query.set('date_to', params.dateTo);
    return apiRequest(`/samples/stats?${query.toString()}`);
  },
};
