import { apiGet, apiPost, apiPut } from '../client';
import type { Patient, CreatePatientRequest, PaginatedResponse } from '../types';

export interface ListPatientsParams {
  search?: string;
  skip?: number;
  limit?: number;
}

export async function listPatients(params?: ListPatientsParams): Promise<PaginatedResponse<Patient>> {
  return apiGet<PaginatedResponse<Patient>>('/patients', params as Record<string, any>);
}

export async function getPatient(id: string): Promise<Patient> {
  return apiGet<Patient>(`/patients/${id}`);
}

export async function createPatient(data: CreatePatientRequest): Promise<Patient> {
  return apiPost<Patient>('/patients', data);
}

export async function updatePatient(id: string, data: Partial<Patient>): Promise<Patient> {
  return apiPut<Patient>(`/patients/${id}`, data);
}

export async function getPatientHistory(patientId: string): Promise<any[]> {
  return apiGet<any[]>(`/patient-history/${patientId}`);
}

export async function searchByPhone(phone: string, name?: string): Promise<Patient[]> {
  return apiGet<Patient[]>('/history/' + encodeURIComponent(phone), { name } as Record<string, any>);
}
