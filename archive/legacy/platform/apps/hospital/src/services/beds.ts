import { apiRequest } from './api';

export interface Bed {
  id: string;
  wardId: string;
  ward: string;
  wardAr: string;
  department: string;
  departmentAr: string;
  room: string;
  bedNumber: string;
  status: 'available' | 'occupied' | 'reserved' | 'maintenance' | 'cleaning';
  patientId: string | null;
  patientName: string | null;
  patientNameAr: string | null;
  admissionId: string | null;
  isIsolation: boolean;
  equipment: string[];
  lastCleaned: string | null;
  notes: string;
  createdAt: string;
  updatedAt: string;
}

export interface Ward {
  id: string;
  name: string;
  nameAr: string;
  department: string;
  departmentAr: string;
  floor: number;
  totalBeds: number;
  availableBeds: number;
  occupiedBeds: number;
  maintenanceBeds: number;
  isolationBeds: number;
}

export async function getBeds(params?: {
  wardId?: string;
  department?: string;
  status?: string;
}): Promise<Bed[]> {
  const searchParams = new URLSearchParams();
  if (params?.wardId) searchParams.set('wardId', params.wardId);
  if (params?.department) searchParams.set('department', params.department);
  if (params?.status) searchParams.set('status', params.status);
  const qs = searchParams.toString();
  return apiRequest(`/hospital/beds${qs ? `?${qs}` : ''}`);
}

export async function getWards(): Promise<Ward[]> {
  return apiRequest('/hospital/wards');
}

export async function assignBed(
  bedId: string,
  patientId: string,
  admissionId: string,
): Promise<Bed> {
  return apiRequest(`/hospital/beds/${bedId}/assign`, {
    method: 'POST',
    body: JSON.stringify({ patientId, admissionId }),
  });
}

export async function releaseBed(bedId: string): Promise<Bed> {
  return apiRequest(`/hospital/beds/${bedId}/release`, {
    method: 'POST',
  });
}

export async function setBedMaintenance(
  bedId: string,
  maintenance: boolean,
  notes?: string,
): Promise<Bed> {
  return apiRequest(`/hospital/beds/${bedId}/maintenance`, {
    method: 'POST',
    body: JSON.stringify({ maintenance, notes }),
  });
}

export async function getBedOccupancyStats(): Promise<{
  total: number;
  available: number;
  occupied: number;
  maintenance: number;
  reserved: number;
  cleaning: number;
  occupancyRate: number;
  isolationOccupied: number;
  totalIsolation: number;
}> {
  return apiRequest('/hospital/beds/stats');
}
