import { apiRequest, cacheClinicalData, getCachedClinicalData } from './api';

export interface VitalSigns {
  bloodPressureSystolic: number;
  bloodPressureDiastolic: number;
  heartRate: number;
  respiratoryRate: number;
  temperature: number;
  oxygenSaturation: number;
  bloodGlucose?: number;
  painLevel?: number;
  weight?: number;
  height?: number;
  bmi?: number;
  recordedAt: string;
  recordedBy: string;
}

export interface Diagnosis {
  id: string;
  patientId: string;
  code: string;
  codingSystem: 'ICD-10' | 'ICD-11';
  description: string;
  descriptionAr: string;
  type: 'primary' | 'secondary' | 'complication' | 'historical';
  status: 'active' | 'resolved' | 'chronic' | 'suspected';
  onsetDate?: string;
  resolutionDate?: string;
  notes?: string;
  diagnosedBy: string;
  diagnosedAt: string;
  createdAt: string;
}

export interface ClinicalNote {
  id: string;
  patientId: string;
  visitId?: string;
  type: 'consultation' | 'follow_up' | 'procedure' | 'discharge_summary' | 'progress_note';
  content: string;
  contentAr: string;
  isSigned: boolean;
  signedBy?: string;
  signedAt?: string;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

export interface Visit {
  id: string;
  patientId: string;
  visitDate: string;
  visitType: 'outpatient' | 'inpatient' | 'emergency' | 'follow_up' | 'telemedicine';
  chiefComplaint: string;
  chiefComplaintAr: string;
  diagnosis: string;
  diagnosisAr: string;
  department: string;
  doctorId: string;
  doctorName: string;
  notes?: string;
  vitalSigns?: VitalSigns;
  status: 'active' | 'completed' | 'cancelled';
  createdAt: string;
  updatedAt: string;
}

export interface LabResult {
  id: string;
  patientId: string;
  orderId: string;
  testName: string;
  testNameAr: string;
  category: string;
  result: string;
  unit: string;
  referenceRange: string;
  flag: 'normal' | 'high' | 'low' | 'critical_high' | 'critical_low' | 'abnormal';
  interpretation?: string;
  performedBy?: string;
  performedAt: string;
  verifiedAt?: string;
  verifiedBy?: string;
  createdAt: string;
}

export interface RadiologyReport {
  id: string;
  patientId: string;
  orderId: string;
  examType: string;
  examTypeAr: string;
  bodyPart: string;
  technique?: string;
  findings: string;
  findingsAr: string;
  impression: string;
  impressionAr: string;
  images: string[];
  radiologist?: string;
  status: 'pending' | 'completed' | 'verified';
  performedAt: string;
  createdAt: string;
}

export interface Allergy {
  id: string;
  patientId: string;
  allergen: string;
  allergenAr: string;
  reaction: string;
  severity: 'mild' | 'moderate' | 'severe';
  recordedAt: string;
}

export interface Immunization {
  id: string;
  patientId: string;
  vaccine: string;
  vaccineAr: string;
  doseNumber: number;
  administeredAt: string;
  administeredBy: string;
  nextDoseDue?: string;
  facility?: string;
}

export interface FamilyHistory {
  id: string;
  patientId: string;
  relation: string;
  condition: string;
  conditionAr: string;
  ageOfOnset?: number;
  notes?: string;
}

export interface SocialHistory {
  smoking: 'never' | 'former' | 'current';
  smokingPackYears?: number;
  alcohol: 'never' | 'occasional' | 'regular';
  occupation?: string;
  exercise?: string;
  diet?: string;
}

export interface ClinicalTimelineEvent {
  id: string;
  patientId: string;
  date: string;
  type: 'visit' | 'diagnosis' | 'lab_result' | 'radiology' | 'prescription' | 'procedure' | 'note' | 'vaccination' | 'allergy' | 'admission' | 'discharge';
  title: string;
  titleAr: string;
  description?: string;
  descriptionAr?: string;
  severity?: 'info' | 'warning' | 'critical' | 'success';
  details?: Record<string, unknown>;
}

export async function getVitalSigns(patientId: string): Promise<VitalSigns[]> {
  return apiRequest<VitalSigns[]>(`/patients/${patientId}/vitals`);
}

export async function recordVitalSigns(patientId: string, vitals: Omit<VitalSigns, 'recordedAt' | 'recordedBy'>): Promise<VitalSigns> {
  return apiRequest<VitalSigns>(`/patients/${patientId}/vitals`, {
    method: 'POST',
    body: JSON.stringify(vitals),
    offlinePriority: 'high',
  });
}

export async function getDiagnoses(patientId: string): Promise<Diagnosis[]> {
  return apiRequest<Diagnosis[]>(`/patients/${patientId}/diagnoses`);
}

export async function addDiagnosis(patientId: string, diagnosis: Omit<Diagnosis, 'id' | 'patientId' | 'createdAt'>): Promise<Diagnosis> {
  return apiRequest<Diagnosis>(`/patients/${patientId}/diagnoses`, {
    method: 'POST',
    body: JSON.stringify(diagnosis),
    offlinePriority: 'high',
  });
}

export async function updateDiagnosis(patientId: string, diagnosisId: string, updates: Partial<Diagnosis>): Promise<Diagnosis> {
  return apiRequest<Diagnosis>(`/patients/${patientId}/diagnoses/${diagnosisId}`, {
    method: 'PATCH',
    body: JSON.stringify(updates),
  });
}

export async function getClinicalNotes(patientId: string): Promise<ClinicalNote[]> {
  return apiRequest<ClinicalNote[]>(`/patients/${patientId}/notes`);
}

export async function createClinicalNote(patientId: string, note: Omit<ClinicalNote, 'id' | 'patientId' | 'createdAt' | 'updatedAt'>): Promise<ClinicalNote> {
  return apiRequest<ClinicalNote>(`/patients/${patientId}/notes`, {
    method: 'POST',
    body: JSON.stringify(note),
    offlinePriority: 'high',
  });
}

export async function signClinicalNote(patientId: string, noteId: string): Promise<ClinicalNote> {
  return apiRequest<ClinicalNote>(`/patients/${patientId}/notes/${noteId}/sign`, {
    method: 'POST',
  });
}

export async function getVisits(patientId: string): Promise<Visit[]> {
  return apiRequest<Visit[]>(`/patients/${patientId}/visits`);
}

export async function createVisit(patientId: string, visit: Omit<Visit, 'id' | 'patientId' | 'createdAt' | 'updatedAt'>): Promise<Visit> {
  return apiRequest<Visit>(`/patients/${patientId}/visits`, {
    method: 'POST',
    body: JSON.stringify(visit),
    offlinePriority: 'high',
  });
}

export async function getLabResults(patientId: string): Promise<LabResult[]> {
  return apiRequest<LabResult[]>(`/patients/${patientId}/lab-results`);
}

export async function getRadiologyReports(patientId: string): Promise<RadiologyReport[]> {
  return apiRequest<RadiologyReport[]>(`/patients/${patientId}/radiology`);
}

export async function getAllergies(patientId: string): Promise<Allergy[]> {
  return apiRequest<Allergy[]>(`/patients/${patientId}/allergies`);
}

export async function addAllergy(patientId: string, allergy: Omit<Allergy, 'id' | 'patientId' | 'recordedAt'>): Promise<Allergy> {
  return apiRequest<Allergy>(`/patients/${patientId}/allergies`, {
    method: 'POST',
    body: JSON.stringify(allergy),
  });
}

export async function getImmunizations(patientId: string): Promise<Immunization[]> {
  return apiRequest<Immunization[]>(`/patients/${patientId}/immunizations`);
}

export async function getFamilyHistory(patientId: string): Promise<FamilyHistory[]> {
  return apiRequest<FamilyHistory[]>(`/patients/${patientId}/family-history`);
}

export async function getSocialHistory(patientId: string): Promise<SocialHistory | null> {
  try {
    return await apiRequest<SocialHistory>(`/patients/${patientId}/social-history`);
  } catch {
    return null;
  }
}

export async function getClinicalTimeline(patientId: string): Promise<ClinicalTimelineEvent[]> {
  const cacheKey = `timeline:${patientId}`;
  const cached = await getCachedClinicalData(cacheKey);
  try {
    const data = await apiRequest<ClinicalTimelineEvent[]>(`/patients/${patientId}/timeline`);
    await cacheClinicalData(cacheKey, data);
    return data;
  } catch (error) {
    if (cached) return cached as ClinicalTimelineEvent[];
    throw error;
  }
}
