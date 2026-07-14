import { GulaClient } from '../client';
import {
  SampleCreate, SampleUpdate, SampleResponse, SampleTransferRequest,
  ListResponse, PaginationParams,
} from '../types';

export class SamplesAPI {
  constructor(private client: GulaClient) {}

  async list(params?: PaginationParams & { status?: string; type?: string }): Promise<ListResponse<SampleResponse>> {
    return this.client.get<ListResponse<SampleResponse>>('/samples', params as Record<string, unknown>);
  }

  async get(id: number): Promise<SampleResponse> {
    return this.client.get<SampleResponse>(`/samples/${id}`);
  }

  async create(data: SampleCreate): Promise<SampleResponse> {
    return this.client.post<SampleResponse>('/samples', data);
  }

  async update(id: number, data: SampleUpdate): Promise<SampleResponse> {
    return this.client.put<SampleResponse>(`/samples/${id}`, data);
  }

  async delete(id: number): Promise<void> {
    return this.client.delete(`/samples/${id}`);
  }

  async stats(): Promise<Record<string, unknown>> {
    return this.client.get('/samples/stats');
  }

  async export(params?: Record<string, unknown>): Promise<Blob> {
    const qs = new URLSearchParams(
      Object.entries(params ?? {}).map(([k, v]) => [k, String(v)])
    ).toString();
    return this.client.download(`/samples/export?${qs}`, 'samples.csv');
  }

  async bulkRegister(data: SampleCreate[]): Promise<SampleResponse[]> {
    return this.client.post<SampleResponse[]>('/samples/bulk-register', data);
  }

  async printBarcode(params?: { sample_id?: number }): Promise<Blob> {
    return this.client.download('/samples/print-barcode?' + new URLSearchParams(
      Object.entries(params ?? {}).map(([k, v]) => [k, String(v)])
    ).toString(), 'barcode.pdf');
  }

  async receive(id: number): Promise<SampleResponse> {
    return this.client.post<SampleResponse>(`/samples/${id}/receive`);
  }

  async reject(id: number, reason: string): Promise<SampleResponse> {
    return this.client.post<SampleResponse>(`/samples/${id}/reject`, { reason });
  }

  async lookupByBarcode(barcode: string): Promise<SampleResponse> {
    return this.client.get<SampleResponse>(`/samples/barcode/${encodeURIComponent(barcode)}`);
  }

  async printLabel(id: number): Promise<void> {
    return this.client.post(`/samples/${id}/print-label`);
  }

  async transfer(id: number, data: SampleTransferRequest): Promise<SampleResponse> {
    return this.client.post<SampleResponse>(`/samples/${id}/transfer`, data);
  }

  async timeline(id: number): Promise<{ status: string; timestamp: string; user: string }[]> {
    return this.client.get(`/samples/${id}/timeline`);
  }

  async history(id: number, params?: PaginationParams): Promise<ListResponse<{ action: string; timestamp: string; user: string }>> {
    return this.client.get(`/samples/history/${id}`, params as Record<string, unknown>);
  }
}
