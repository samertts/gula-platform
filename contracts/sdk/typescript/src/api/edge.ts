import { GulaClient } from '../client';
import {
  RegisterDeviceRequest, RegisterDeviceResponse, DeviceSummary,
  DeviceDetail, TaskSubmitRequest, TaskSummary, TaskDetail,
  PolicyView, PolicyUpdate, HeartbeatRequest, HeartbeatResponse,
  TaskResultRequest, ModelRegisterRequest, ModelInfo,
  ModelStatusUpdate, ModelAssignRequest, ListResponse, PaginationParams,
  EdgeSite,
} from '../types';

export class EdgeAPI {
  constructor(private client: GulaClient) {}

  // ── Devices ──
  async registerDevice(data: RegisterDeviceRequest): Promise<RegisterDeviceResponse> {
    return this.client.post<RegisterDeviceResponse>('/edge/devices/register', data);
  }

  async listDevices(params?: PaginationParams): Promise<ListResponse<DeviceSummary>> {
    return this.client.get<ListResponse<DeviceSummary>>('/edge/devices', params as Record<string, unknown>);
  }

  async getDevice(deviceId: string): Promise<DeviceDetail> {
    return this.client.get<DeviceDetail>(`/edge/devices/${deviceId}`);
  }

  async revokeDevice(deviceId: string): Promise<void> {
    return this.client.post(`/edge/devices/${deviceId}/revoke`);
  }

  async quarantineDevice(deviceId: string): Promise<void> {
    return this.client.post(`/edge/devices/${deviceId}/quarantine`);
  }

  // ── Tasks ──
  async submitTask(data: TaskSubmitRequest): Promise<{ task_uid: string }> {
    return this.client.post<{ task_uid: string }>('/edge/tasks', data);
  }

  async listTasks(params?: PaginationParams & { status?: string; kind?: string }): Promise<ListResponse<TaskSummary>> {
    return this.client.get<ListResponse<TaskSummary>>('/edge/tasks', params as Record<string, unknown>);
  }

  async getTask(taskUid: string): Promise<TaskDetail> {
    return this.client.get<TaskDetail>(`/edge/tasks/${taskUid}`);
  }

  async cancelTask(taskUid: string): Promise<void> {
    return this.client.post(`/edge/tasks/${taskUid}/cancel`);
  }

  // ── Policy ──
  async getPolicy(): Promise<PolicyView> {
    return this.client.get<PolicyView>('/edge/policy');
  }

  async updatePolicy(data: PolicyUpdate): Promise<PolicyView> {
    return this.client.put<PolicyView>('/edge/policy', data);
  }

  // ── Agent Endpoints ──
  async heartbeat(data: HeartbeatRequest): Promise<HeartbeatResponse> {
    return this.client.post<HeartbeatResponse>('/edge/agent/heartbeat', data);
  }

  async reportTaskResult(taskUid: string, data: TaskResultRequest): Promise<void> {
    return this.client.post(`/edge/agent/tasks/${taskUid}/result`, data);
  }

  // ── Models ──
  async registerModel(data: ModelRegisterRequest): Promise<ModelInfo> {
    return this.client.post<ModelInfo>('/edge/models', data);
  }

  async listModels(params?: PaginationParams): Promise<ListResponse<ModelInfo>> {
    return this.client.get<ListResponse<ModelInfo>>('/edge/models', params as Record<string, unknown>);
  }

  async updateModelStatus(modelUid: string, data: ModelStatusUpdate): Promise<ModelInfo> {
    return this.client.put<ModelInfo>(`/edge/models/${modelUid}/status`, data);
  }

  async assignModel(modelUid: string, data: ModelAssignRequest): Promise<void> {
    return this.client.post(`/edge/models/${modelUid}/assign`, data);
  }

  // ── Sites ──
  async listSites(params?: PaginationParams): Promise<ListResponse<EdgeSite>> {
    return this.client.get<ListResponse<EdgeSite>>('/edge/sites', params as Record<string, unknown>);
  }

  async createSite(data: { name: string; lab_id: number }): Promise<EdgeSite> {
    return this.client.post<EdgeSite>('/edge/sites', data);
  }

  async getSite(siteId: number): Promise<EdgeSite> {
    return this.client.get<EdgeSite>(`/edge/sites/${siteId}`);
  }

  async updateSite(siteId: number, data: Partial<EdgeSite>): Promise<EdgeSite> {
    return this.client.put<EdgeSite>(`/edge/sites/${siteId}`, data);
  }

  async deleteSite(siteId: number): Promise<void> {
    return this.client.delete(`/edge/sites/${siteId}`);
  }

  async triggerSync(): Promise<void> {
    return this.client.post('/edge/sync');
  }

  async getSyncStatus(): Promise<{ last_sync: string; pending: number }> {
    return this.client.get('/edge/sync/status');
  }
}
