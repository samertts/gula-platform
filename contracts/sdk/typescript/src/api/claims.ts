import { GulaClient } from '../client';
import {
  ClaimCreate, ClaimResponse, ListResponse, PaginationParams,
} from '../types';

export class ClaimsAPI {
  constructor(private client: GulaClient) {}

  async list(params?: PaginationParams): Promise<ListResponse<ClaimResponse>> {
    return this.client.get<ListResponse<ClaimResponse>>('/claims', params as Record<string, unknown>);
  }

  async get(id: number): Promise<ClaimResponse> {
    return this.client.get<ClaimResponse>(`/claims/${id}`);
  }

  async create(data: ClaimCreate): Promise<ClaimResponse> {
    return this.client.post<ClaimResponse>('/claims', data);
  }

  async update(id: number, data: Partial<ClaimCreate>): Promise<ClaimResponse> {
    return this.client.put<ClaimResponse>(`/claims/${id}`, data);
  }

  async submit(id: number): Promise<ClaimResponse> {
    return this.client.post<ClaimResponse>(`/claims/${id}/submit`);
  }

  async approve(id: number): Promise<ClaimResponse> {
    return this.client.post<ClaimResponse>(`/claims/${id}/approve`);
  }

  async reject(id: number, reason: string): Promise<ClaimResponse> {
    return this.client.post<ClaimResponse>(`/claims/${id}/reject`, { reason });
  }

  async status(id: number): Promise<ClaimResponse> {
    return this.client.get<ClaimResponse>(`/claims/${id}/status`);
  }

  async stats(): Promise<Record<string, unknown>> {
    return this.client.get('/claims/stats');
  }
}
