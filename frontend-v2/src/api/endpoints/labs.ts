import { apiGet, apiPut } from '../client';
import type { Lab, Employee } from '../types';

export async function getMyLab(): Promise<Lab> {
  return apiGet<Lab>('/labs/me');
}

export async function updateMyLab(data: Partial<Lab>): Promise<Lab> {
  return apiPut<Lab>('/labs/me', data);
}

export async function listEmployees(): Promise<Employee[]> {
  return apiGet<Employee[]>('/labs/me/employees');
}
