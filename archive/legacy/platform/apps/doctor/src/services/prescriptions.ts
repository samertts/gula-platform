import { apiRequest } from './api';

export interface DrugInteraction {
  drug1: string;
  drug2: string;
  severity: 'minor' | 'moderate' | 'major' | 'contraindicated';
  description: string;
  descriptionAr: string;
  recommendation: string;
  recommendationAr: string;
}

export interface PrescriptionMedication {
  id: string;
  medicationCode: string;
  medicationName: string;
  medicationNameAr: string;
  strength: string;
  form: string;
  route: string;
  dose: string;
  frequency: string;
  duration: string;
  quantity: number;
  refills: number;
  instructions: string;
  instructionsAr: string;
  substitutionAllowed: boolean;
  interactions?: DrugInteraction[];
}

export interface Prescription {
  id: string;
  patientId: string;
  patientName: string;
  patientNameAr: string;
  doctorId: string;
  doctorName: string;
  facilityName: string;
  facilityNameAr: string;
  medications: PrescriptionMedication[];
  diagnosis?: string;
  diagnosisAr?: string;
  notes?: string;
  notesAr?: string;
  isSigned: boolean;
  signedAt?: string;
  isControlled: boolean;
  status: 'active' | 'dispensed' | 'partial' | 'cancelled' | 'expired';
  createdAt: string;
  updatedAt: string;
}

export interface MedicationSearchResult {
  code: string;
  name: string;
  nameAr: string;
  strength: string;
  form: string;
  category: string;
  isControlled: boolean;
  requiresDiagnosis: boolean;
}

export async function searchMedications(query: string): Promise<MedicationSearchResult[]> {
  return apiRequest<MedicationSearchResult[]>(`/medications/search?q=${encodeURIComponent(query)}`);
}

export async function getPrescriptions(patientId: string): Promise<Prescription[]> {
  return apiRequest<Prescription[]>(`/patients/${patientId}/prescriptions`);
}

export async function getPrescription(prescriptionId: string): Promise<Prescription> {
  return apiRequest<Prescription>(`/prescriptions/${prescriptionId}`);
}

export async function createPrescription(
  patientId: string,
  prescription: Omit<Prescription, 'id' | 'patientId' | 'patientName' | 'patientNameAr' | 'doctorId' | 'doctorName' | 'facilityName' | 'facilityNameAr' | 'createdAt' | 'updatedAt' | 'status'>,
): Promise<Prescription> {
  return apiRequest<Prescription>(`/patients/${patientId}/prescriptions`, {
    method: 'POST',
    body: JSON.stringify(prescription),
    offlinePriority: 'high',
  });
}

export async function signPrescription(prescriptionId: string): Promise<Prescription> {
  return apiRequest<Prescription>(`/prescriptions/${prescriptionId}/sign`, {
    method: 'POST',
    body: JSON.stringify({}),
    offlinePriority: 'high',
  });
}

export async function cancelPrescription(prescriptionId: string, reason: string): Promise<Prescription> {
  return apiRequest<Prescription>(`/prescriptions/${prescriptionId}/cancel`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  });
}

export async function checkDrugInteractions(
  patientId: string,
  medications: { code: string; name: string }[],
): Promise<DrugInteraction[]> {
  return apiRequest<DrugInteraction[]>(`/patients/${patientId}/drug-interactions`, {
    method: 'POST',
    body: JSON.stringify({ medications }),
  });
}

export async function getActivePrescriptions(patientId: string): Promise<Prescription[]> {
  return apiRequest<Prescription[]>(`/patients/${patientId}/prescriptions/active`);
}

export async function printPrescription(prescriptionId: string): Promise<string> {
  const result = await apiRequest<{ url: string }>(`/prescriptions/${prescriptionId}/print`);
  return result.url;
}
