import { GulaClient } from '../client';
import {
  ComplianceRecord, Regulation, ComplianceReport,
  ListResponse, PaginationParams,
} from '../types';

export class ComplianceAPI {
  constructor(private client: GulaClient) {}

  async list(params?: PaginationParams): Promise<ListResponse<ComplianceRecord>> {
    return this.client.get<ListResponse<ComplianceRecord>>('/compliance', params as Record<string, unknown>);
  }

  async get(id: number): Promise<ComplianceRecord> {
    return this.client.get<ComplianceRecord>(`/compliance/${id}`);
  }

  async create(data: Partial<ComplianceRecord>): Promise<ComplianceRecord> {
    return this.client.post<ComplianceRecord>('/compliance', data);
  }

  async update(id: number, data: Partial<ComplianceRecord>): Promise<ComplianceRecord> {
    return this.client.put<ComplianceRecord>(`/compliance/${id}`, data);
  }

  async certify(id: number): Promise<ComplianceRecord> {
    return this.client.put<ComplianceRecord>(`/compliance/${id}/certify`);
  }

  async regulations(params?: PaginationParams): Promise<ListResponse<Regulation>> {
    return this.client.get<ListResponse<Regulation>>('/compliance/regulations', params as Record<string, unknown>);
  }

  async reports(params?: PaginationParams): Promise<ListResponse<ComplianceReport>> {
    return this.client.get<ListResponse<ComplianceReport>>('/compliance/reports', params as Record<string, unknown>);
  }

  async generateReport(data: { type: string; period_start: string; period_end: string }): Promise<ComplianceReport> {
    return this.client.post<ComplianceReport>('/compliance/reports/generate', data);
  }

  async triggerAudit(data: { lab_id: number; reason?: string }): Promise<void> {
    return this.client.post('/compliance/audit', data);
  }

  async checklist(): Promise<{ item: string; status: string }[]> {
    return this.client.get('/compliance/checklist');
  }
}
