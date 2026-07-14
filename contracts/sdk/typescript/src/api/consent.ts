import { GulaClient } from '../client';
import {
  GrantRequest, GrantResponse, RevokeRequest, RevokeResponse,
  CheckResponse, ConsentRecord, ListResponse, PaginationParams,
} from '../types';

export class ConsentAPI {
  constructor(private client: GulaClient) {}

  async grant(data: GrantRequest): Promise<GrantResponse> {
    return this.client.post<GrantResponse>('/consent/grant', data);
  }

  async revoke(data: RevokeRequest): Promise<RevokeResponse> {
    return this.client.post<RevokeResponse>('/consent/revoke', data);
  }

  async check(params: { gpid: string; grantee_id: string; scope: string }): Promise<CheckResponse> {
    return this.client.get<CheckResponse>('/consent/check', params as Record<string, unknown>);
  }

  async list(params?: PaginationParams): Promise<ListResponse<ConsentRecord>> {
    return this.client.get<ListResponse<ConsentRecord>>('/consent', params as Record<string, unknown>);
  }

  async update(id: string, data: Partial<ConsentRecord>): Promise<ConsentRecord> {
    return this.client.put<ConsentRecord>(`/consent/${id}`, data);
  }

  async revokeById(id: string): Promise<void> {
    return this.client.post(`/consent/${id}/revoke`);
  }

  async auditLog(params?: PaginationParams): Promise<ListResponse<{ action: string; user: string; timestamp: string }>> {
    return this.client.get('/consent/audit', params as Record<string, unknown>);
  }

  async citizenConsent(data: { action: string; gpid: string; grantee_id: string; scope: string }): Promise<void> {
    return this.client.post('/citizen-portal/consent', data);
  }
}
