import { GulaClient } from '../client';
import {
  QCSubmit, QCBatchSubmit, QCRecord, QCRule,
  LeveyJenningsData, ListResponse, PaginationParams,
} from '../types';

export class QualityControlAPI {
  constructor(private client: GulaClient) {}

  async list(params?: PaginationParams & { status?: string; test_id?: string }): Promise<ListResponse<QCRecord>> {
    return this.client.get<ListResponse<QCRecord>>('/quality-control', params as Record<string, unknown>);
  }

  async get(id: number): Promise<QCRecord> {
    return this.client.get<QCRecord>(`/quality-control/${id}`);
  }

  async create(data: QCSubmit): Promise<QCRecord> {
    return this.client.post<QCRecord>('/quality-control', data);
  }

  async update(id: number, data: Partial<QCSubmit>): Promise<QCRecord> {
    return this.client.put<QCRecord>(`/quality-control/${id}`, data);
  }

  async delete(id: number): Promise<void> {
    return this.client.delete(`/quality-control/${id}`);
  }

  async approve(id: number): Promise<QCRecord> {
    return this.client.post<QCRecord>(`/quality-control/${id}/approve`);
  }

  async submitBatch(data: QCBatchSubmit): Promise<QCRecord[]> {
    return this.client.post<QCRecord[]>('/quality-control/batch-submit', data);
  }

  async evaluate(data: QCSubmit): Promise<{ passed: boolean; violated_rules: string[] }> {
    return this.client.post('/quality-control/evaluate', data);
  }

  async stats(): Promise<Record<string, unknown>> {
    return this.client.get('/quality-control/stats');
  }

  async import(file: File): Promise<{ imported: number }> {
    const fd = new FormData();
    fd.append('file', file);
    return this.client.upload('/quality-control/import', fd);
  }

  async export(params?: Record<string, unknown>): Promise<Blob> {
    const qs = new URLSearchParams(
      Object.entries(params ?? {}).map(([k, v]) => [k, String(v)])
    ).toString();
    return this.client.download(`/quality-control/export?${qs}`, 'qc-data.csv');
  }

  async rules(params?: PaginationParams): Promise<ListResponse<QCRule>> {
    return this.client.get<ListResponse<QCRule>>('/quality-control/rules', params as Record<string, unknown>);
  }

  async createRule(data: Partial<QCRule>): Promise<QCRule> {
    return this.client.post<QCRule>('/quality-control/rules', data);
  }

  async leveyJennings(testId: string): Promise<LeveyJenningsData> {
    return this.client.get<LeveyJenningsData>(`/quality-control/levey-jennings/${testId}`);
  }
}
