import { apiRequest, cachePatientData, getCachedPatientData } from './api';

export interface Patient {
  id: string;
  nationalId?: string;
  sndhsHealthId?: string;
  name: string;
  nameAr: string;
  dateOfBirth: string;
  gender: 'male' | 'female';
  bloodType?: string;
  phone?: string;
  email?: string;
  address?: string;
  city?: string;
  governorate?: string;
  allergies: string[];
  chronicConditions: string[];
  medications: string[];
  emergencyContact?: {
    name: string;
    phone: string;
    relation: string;
  };
  mpiScore?: number;
  mpiMatchedIds?: string[];
  labId: string;
  createdAt: string;
  updatedAt: string;
}

export interface PatientSearchParams {
  query?: string;
  nationalId?: string;
  name?: string;
  phone?: string;
  dateOfBirth?: string;
  gender?: string;
  bloodType?: string;
  city?: string;
  governorate?: string;
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface PatientSearchResult {
  patients: Patient[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  mpiMatchCount?: number;
}

export interface MpiMatchResult {
  patientId: string;
  matchedPatientId: string;
  score: number;
  matchedFields: string[];
  isConfirmed: boolean;
}

export async function searchPatients(params: PatientSearchParams): Promise<PatientSearchResult> {
  const queryParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '' && value !== null) {
      queryParams.set(key, String(value));
    }
  });
  return apiRequest<PatientSearchResult>(`/patients?${queryParams.toString()}`);
}

export async function getPatient(patientId: string): Promise<Patient> {
  const cached = await getCachedPatientData(patientId);
  try {
    const data = await apiRequest<Patient>(`/patients/${patientId}`);
    await cachePatientData(patientId, data);
    return data;
  } catch (error) {
    if (cached) return cached as Patient;
    throw error;
  }
}

export async function createPatient(patient: Omit<Patient, 'id' | 'createdAt' | 'updatedAt'>): Promise<Patient> {
  return apiRequest<Patient>('/patients', {
    method: 'POST',
    body: JSON.stringify(patient),
    offlinePriority: 'high',
  });
}

export async function updatePatient(patientId: string, updates: Partial<Patient>): Promise<Patient> {
  return apiRequest<Patient>(`/patients/${patientId}`, {
    method: 'PATCH',
    body: JSON.stringify(updates),
    offlinePriority: 'high',
  });
}

export async function searchMpi(query: string): Promise<MpiMatchResult[]> {
  return apiRequest<MpiMatchResult[]>(`/patients/mpi/search?query=${encodeURIComponent(query)}`);
}

export async function confirmMpiMatch(patientId: string, matchedPatientId: string): Promise<void> {
  return apiRequest(`/patients/${patientId}/mpi/confirm`, {
    method: 'POST',
    body: JSON.stringify({ matchedPatientId }),
  });
}

export async function rejectMpiMatch(patientId: string, matchedPatientId: string): Promise<void> {
  return apiRequest(`/patients/${patientId}/mpi/reject`, {
    method: 'POST',
    body: JSON.stringify({ matchedPatientId }),
  });
}

export async function mergePatients(primaryId: string, secondaryId: string): Promise<Patient> {
  return apiRequest<Patient>(`/patients/${primaryId}/merge`, {
    method: 'POST',
    body: JSON.stringify({ secondaryPatientId: secondaryId }),
  });
}

export async function getPatientByNationalId(nationalId: string): Promise<Patient | null> {
  try {
    return await apiRequest<Patient>(`/patients/by-national-id/${nationalId}`);
  } catch {
    return null;
  }
}

export async function getPatientByHealthId(healthId: string): Promise<Patient | null> {
  try {
    return await apiRequest<Patient>(`/patients/by-health-id/${healthId}`);
  } catch {
    return null;
  }
}

export async function getPatientByPhone(phone: string): Promise<Patient | null> {
  try {
    return await apiRequest<Patient>(`/patients/by-phone/${phone}`);
  } catch {
    return null;
  }
}

export async function getRecentPatients(page = 1, pageSize = 20): Promise<PatientSearchResult> {
  return apiRequest<PatientSearchResult>(`/patients/recent?page=${page}&pageSize=${pageSize}`);
}

export async function deletePatient(patientId: string): Promise<void> {
  return apiRequest(`/patients/${patientId}`, { method: 'DELETE' });
}
