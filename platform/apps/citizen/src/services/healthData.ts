import { apiRequest } from './api';
import { cacheHealthData, getCachedHealthData } from './offline';
import type {
  LabResult,
  RadiologyReport,
  Prescription,
  Vaccination,
  HealthRecord,
  HealthScore,
} from '../types';

export async function getLabResults(patientId: string): Promise<LabResult[]> {
  if (!navigator.onLine) {
    return getCachedHealthData();
  }

  try {
    const response = await apiRequest<{ results: LabResult[] }>(
      `/citizen/patients/${patientId}/lab-results`,
    );
    await cacheHealthData(response.results);
    return response.results;
  } catch {
    return getCachedHealthData();
  }
}

export async function getLabResultDetail(resultId: string): Promise<LabResult> {
  return apiRequest<LabResult>(`/citizen/lab-results/${resultId}`);
}

export async function getRadiologyReports(patientId: string): Promise<RadiologyReport[]> {
  return apiRequest<{ reports: RadiologyReport[] }>(
    `/citizen/patients/${patientId}/radiology`,
  ).then((r) => r.reports);
}

export async function getRadiologyReportDetail(reportId: string): Promise<RadiologyReport> {
  return apiRequest<RadiologyReport>(`/citizen/radiology/${reportId}`);
}

export async function getPrescriptions(patientId: string): Promise<Prescription[]> {
  return apiRequest<{ prescriptions: Prescription[] }>(
    `/citizen/patients/${patientId}/prescriptions`,
  ).then((r) => r.prescriptions);
}

export async function getVaccinations(patientId: string): Promise<Vaccination[]> {
  return apiRequest<{ vaccinations: Vaccination[] }>(
    `/citizen/patients/${patientId}/vaccinations`,
  ).then((r) => r.vaccinations);
}

export async function getMedicalHistory(patientId: string): Promise<HealthRecord[]> {
  return apiRequest<{ records: HealthRecord[] }>(
    `/citizen/patients/${patientId}/medical-history`,
  ).then((r) => r.records);
}

export async function getHealthScore(patientId: string): Promise<HealthScore> {
  return apiRequest<HealthScore>(`/citizen/patients/${patientId}/health-score`);
}

export async function getVitalTrends(
  patientId: string,
  type: string,
  period: string = '3m',
): Promise<{ date: string; value: number }[]> {
  return apiRequest<{ data: { date: string; value: number }[] }>(
    `/citizen/patients/${patientId}/trends/${type}?period=${period}`,
  ).then((r) => r.data);
}

export async function downloadReport(reportId: string, type: 'lab' | 'radiology'): Promise<string> {
  const response = await apiRequest<{ url: string }>(
    `/citizen/reports/${reportId}/download?type=${type}`,
  );
  return response.url;
}
