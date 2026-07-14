import { GulaClient } from '../client';
import {
  CreateLabRequest, CreateUserRequest, ChangeRoleRequest,
  KillSwitchRequest, ListResponse, PaginationParams, LabResponse,
  UserBrief, SetTierBody, FeatureFlagBody, TierInfo,
} from '../types';

export class AdminAPI {
  constructor(private client: GulaClient) {}

  async listUsers(params?: PaginationParams): Promise<ListResponse<UserBrief>> {
    return this.client.get<ListResponse<UserBrief>>('/admin/users', params as Record<string, unknown>);
  }

  async getUser(userId: number): Promise<UserBrief> {
    return this.client.get<UserBrief>(`/admin/users/${userId}`);
  }

  async createUser(data: CreateUserRequest): Promise<UserBrief> {
    return this.client.post<UserBrief>('/admin/users', data);
  }

  async updateUser(userId: number, data: Partial<CreateUserRequest>): Promise<UserBrief> {
    return this.client.put<UserBrief>(`/admin/users/${userId}`, data);
  }

  async deleteUser(userId: number): Promise<void> {
    return this.client.delete(`/admin/users/${userId}`);
  }

  async deactivateUser(userId: number): Promise<UserBrief> {
    return this.client.put<UserBrief>(`/admin/users/${userId}/deactivate`);
  }

  async reactivateUser(userId: number): Promise<UserBrief> {
    return this.client.put<UserBrief>(`/admin/users/${userId}/reactivate`);
  }

  async changeUserRole(userId: number, data: ChangeRoleRequest): Promise<UserBrief> {
    return this.client.put<UserBrief>(`/admin/users/${userId}/role`, data);
  }

  async listLabs(params?: PaginationParams): Promise<ListResponse<LabResponse>> {
    return this.client.get<ListResponse<LabResponse>>('/admin/labs', params as Record<string, unknown>);
  }

  async createLab(data: CreateLabRequest): Promise<LabResponse> {
    return this.client.post<LabResponse>('/admin/labs', data);
  }

  async updateLab(labId: number, data: Partial<CreateLabRequest>): Promise<LabResponse> {
    return this.client.put<LabResponse>(`/admin/labs/${labId}`, data);
  }

  async deleteLab(labId: number): Promise<void> {
    return this.client.delete(`/admin/labs/${labId}`);
  }

  async stats(): Promise<Record<string, unknown>> {
    return this.client.get('/admin/stats');
  }

  async getSystemConfig(): Promise<Record<string, unknown>> {
    return this.client.get('/admin/system/config');
  }

  async updateSystemConfig(data: Record<string, unknown>): Promise<Record<string, unknown>> {
    return this.client.post('/admin/system/config', data);
  }

  async triggerMaintenance(data: { type: string; reason?: string }): Promise<void> {
    return this.client.post('/admin/maintenance', data);
  }

  async activityLog(params?: PaginationParams): Promise<ListResponse<{ action: string; user: string; timestamp: string }>> {
    return this.client.get('/admin/activity-log', params as Record<string, unknown>);
  }

  async serviceStatus(): Promise<Record<string, unknown>> {
    return this.client.get('/admin/service-status');
  }

  async systemHealth(): Promise<Record<string, unknown>> {
    return this.client.get('/admin/system/health');
  }

  async systemLogs(params?: PaginationParams): Promise<ListResponse<Record<string, unknown>>> {
    return this.client.get('/admin/logs', params as Record<string, unknown>);
  }

  async killSwitch(data: KillSwitchRequest): Promise<void> {
    return this.client.post('/admin/kill-switch', data);
  }

  // ── Tier Management ──
  async listTiers(params?: PaginationParams): Promise<ListResponse<TierInfo>> {
    return this.client.get<ListResponse<TierInfo>>('/tiers', params as Record<string, unknown>);
  }

  async getTier(tierId: number): Promise<TierInfo> {
    return this.client.get<TierInfo>(`/tiers/${tierId}`);
  }

  async createTier(data: TierInfo): Promise<TierInfo> {
    return this.client.post<TierInfo>('/tiers', data);
  }

  async updateTier(tierId: number, data: Partial<TierInfo>): Promise<TierInfo> {
    return this.client.put<TierInfo>(`/tiers/${tierId}`, data);
  }

  async deleteTier(tierId: number): Promise<void> {
    return this.client.delete(`/tiers/${tierId}`);
  }

  async assignLabToTier(tierId: number, labId: number): Promise<void> {
    return this.client.post(`/tiers/${tierId}/assign`, { lab_id: labId });
  }

  async setLabTier(labId: number, data: SetTierBody): Promise<void> {
    return this.client.post(`/admin/tiers/${labId}`, data);
  }

  async setFeatureFlag(labId: number, data: FeatureFlagBody): Promise<void> {
    return this.client.post(`/admin/tiers/flags/${labId}`, data);
  }

  async getTierUsage(): Promise<{ tier: string; labs_count: number; total_patients: number; total_results: number }[]> {
    return this.client.get('/tiers/usage');
  }

  async getTierLimits(): Promise<Record<string, Record<string, number>>> {
    return this.client.get('/tiers/limits');
  }
}
