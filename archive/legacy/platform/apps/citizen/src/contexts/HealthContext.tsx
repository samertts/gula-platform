import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import type { LabResult, RadiologyReport, Prescription, Vaccination, HealthRecord, HealthScore } from '../types';

interface HealthContextValue {
  labResults: LabResult[];
  radiologyReports: RadiologyReport[];
  prescriptions: Prescription[];
  vaccinations: Vaccination[];
  medicalHistory: HealthRecord[];
  healthScore: HealthScore | null;
  setLabResults: (results: LabResult[]) => void;
  setRadiologyReports: (reports: RadiologyReport[]) => void;
  setPrescriptions: (prescriptions: Prescription[]) => void;
  setVaccinations: (vaccinations: Vaccination[]) => void;
  setMedicalHistory: (history: HealthRecord[]) => void;
  setHealthScore: (score: HealthScore) => void;
  clearHealthData: () => void;
}

const HealthContext = createContext<HealthContextValue | null>(null);

export function HealthProvider({ children }: { children: ReactNode }) {
  const [labResults, setLabResults] = useState<LabResult[]>([]);
  const [radiologyReports, setRadiologyReports] = useState<RadiologyReport[]>([]);
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [vaccinations, setVaccinations] = useState<Vaccination[]>([]);
  const [medicalHistory, setMedicalHistory] = useState<HealthRecord[]>([]);
  const [healthScore, setHealthScore] = useState<HealthScore | null>(null);

  const clearHealthData = useCallback(() => {
    setLabResults([]);
    setRadiologyReports([]);
    setPrescriptions([]);
    setVaccinations([]);
    setMedicalHistory([]);
    setHealthScore(null);
  }, []);

  return (
    <HealthContext.Provider
      value={{
        labResults,
        radiologyReports,
        prescriptions,
        vaccinations,
        medicalHistory,
        healthScore,
        setLabResults,
        setRadiologyReports,
        setPrescriptions,
        setVaccinations,
        setMedicalHistory,
        setHealthScore,
        clearHealthData,
      }}
    >
      {children}
    </HealthContext.Provider>
  );
}

export function useHealth(): HealthContextValue {
  const ctx = useContext(HealthContext);
  if (!ctx) throw new Error('useHealth must be used within HealthProvider');
  return ctx;
}
