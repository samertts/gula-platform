import { apiRequest } from './api';

export interface HospitalDashboardResponse {
  hospital_id: number;
  departments: number;
  clinics: number;
  rooms: number;
  beds: { total: number; occupied: number };
  equipment: { total: number; operational: number };
  operation_theaters: { total: number; available: number };
}

export function getHospitalDashboard(hospitalId: number): Promise<HospitalDashboardResponse> {
  return apiRequest<HospitalDashboardResponse>(`/hospitals/${encodeURIComponent(String(hospitalId))}/dashboard`);
}
