import { GulaClient } from '../client';
import {
  PatientCreate, PatientUpdate, PatientResponse, PatientHistory,
  ListResponse, PaginationParams, QueryParams, ScanRequest,
  ConvertGuestRequest,
} from '../types';

export class PatientsAPI {
  constructor(private client: GulaClient) {}

  async list(params?: PaginationParams & { gender?: string; status?: string; lab_id?: number }): Promise<ListResponse<PatientResponse>> {
    return this.client.get<ListResponse<PatientResponse>>('/patients', params as Record<string, unknown>);
  }

  async get(id: number): Promise<PatientResponse> {
    return this.client.get<PatientResponse>(`/patients/${id}`);
  }

  async create(data: PatientCreate): Promise<PatientResponse> {
    return this.client.post<PatientResponse>('/patients', data);
  }

  async update(id: number, data: PatientUpdate): Promise<PatientResponse> {
    return this.client.put<PatientResponse>(`/patients/${id}`, data);
  }

  async delete(id: number): Promise<void> {
    return this.client.delete(`/patients/${id}`);
  }

  async search(query: string, params?: PaginationParams): Promise<ListResponse<PatientResponse>> {
    return this.client.get<ListResponse<PatientResponse>>('/patients/search', { ...params, q: query });
  }

  async history(id: number, params?: PaginationParams): Promise<PatientHistory> {
    return this.client.get<PatientHistory>(`/patients/${id}/history`, params as Record<string, unknown>);
  }

  async merge(id: number, targetId: number): Promise<void> {
    return this.client.put(`/patients/${id}/merge`, { target_patient_id: targetId });
  }

  async lookupByPhone(phone: string): Promise<PatientResponse> {
    return this.client.get<PatientResponse>(`/patients/phone/${encodeURIComponent(phone)}`);
  }

  async stats(): Promise<Record<string, unknown>> {
    return this.client.get('/patients/stats');
  }

  async activity(params?: PaginationParams): Promise<ListResponse<PatientResponse>> {
    return this.client.get<ListResponse<PatientResponse>>('/patients/activity', params as Record<string, unknown>);
  }

  async convertGuest(data: ConvertGuestRequest): Promise<PatientResponse> {
    return this.client.post<PatientResponse>('/patients/convert-guest', data);
  }

  async exportCsv(params?: QueryParams): Promise<Blob> {
    return this.client.download('/patients/export-csv?' + new URLSearchParams(
      Object.entries(params ?? {}).map(([k, v]) => [k, String(v)])
    ).toString(), 'patients.csv');
  }

  async bulkAssignLab(data: { patient_ids: number[]; lab_id: number }): Promise<void> {
    return this.client.post('/patients/bulk-assign-lab', data);
  }

  async scanCard(data: ScanRequest): Promise<PatientResponse> {
    return this.client.post<PatientResponse>('/patient-card/scan', data);
  }
}
