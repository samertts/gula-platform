import { api } from './api';
import type { VitalSigns } from '@/utils/types';

export const vitalsService = {
  getList: async (patientId: string) => {
    return api.get<VitalSigns[]>(`/nurse/vitals?patientId=${patientId}`);
  },

  getLatest: async (patientId: string) => {
    return api.get<VitalSigns>(`/nurse/vitals/latest/${patientId}`);
  },

  getWardVitals: async (ward: string) => {
    return api.get<VitalSigns[]>(`/nurse/vitals/ward/${ward}`);
  },

  record: async (data: Omit<VitalSigns, 'id' | 'recordedAt' | 'recordedBy' | 'earlyWarningScore'>) => {
    return api.post<VitalSigns>('/nurse/vitals', data);
  },

  getChart: async (patientId: string, hours: number = 24) => {
    return api.get<VitalSigns[]>(`/nurse/vitals/chart/${patientId}?hours=${hours}`);
  },

  calculateEWS: (vitals: Partial<VitalSigns>): number => {
    let score = 0;

    if (vitals.temperature != null) {
      if (vitals.temperature <= 35) score += 3;
      else if (vitals.temperature < 36) score += 1;
      else if (vitals.temperature > 39) score += 2;
      else if (vitals.temperature >= 38.1) score += 1;
    }

    if (vitals.heartRate != null) {
      if (vitals.heartRate <= 40) score += 3;
      else if (vitals.heartRate < 50) score += 1;
      else if (vitals.heartRate > 130) score += 3;
      else if (vitals.heartRate > 110) score += 2;
      else if (vitals.heartRate > 90) score += 1;
    }

    if (vitals.respiratoryRate != null) {
      if (vitals.respiratoryRate <= 8) score += 3;
      else if (vitals.respiratoryRate < 11) score += 1;
      else if (vitals.respiratoryRate > 30) score += 3;
      else if (vitals.respiratoryRate > 24) score += 2;
      else if (vitals.respiratoryRate > 20) score += 1;
    }

    if (vitals.bloodPressureSystolic != null) {
      if (vitals.bloodPressureSystolic <= 90) score += 3;
      else if (vitals.bloodPressureSystolic < 100) score += 2;
      else if (vitals.bloodPressureSystolic > 220) score += 3;
      else if (vitals.bloodPressureSystolic > 199) score += 2;
    }

    if (vitals.oxygenSaturation != null) {
      if (vitals.oxygenSaturation <= 85) score += 3;
      else if (vitals.oxygenSaturation < 90) score += 2;
      else if (vitals.oxygenSaturation <= 93) score += 1;
    }

    if (vitals.consciousness) {
      const conscious = vitals.consciousness.toLowerCase();
      if (conscious === 'unresponsive' || conscious === 'pain') score += 3;
      else if (conscious === 'voice' || conscious === 'confused') score += 1;
    }

    return score;
  },

  getEWSGrade: (score: number): { grade: string; color: string; action: string } => {
    if (score >= 7) return { grade: 'حرج', color: 'text-danger-500', action: 'إنذار سريري - تقييم فوري' };
    if (score >= 5) return { grade: 'عالٍ', color: 'text-warning-500', action: 'مراقبة دقيقة - إبلاغ الطبيب' };
    if (score >= 3) return { grade: 'متوسط', color: 'text-warning-400', action: 'زيادة وتيرة المراقبة' };
    return { grade: 'منخفض', color: 'text-success-500', action: 'مراقبة روتينية' };
  },
};
