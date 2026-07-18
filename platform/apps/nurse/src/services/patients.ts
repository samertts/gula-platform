import { api } from './api';
import type { Patient, Admission, BedAssignment } from '@/utils/types';

export const patientsService = {
  getList: async (ward?: string) => {
    const params = ward ? `?ward=${ward}` : '';
    return api.get<Patient[]>(`/nurse/patients${params}`);
  },

  getById: async (id: string) => {
    return api.get<Patient>(`/nurse/patients/${id}`);
  },

  getByBed: async (ward: string, bed: string) => {
    return api.get<Patient>(`/nurse/patients/by-bed?ward=${ward}&bed=${bed}`);
  },

  getAdmissions: async (ward?: string) => {
    const params = ward ? `?ward=${ward}` : '';
    return api.get<Admission[]>(`/nurse/admissions${params}`);
  },

  admitPatient: async (data: Partial<Admission>) => {
    return api.post<Admission>('/nurse/admissions', data);
  },

  dischargePatient: async (id: string, data: { dischargeDate: string; notes?: string }) => {
    return api.post(`/nurse/patients/${id}/discharge`, data);
  },

  getBedAssignments: async (ward: string) => {
    return api.get<BedAssignment[]>(`/nurse/ward/${ward}/beds`);
  },

  assignBed: async (patientId: string, ward: string, bed: string) => {
    return api.post(`/nurse/patients/${patientId}/assign-bed`, { ward, bed });
  },

  search: async (query: string) => {
    return api.get<Patient[]>(`/nurse/patients/search?q=${encodeURIComponent(query)}`);
  },

  verifyBedside: async (patientId: string, method: 'qr' | 'barcode' | 'manual', identifier: string) => {
    return api.post<{ verified: boolean; patient: Patient }>(`/nurse/patients/${patientId}/verify`, { method, identifier });
  },
};
