import { api } from './api';
import type { Medication } from '@/utils/types';

export const medicationsService = {
  getList: async (patientId?: string) => {
    const params = patientId ? `?patientId=${patientId}` : '';
    return api.get<Medication[]>(`/nurse/medications${params}`);
  },

  getScheduled: async (ward?: string) => {
    const params = ward ? `?ward=${ward}` : '';
    return api.get<Medication[]>(`/nurse/medications/scheduled${params}`);
  },

  getById: async (id: string) => {
    return api.get<Medication>(`/nurse/medications/${id}`);
  },

  administer: async (id: string, data: {
    administeredTime: string;
    rightsVerified: Medication['rightsVerified'];
    notes?: string;
  }) => {
    return api.post<Medication>(`/nurse/medications/${id}/administer`, data);
  },

  hold: async (id: string, reason: string) => {
    return api.post(`/nurse/medications/${id}/hold`, { reason });
  },

  recordRefusal: async (id: string, reason: string) => {
    return api.post(`/nurse/medications/${id}/refuse`, { reason });
  },

  verifyBarcode: async (barcode: string) => {
    return api.get<Medication>(`/nurse/medications/verify-barcode?code=${encodeURIComponent(barcode)}`);
  },

  getSchedule: async (ward: string, date: string) => {
    return api.get<Medication[]>(`/nurse/medications/schedule?ward=${ward}&date=${date}`);
  },
};
