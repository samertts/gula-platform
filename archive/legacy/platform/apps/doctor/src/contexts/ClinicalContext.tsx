import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import {
  getVitalSigns, getDiagnoses, getClinicalNotes, getVisits,
  getLabResults, getRadiologyReports, getAllergies, getImmunizations,
  getFamilyHistory, getSocialHistory, getClinicalTimeline,
  type VitalSigns, type Diagnosis, type ClinicalNote, type Visit,
  type LabResult, type RadiologyReport, type Allergy,
  type Immunization, type FamilyHistory, type SocialHistory,
  type ClinicalTimelineEvent,
} from '../services/clinical';

interface ClinicalContextValue {
  vitalSigns: VitalSigns[];
  diagnoses: Diagnosis[];
  clinicalNotes: ClinicalNote[];
  visits: Visit[];
  labResults: LabResult[];
  radiologyReports: RadiologyReport[];
  allergies: Allergy[];
  immunizations: Immunization[];
  familyHistory: FamilyHistory[];
  socialHistory: SocialHistory | null;
  timeline: ClinicalTimelineEvent[];
  isLoading: Record<string, boolean>;
  loadVitalSigns: (patientId: string) => Promise<void>;
  loadDiagnoses: (patientId: string) => Promise<void>;
  loadClinicalNotes: (patientId: string) => Promise<void>;
  loadVisits: (patientId: string) => Promise<void>;
  loadLabResults: (patientId: string) => Promise<void>;
  loadRadiologyReports: (patientId: string) => Promise<void>;
  loadAllergies: (patientId: string) => Promise<void>;
  loadImmunizations: (patientId: string) => Promise<void>;
  loadFamilyHistory: (patientId: string) => Promise<void>;
  loadSocialHistory: (patientId: string) => Promise<void>;
  loadTimeline: (patientId: string) => Promise<void>;
  loadAllClinicalData: (patientId: string) => Promise<void>;
  clearData: () => void;
}

const ClinicalContext = createContext<ClinicalContextValue | null>(null);

const initialLoading: Record<string, boolean> = {
  vitalSigns: false,
  diagnoses: false,
  clinicalNotes: false,
  visits: false,
  labResults: false,
  radiologyReports: false,
  allergies: false,
  immunizations: false,
  familyHistory: false,
  socialHistory: false,
  timeline: false,
};

export function ClinicalProvider({ children }: { children: ReactNode }) {
  const [vitalSigns, setVitalSigns] = useState<VitalSigns[]>([]);
  const [diagnoses, setDiagnoses] = useState<Diagnosis[]>([]);
  const [clinicalNotes, setClinicalNotes] = useState<ClinicalNote[]>([]);
  const [visits, setVisits] = useState<Visit[]>([]);
  const [labResults, setLabResults] = useState<LabResult[]>([]);
  const [radiologyReports, setRadiologyReports] = useState<RadiologyReport[]>([]);
  const [allergies, setAllergies] = useState<Allergy[]>([]);
  const [immunizations, setImmunizations] = useState<Immunization[]>([]);
  const [familyHistory, setFamilyHistory] = useState<FamilyHistory[]>([]);
  const [socialHistory, setSocialHistory] = useState<SocialHistory | null>(null);
  const [timeline, setTimeline] = useState<ClinicalTimelineEvent[]>([]);
  const [isLoading, setIsLoading] = useState<Record<string, boolean>>(initialLoading);

  const withLoading = useCallback(async (key: string, fn: () => Promise<void>) => {
    setIsLoading(prev => ({ ...prev, [key]: true }));
    try {
      await fn();
    } finally {
      setIsLoading(prev => ({ ...prev, [key]: false }));
    }
  }, []);

  const loadVitalSigns = useCallback(async (patientId: string) => {
    await withLoading('vitalSigns', async () => {
      const data = await getVitalSigns(patientId);
      setVitalSigns(data);
    });
  }, [withLoading]);

  const loadDiagnoses = useCallback(async (patientId: string) => {
    await withLoading('diagnoses', async () => {
      const data = await getDiagnoses(patientId);
      setDiagnoses(data);
    });
  }, [withLoading]);

  const loadClinicalNotes = useCallback(async (patientId: string) => {
    await withLoading('clinicalNotes', async () => {
      const data = await getClinicalNotes(patientId);
      setClinicalNotes(data);
    });
  }, [withLoading]);

  const loadVisits = useCallback(async (patientId: string) => {
    await withLoading('visits', async () => {
      const data = await getVisits(patientId);
      setVisits(data);
    });
  }, [withLoading]);

  const loadLabResults = useCallback(async (patientId: string) => {
    await withLoading('labResults', async () => {
      const data = await getLabResults(patientId);
      setLabResults(data);
    });
  }, [withLoading]);

  const loadRadiologyReports = useCallback(async (patientId: string) => {
    await withLoading('radiologyReports', async () => {
      const data = await getRadiologyReports(patientId);
      setRadiologyReports(data);
    });
  }, [withLoading]);

  const loadAllergies = useCallback(async (patientId: string) => {
    await withLoading('allergies', async () => {
      const data = await getAllergies(patientId);
      setAllergies(data);
    });
  }, [withLoading]);

  const loadImmunizations = useCallback(async (patientId: string) => {
    await withLoading('immunizations', async () => {
      const data = await getImmunizations(patientId);
      setImmunizations(data);
    });
  }, [withLoading]);

  const loadFamilyHistory = useCallback(async (patientId: string) => {
    await withLoading('familyHistory', async () => {
      const data = await getFamilyHistory(patientId);
      setFamilyHistory(data);
    });
  }, [withLoading]);

  const loadSocialHistory = useCallback(async (patientId: string) => {
    await withLoading('socialHistory', async () => {
      const data = await getSocialHistory(patientId);
      setSocialHistory(data);
    });
  }, [withLoading]);

  const loadTimeline = useCallback(async (patientId: string) => {
    await withLoading('timeline', async () => {
      const data = await getClinicalTimeline(patientId);
      setTimeline(data);
    });
  }, [withLoading]);

  const loadAllClinicalData = useCallback(async (patientId: string) => {
    await Promise.all([
      loadVitalSigns(patientId),
      loadDiagnoses(patientId),
      loadClinicalNotes(patientId),
      loadVisits(patientId),
      loadLabResults(patientId),
      loadRadiologyReports(patientId),
      loadAllergies(patientId),
      loadImmunizations(patientId),
      loadFamilyHistory(patientId),
      loadSocialHistory(patientId),
      loadTimeline(patientId),
    ]);
  }, [loadVitalSigns, loadDiagnoses, loadClinicalNotes, loadVisits, loadLabResults, loadRadiologyReports, loadAllergies, loadImmunizations, loadFamilyHistory, loadSocialHistory, loadTimeline]);

  const clearData = useCallback(() => {
    setVitalSigns([]);
    setDiagnoses([]);
    setClinicalNotes([]);
    setVisits([]);
    setLabResults([]);
    setRadiologyReports([]);
    setAllergies([]);
    setImmunizations([]);
    setFamilyHistory([]);
    setSocialHistory(null);
    setTimeline([]);
    setIsLoading(initialLoading);
  }, []);

  return (
    <ClinicalContext.Provider
      value={{
        vitalSigns, diagnoses, clinicalNotes, visits,
        labResults, radiologyReports, allergies,
        immunizations, familyHistory, socialHistory, timeline,
        isLoading,
        loadVitalSigns, loadDiagnoses, loadClinicalNotes, loadVisits,
        loadLabResults, loadRadiologyReports, loadAllergies,
        loadImmunizations, loadFamilyHistory, loadSocialHistory,
        loadTimeline, loadAllClinicalData, clearData,
      }}
    >
      {children}
    </ClinicalContext.Provider>
  );
}

export function useClinicalContext(): ClinicalContextValue {
  const ctx = useContext(ClinicalContext);
  if (!ctx) throw new Error('useClinicalContext must be used within ClinicalProvider');
  return ctx;
}
