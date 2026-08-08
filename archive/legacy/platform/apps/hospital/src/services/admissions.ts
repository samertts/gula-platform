import { apiRequest } from './api';

export interface Admission {
  id: string;
  patientId: string;
  patientName: string;
  patientNameAr: string;
  gender: 'male' | 'female';
  dateOfBirth: string;
  phone: string;
  nationalId: string;
  admissionDate: string;
  department: string;
  departmentAr: string;
  ward: string;
  wardAr: string;
  bedId: string | null;
  diagnosis: string;
  diagnosisAr: string;
  referringDoctor: string;
  referringDoctorAr: string;
  admittingDoctor: string;
  admittingDoctorAr: string;
  insuranceProvider: string;
  insuranceNumber: string;
  emergencyContact: string;
  emergencyPhone: string;
  status: 'pending' | 'active' | 'transferred' | 'discharged';
  notes: string;
  createdAt: string;
  updatedAt: string;
}

export interface AdmissionCreatePayload {
  patientId?: string;
  patientName: string;
  patientNameAr: string;
  gender: 'male' | 'female';
  dateOfBirth: string;
  phone: string;
  nationalId: string;
  department: string;
  ward: string;
  diagnosis: string;
  diagnosisAr: string;
  referringDoctor: string;
  referringDoctorAr: string;
  insuranceProvider: string;
  insuranceNumber: string;
  emergencyContact: string;
  emergencyPhone: string;
  notes?: string;
}

export async function getAdmissions(params?: {
  status?: string;
  department?: string;
  search?: string;
  page?: number;
  limit?: number;
}): Promise<{ data: Admission[]; total: number; page: number }> {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.set('status', params.status);
  if (params?.department) searchParams.set('department', params.department);
  if (params?.search) searchParams.set('search', params.search);
  if (params?.page) searchParams.set('page', String(params.page));
  if (params?.limit) searchParams.set('limit', String(params.limit));
  const qs = searchParams.toString();
  return apiRequest(`/hospital/admissions${qs ? `?${qs}` : ''}`);
}

export async function getAdmission(id: string): Promise<Admission> {
  return apiRequest(`/hospital/admissions/${id}`);
}

export async function createAdmission(data: AdmissionCreatePayload): Promise<Admission> {
  return apiRequest('/hospital/admissions', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateAdmission(id: string, data: Partial<Admission>): Promise<Admission> {
  return apiRequest(`/hospital/admissions/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function dischargePatient(id: string, dischargeNotes?: string): Promise<Admission> {
  return apiRequest(`/hospital/admissions/${id}/discharge`, {
    method: 'POST',
    body: JSON.stringify({ dischargeNotes }),
  });
}

export async function transferPatient(
  id: string,
  targetDepartment: string,
  targetWard: string,
  targetBedId?: string,
): Promise<Admission> {
  return apiRequest(`/hospital/admissions/${id}/transfer`, {
    method: 'POST',
    body: JSON.stringify({ targetDepartment, targetWard, targetBedId }),
  });
}
