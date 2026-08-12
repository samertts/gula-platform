import { cacheHealthData, getCachedHealthData } from './offline';
import { apiRequest } from './api';
import type {
  LabResult,
  RadiologyReport,
  Prescription,
  Vaccination,
  HealthRecord,
  HealthScore,
} from '../types';

export interface CitizenDashboard {
  appointments?: { upcoming?: number };
  medications?: { active?: number };
  laboratory?: { recent_results?: number };
  radiology?: { recent_studies?: number };
  family?: { members?: number };
  notifications?: { unread?: number };
  certificates?: { active?: number };
}

function asRecord(value: unknown): Record<string, unknown> {
  return typeof value === 'object' && value !== null ? value as Record<string, unknown> : {};
}

function asText(value: unknown, fallback = ''): string {
  return typeof value === 'string' || typeof value === 'number' ? String(value) : fallback;
}

function asDate(value: unknown): string {
  return asText(value, new Date(0).toISOString());
}

function normalizeFlag(value: unknown): LabResult['flag'] {
  const flag = asText(value).toUpperCase();
  if (flag === 'H' || flag === 'L' || flag === 'C') return flag;
  return 'N';
}

function normalizeLabResult(value: unknown): LabResult {
  const item = asRecord(value);
  const low = item.reference_low;
  const high = item.reference_high;
  const referenceRange = item.reference_range
    ? asText(item.reference_range)
    : low !== undefined || high !== undefined ? `${asText(low, '—')}–${asText(high, '—')}` : '';
  const status = asText(item.status);
  return {
    id: asText(item.id),
    patientId: asText(item.patient_id),
    orderId: asText(item.order_id),
    labName: asText(item.lab_name, 'مختبر GULA'),
    labId: asText(item.lab_id),
    testName: asText(item.test_name),
    category: asText(item.category, 'مختبر'),
    value: asText(item.value_text ?? item.value),
    unit: asText(item.unit),
    referenceRange,
    flag: normalizeFlag(item.flag_code ?? item.flag),
    interpretation: asText(item.interpretation),
    performedDate: asDate(item.collected_at ?? item.performed_date),
    verifiedDate: asText(item.verified_date),
    verifiedBy: asText(item.verified_by),
    status: status === 'validated' || Boolean(item.is_validated) ? 'verified' : status === 'pending' ? 'pending' : 'completed',
  };
}

function normalizeRadiologyReport(value: unknown): RadiologyReport {
  const item = asRecord(value);
  const allowedModalities: RadiologyReport['modality'][] = ['X-ray', 'CT', 'MRI', 'Ultrasound', 'Mammography', 'PET', 'Other'];
  const rawModality = asText(item.modality);
  const modality = allowedModalities.includes(rawModality as RadiologyReport['modality'])
    ? rawModality as RadiologyReport['modality']
    : 'Other';
  const rawStatus = asText(item.status);
  return {
    id: asText(item.study_id),
    patientId: asText(item.citizen_id),
    studyId: asText(item.study_id),
    modality,
    bodyPart: asText(item.body_part),
    findings: asText(item.findings),
    impression: asText(item.impression),
    radiologist: asText(item.radiologist_name),
    facility: asText(item.facility_name, 'مرفق صحي GULA'),
    studyDate: asDate(item.performed_at ?? item.requested_at),
    reportDate: asDate(item.reported_at ?? item.performed_at ?? item.requested_at),
    status: rawStatus === 'final' || rawStatus === 'amended' ? rawStatus : 'preliminary',
    pdfUrl: asText(item.report_url),
    imageUrls: [],
  };
}

function normalizePrescription(value: unknown): Prescription {
  const item = asRecord(value);
  const route = asText(item.route);
  const allowedRoutes: Prescription['route'][] = ['oral', 'topical', 'injection', 'inhalation', 'other'];
  return {
    id: asText(item.medication_id),
    patientId: asText(item.citizen_id),
    medicationName: asText(item.medication_name),
    dosage: asText(item.dosage_text),
    frequency: asText(item.frequency),
    route: allowedRoutes.includes(route as Prescription['route']) ? route as Prescription['route'] : 'other',
    quantity: 0,
    refills: 0,
    prescribedBy: asText(item.prescriber),
    prescribedDate: asDate(item.date_started),
    expiryDate: '',
    status: asText(item.status) === 'active' ? 'active' : 'completed',
    notes: asText(item.medication_name_ar),
    isControlled: false,
  };
}

function normalizeVaccination(value: unknown): Vaccination {
  const item = asRecord(value);
  const rawStatus = asText(item.status);
  return {
    id: asText(item.id),
    patientId: asText(item.citizen_id),
    vaccineName: asText(item.vaccine_name),
    doseNumber: Number(item.dose_number) || 1,
    totalDoses: Number(item.total_doses) || 1,
    administeredDate: asDate(item.date_administered),
    administeredBy: asText(item.administered_by),
    facility: asText(item.facility_name),
    batchNumber: asText(item.lot_number),
    nextDoseDate: asText(item.next_due_date),
    status: rawStatus === 'scheduled' || rawStatus === 'overdue' ? rawStatus : 'completed',
    notes: asText(item.notes),
  };
}

export async function getCitizenDashboard(): Promise<CitizenDashboard> {
  return apiRequest<CitizenDashboard>('/citizen-platform/me/dashboard');
}

export async function getLabResults(patientId: string): Promise<LabResult[]> {
  void patientId;
  if (!navigator.onLine) return getCachedHealthData();

  try {
    const response = await apiRequest<{ results: unknown[] }>('/citizen/results?limit=50&offset=0');
    const results = response.results.map(normalizeLabResult);
    await cacheHealthData(results);
    return results;
  } catch {
    return getCachedHealthData();
  }
}

export async function getLabResultDetail(resultId: string): Promise<LabResult> {
  return apiRequest<LabResult>(`/citizen/lab-results/${resultId}`);
}

export async function getRadiologyReports(patientId: string): Promise<RadiologyReport[]> {
  const response = await apiRequest<{ studies: unknown[] }>(`/citizen-platform/radiology/${encodeURIComponent(patientId)}`);
  return response.studies.map(normalizeRadiologyReport);
}

export async function getRadiologyReportDetail(reportId: string): Promise<RadiologyReport> {
  return apiRequest<RadiologyReport>(`/radiology/studies/${encodeURIComponent(reportId)}`);
}

export async function getPrescriptions(patientId: string): Promise<Prescription[]> {
  const response = await apiRequest<{ medications: unknown[] }>(`/citizen-platform/medications/${encodeURIComponent(patientId)}`);
  return response.medications.map(normalizePrescription);
}

export async function getVaccinations(patientId: string): Promise<Vaccination[]> {
  const response = await apiRequest<{ vaccinations: unknown[] }>(`/citizen-platform/vaccinations/${encodeURIComponent(patientId)}`);
  return response.vaccinations.map(normalizeVaccination);
}

export async function getMedicalHistory(patientId: string): Promise<HealthRecord[]> {
  void patientId;
  const response = await apiRequest<{ timeline?: unknown[] }>('/citizen/health-record');
  return (response.timeline || []).map((value): HealthRecord => {
    const item = asRecord(value);
    return {
      id: `${asText(item.date)}-${asText(item.lab)}`,
      patientId: '',
      type: 'visit',
      title: 'زيارة وفحوصات مخبرية',
      description: asText(item.status),
      provider: asText(item.lab),
      providerId: '',
      facilityName: asText(item.lab),
      date: asDate(item.date),
      createdAt: asDate(item.date),
      metadata: { tests: item.tests },
    };
  });
}

/** The backend does not expose a clinical score endpoint; do not fabricate one. */
export async function getHealthScore(_patientId: string): Promise<HealthScore | null> {
  return null;
}

export async function getVitalTrends(
  patientId: string,
  type: string,
  period = '3m',
): Promise<{ date: string; value: number }[]> {
  return apiRequest<{ data: { date: string; value: number }[] }>(
    `/citizen-platform/trends/${encodeURIComponent(patientId)}/${encodeURIComponent(type)}?period=${encodeURIComponent(period)}`,
  ).then((r) => r.data);
}

export async function downloadReport(reportId: string, type: 'lab' | 'radiology'): Promise<string> {
  const response = await apiRequest<{ url: string }>(
    `/citizen/reports/${encodeURIComponent(reportId)}/download?type=${type}`,
  );
  return response.url;
}
