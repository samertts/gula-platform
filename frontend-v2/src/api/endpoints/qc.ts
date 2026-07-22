import { apiGet, apiPost } from '../client';
import type { QCResult, PaginatedResponse } from '../types';

export interface SubmitQCRequest {
  test_code: string;
  level: string;
  expected_value: string;
  measured_value: string;
  sd: number;
}

export async function submitQC(data: SubmitQCRequest): Promise<QCResult> {
  return apiPost<QCResult>('/qc', data);
}

export async function submitQCBatch(results: SubmitQCRequest[]): Promise<QCResult[]> {
  return apiPost<QCResult[]>('/qc/batch', { results });
}

export async function listQC(params?: {
  test_code?: string;
  status?: string;
  days?: number;
  skip?: number;
  limit?: number;
}): Promise<PaginatedResponse<QCResult>> {
  return apiGet<PaginatedResponse<QCResult>>('/qc', params as Record<string, any>);
}

export async function getQCSummary(days?: number): Promise<any> {
  return apiGet<any>('/qc/summary', { days } as Record<string, any>);
}
