import { apiRequest } from './api';

export interface Department {
  id: string;
  name: string;
  nameAr: string;
  code: string;
  description: string;
  descriptionAr: string;
  floor: number;
  headDoctor: string;
  headDoctorAr: string;
  headNurse: string;
  headNurseAr: string;
  totalStaff: number;
  totalDoctors: number;
  totalNurses: number;
  totalBeds: number;
  availableBeds: number;
  occupiedBeds: number;
  activePatients: number;
  admissionsToday: number;
  dischargesToday: number;
  avgLengthOfStay: number;
  bedOccupancyRate: number;
  status: 'active' | 'inactive' | 'under_maintenance';
  createdAt: string;
  updatedAt: string;
}

export interface DepartmentMetric {
  id: string;
  departmentId: string;
  date: string;
  admissions: number;
  discharges: number;
  transfersIn: number;
  transfersOut: number;
  deaths: number;
  occupiedBeds: number;
  availableBeds: number;
  avgLengthOfStay: number;
  readmissionRate: number;
  infectionRate: number;
  patientSatisfaction: number;
}

export async function getDepartments(): Promise<Department[]> {
  return apiRequest('/hospital/departments');
}

export async function getDepartment(id: string): Promise<Department> {
  return apiRequest(`/hospital/departments/${id}`);
}

export async function getDepartmentMetrics(
  departmentId: string,
  period?: 'daily' | 'weekly' | 'monthly',
): Promise<DepartmentMetric[]> {
  const params = period ? `?period=${period}` : '';
  return apiRequest(`/hospital/departments/${departmentId}/metrics${params}`);
}

export async function getDepartmentStats(): Promise<{
  totalDepartments: number;
  totalBeds: number;
  totalOccupied: number;
  totalAvailable: number;
  overallOccupancyRate: number;
  avgLengthOfStay: number;
  admissionsLast24h: number;
  dischargesLast24h: number;
}> {
  return apiRequest('/hospital/departments/stats');
}
