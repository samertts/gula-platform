import { apiGet, apiPost, apiPut, apiDelete } from '../client';
import type { ClinicalNote, Allergy, Diagnosis } from '../types';

export async function createClinicalNote(data: {
  patient_id: string;
  note_type: string;
  title: string;
  content: string;
}): Promise<ClinicalNote> {
  return apiPost<ClinicalNote>('/ehr/clinical-notes', data);
}

export async function getClinicalNote(noteId: string): Promise<ClinicalNote> {
  return apiGet<ClinicalNote>(`/ehr/clinical-notes/${noteId}`);
}

export async function updateClinicalNote(noteId: string, data: Partial<ClinicalNote>): Promise<ClinicalNote> {
  return apiPut<ClinicalNote>(`/ehr/clinical-notes/${noteId}`, data);
}

export async function deleteClinicalNote(noteId: string): Promise<void> {
  return apiDelete<void>(`/ehr/clinical-notes/${noteId}`);
}

export async function listPatientNotes(patientId: string): Promise<ClinicalNote[]> {
  return apiGet<ClinicalNote[]>(`/ehr/patients/${patientId}/clinical-notes`);
}

export async function createAllergy(data: {
  patient_id: string;
  code_display: string;
  severity: string;
  status: string;
}): Promise<Allergy> {
  return apiPost<Allergy>('/ehr/allergies', data);
}

export async function listPatientAllergies(patientId: string): Promise<Allergy[]> {
  return apiGet<Allergy[]>(`/ehr/patients/${patientId}/allergies`);
}

export async function createDiagnosis(data: {
  patient_id: string;
  diagnosis_text: string;
  icd10_code?: string;
}): Promise<Diagnosis> {
  return apiPost<Diagnosis>('/ehr/diagnoses', data);
}

export async function listPatientDiagnoses(patientId: string): Promise<Diagnosis[]> {
  return apiGet<Diagnosis[]>(`/ehr/patients/${patientId}/diagnoses`);
}

export async function getPatientTimeline(patientId: string, params?: {
  event_type?: string;
  skip?: number;
  limit?: number;
}): Promise<any[]> {
  return apiGet<any[]>(`/ehr/patients/${patientId}/timeline`, params as Record<string, any>);
}

export async function getPatientSummary(patientId: string): Promise<any> {
  return apiGet<any>(`/ehr/patient/${patientId}/summary`);
}
