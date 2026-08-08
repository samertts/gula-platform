import { apiGet, apiPost, apiPut } from '../client';
import type { Sample, PaginatedResponse } from '../types';

export interface RegisterSampleRequest {
  order_id: string;
  sample_type: string;
  collected_by?: string;
  notes?: string;
}

export async function registerSample(data: RegisterSampleRequest): Promise<Sample> {
  return apiPost<Sample>('/samples', data);
}

export async function listSamples(params?: { status?: string; skip?: number; limit?: number }): Promise<PaginatedResponse<Sample>> {
  return apiGet<PaginatedResponse<Sample>>('/samples', params as Record<string, any>);
}

export async function getSampleByBarcode(barcode: string): Promise<Sample> {
  return apiGet<Sample>(`/samples/${encodeURIComponent(barcode)}`);
}

export async function updateSample(barcode: string, data: Partial<Sample>): Promise<Sample> {
  return apiPut<Sample>(`/samples/${encodeURIComponent(barcode)}`, data);
}
