import { GulaClient } from '../client';
import {
  LabUpdate, LabResponse, CreateEmployeeRequest, UpdateEmployeeRequest,
  LabUserResponse, LabWorkHours, LabHoliday, LabDepartment, LabSettings,
  ListResponse, PaginationParams,
} from '../types';

export class LabsAPI {
  constructor(private client: GulaClient) {}

  async list(params?: PaginationParams & { status?: string; city?: string; tier?: string }): Promise<ListResponse<LabResponse>> {
    return this.client.get<ListResponse<LabResponse>>('/labs', params as Record<string, unknown>);
  }

  async get(id: number): Promise<LabResponse> {
    return this.client.get<LabResponse>(`/labs/${id}`);
  }

  async update(id: number, data: LabUpdate): Promise<LabResponse> {
    return this.client.put<LabResponse>(`/labs/${id}`, data);
  }

  async delete(id: number): Promise<void> {
    return this.client.delete(`/labs/${id}`);
  }

  async updateMe(data: LabUpdate): Promise<LabResponse> {
    return this.client.put<LabResponse>('/labs/me', data);
  }

  async search(query: string, params?: PaginationParams): Promise<ListResponse<LabResponse>> {
    return this.client.get<ListResponse<LabResponse>>('/labs/search', { ...params, q: query });
  }

  async nearby(lat: number, lng: number, radius?: number): Promise<ListResponse<LabResponse>> {
    return this.client.get<ListResponse<LabResponse>>('/labs/nearby', { lat, lng, radius });
  }

  async available(): Promise<LabResponse[]> {
    return this.client.get<LabResponse[]>('/labs/available');
  }

  async registrationTypes(): Promise<{ value: string; label: string }[]> {
    return this.client.get('/labs/registration-types');
  }

  async sharedLabs(params?: PaginationParams): Promise<ListResponse<LabResponse>> {
    return this.client.get<ListResponse<LabResponse>>('/labs/shared-labs', params as Record<string, unknown>);
  }

  async mapData(): Promise<{ id: number; name: string; lat: number; lng: number }[]> {
    return this.client.get('/labs/map-data');
  }

  async users(labId: number, params?: PaginationParams): Promise<ListResponse<LabUserResponse>> {
    return this.client.get<ListResponse<LabUserResponse>>(`/labs/${labId}/users`, params as Record<string, unknown>);
  }

  async addUser(labId: number, data: CreateEmployeeRequest): Promise<LabUserResponse> {
    return this.client.post<LabUserResponse>(`/labs/${labId}/users`, data);
  }

  async updateUser(labId: number, userId: number, data: UpdateEmployeeRequest): Promise<LabUserResponse> {
    return this.client.put<LabUserResponse>(`/labs/${labId}/users/${userId}`, data);
  }

  async removeUser(labId: number, userId: number): Promise<void> {
    return this.client.delete(`/labs/${labId}/users/${userId}`);
  }

  async stats(labId: number): Promise<Record<string, unknown>> {
    return this.client.get(`/labs/${labId}/stats`);
  }

  async departments(labId: number, params?: PaginationParams): Promise<ListResponse<LabDepartment>> {
    return this.client.get<ListResponse<LabDepartment>>(`/labs/${labId}/departments`, params as Record<string, unknown>);
  }

  async createDepartment(labId: number, data: { name: string; code?: string }): Promise<LabDepartment> {
    return this.client.post<LabDepartment>(`/labs/${labId}/departments`, data);
  }

  async getWorkHours(labId: number): Promise<LabWorkHours[]> {
    return this.client.get<LabWorkHours[]>(`/labs/${labId}/work-hours`);
  }

  async updateWorkHours(labId: number, data: LabWorkHours[]): Promise<LabWorkHours[]> {
    return this.client.put<LabWorkHours[]>(`/labs/${labId}/work-hours`, data);
  }

  async updateSettings(labId: number, data: LabSettings): Promise<LabSettings> {
    return this.client.put<LabSettings>(`/labs/${labId}/settings`, data);
  }

  async getLogo(labId: number): Promise<Blob> {
    return this.client.download(`/labs/${labId}/logo`);
  }

  async uploadLogo(labId: number, file: File): Promise<void> {
    const fd = new FormData();
    fd.append('logo', file);
    return this.client.upload(`/labs/${labId}/logo`, fd);
  }

  async holidays(labId: number, params?: PaginationParams): Promise<ListResponse<LabHoliday>> {
    return this.client.get<ListResponse<LabHoliday>>(`/labs/${labId}/holidays`, params as Record<string, unknown>);
  }

  async addHoliday(labId: number, data: { date: string; description: string }): Promise<LabHoliday> {
    return this.client.post<LabHoliday>(`/labs/${labId}/holidays`, data);
  }

  async removeHoliday(labId: number, holidayId: number): Promise<void> {
    return this.client.delete(`/labs/${labId}/holidays/${holidayId}`);
  }

  async addEmployee(data: CreateEmployeeRequest): Promise<LabUserResponse> {
    return this.client.post<LabUserResponse>('/labs/me/employees', data);
  }

  async updateEmployee(employeeId: number, data: UpdateEmployeeRequest): Promise<LabUserResponse> {
    return this.client.put<LabUserResponse>(`/labs/me/employees/${employeeId}`, data);
  }
}
