import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import { searchPatients, getPatient, type Patient, type PatientSearchParams, type PatientSearchResult } from '../services/patient';

interface PatientContextValue {
  selectedPatient: Patient | null;
  searchResults: PatientSearchResult | null;
  recentPatients: Patient[];
  isSearching: boolean;
  isLoadingPatient: boolean;
  selectPatient: (patient: Patient | null) => void;
  search: (params: PatientSearchParams) => Promise<PatientSearchResult>;
  loadPatient: (patientId: string) => Promise<Patient>;
  clearSearch: () => void;
  setRecentPatients: (patients: Patient[]) => void;
}

const PatientContext = createContext<PatientContextValue | null>(null);

export function PatientProvider({ children }: { children: ReactNode }) {
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [searchResults, setSearchResults] = useState<PatientSearchResult | null>(null);
  const [recentPatients, setRecentPatientsState] = useState<Patient[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isLoadingPatient, setIsLoadingPatient] = useState(false);

  const selectPatient = useCallback((patient: Patient | null) => {
    setSelectedPatient(patient);
  }, []);

  const search = useCallback(async (params: PatientSearchParams): Promise<PatientSearchResult> => {
    setIsSearching(true);
    try {
      const results = await searchPatients(params);
      setSearchResults(results);
      return results;
    } finally {
      setIsSearching(false);
    }
  }, []);

  const loadPatient = useCallback(async (patientId: string): Promise<Patient> => {
    setIsLoadingPatient(true);
    try {
      const patient = await getPatient(patientId);
      setSelectedPatient(patient);
      return patient;
    } finally {
      setIsLoadingPatient(false);
    }
  }, []);

  const clearSearch = useCallback(() => {
    setSearchResults(null);
  }, []);

  const setRecentPatients = useCallback((patients: Patient[]) => {
    setRecentPatientsState(patients);
  }, []);

  return (
    <PatientContext.Provider
      value={{
        selectedPatient,
        searchResults,
        recentPatients,
        isSearching,
        isLoadingPatient,
        selectPatient,
        search,
        loadPatient,
        clearSearch,
        setRecentPatients,
      }}
    >
      {children}
    </PatientContext.Provider>
  );
}

export function usePatientContext(): PatientContextValue {
  const ctx = useContext(PatientContext);
  if (!ctx) throw new Error('usePatientContext must be used within PatientProvider');
  return ctx;
}
