import { useCallback } from 'react';
import { useClinicalContext } from '../contexts/ClinicalContext';
import {
  addDiagnosis, updateDiagnosis, createClinicalNote, signClinicalNote,
  recordVitalSigns, createVisit, addAllergy,
  type Diagnosis, type ClinicalNote, type VitalSigns, type Visit, type Allergy,
} from '../services/clinical';

export function useClinicalData(patientId: string) {
  const ctx = useClinicalContext();

  const addDiagnosisRecord = useCallback(async (
    diagnosis: Omit<Diagnosis, 'id' | 'patientId' | 'createdAt'>,
  ): Promise<Diagnosis> => {
    const result = await addDiagnosis(patientId, diagnosis);
    await ctx.loadDiagnoses(patientId);
    return result;
  }, [patientId, ctx]);

  const editDiagnosis = useCallback(async (
    diagnosisId: string,
    updates: Partial<Diagnosis>,
  ): Promise<Diagnosis> => {
    const result = await updateDiagnosis(patientId, diagnosisId, updates);
    await ctx.loadDiagnoses(patientId);
    return result;
  }, [patientId, ctx]);

  const addNote = useCallback(async (
    note: Omit<ClinicalNote, 'id' | 'patientId' | 'createdAt' | 'updatedAt'>,
  ): Promise<ClinicalNote> => {
    const result = await createClinicalNote(patientId, note);
    await ctx.loadClinicalNotes(patientId);
    return result;
  }, [patientId, ctx]);

  const signNote = useCallback(async (noteId: string): Promise<ClinicalNote> => {
    const result = await signClinicalNote(patientId, noteId);
    await ctx.loadClinicalNotes(patientId);
    return result;
  }, [patientId, ctx]);

  const addVitalSigns = useCallback(async (
    vitals: Omit<VitalSigns, 'recordedAt' | 'recordedBy'>,
  ): Promise<VitalSigns> => {
    const result = await recordVitalSigns(patientId, vitals);
    await ctx.loadVitalSigns(patientId);
    return result;
  }, [patientId, ctx]);

  const addVisit = useCallback(async (
    visit: Omit<Visit, 'id' | 'patientId' | 'createdAt' | 'updatedAt'>,
  ): Promise<Visit> => {
    const result = await createVisit(patientId, visit);
    await ctx.loadVisits(patientId);
    return result;
  }, [patientId, ctx]);

  const addAllergyRecord = useCallback(async (
    allergy: Omit<Allergy, 'id' | 'patientId' | 'recordedAt'>,
  ): Promise<Allergy> => {
    const result = await addAllergy(patientId, allergy);
    await ctx.loadAllergies(patientId);
    return result;
  }, [patientId, ctx]);

  const refreshAll = useCallback(async () => {
    await ctx.loadAllClinicalData(patientId);
  }, [patientId, ctx]);

  return {
    ...ctx,
    addDiagnosisRecord,
    editDiagnosis,
    addNote,
    signNote,
    addVitalSigns,
    addVisit,
    addAllergyRecord,
    refreshAll,
  };
}
