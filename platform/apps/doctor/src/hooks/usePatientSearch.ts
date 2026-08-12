import { useState, useCallback, useRef } from 'react';
import { usePatientContext } from '../contexts/PatientContext';
import { searchPatients, searchMpi, confirmMpiMatch, rejectMpiMatch, type PatientSearchParams, type PatientSearchResult, type MpiMatchResult } from '../services/patient';

export function usePatientSearch() {
  const { search, searchResults, isSearching } = usePatientContext();
  const [mpiResults, setMpiResults] = useState<MpiMatchResult[]>([]);
  const [searchError, setSearchError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const performSearch = useCallback(async (params: PatientSearchParams): Promise<PatientSearchResult | null> => {
    setSearchError(null);
    try {
      const results = await search(params);

      if (params.query && results.patients.length === 0) {
        try {
          const mpi = await searchMpi(params.query);
          setMpiResults(mpi);
        } catch {}
      } else {
        setMpiResults([]);
      }

      return results;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'فشل البحث';
      setSearchError(message);
      return null;
    }
  }, [search]);

  const debouncedSearch = useCallback((params: PatientSearchParams) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => performSearch(params), 300);
  }, [performSearch]);

  const clearError = useCallback(() => setSearchError(null), []);

  const confirmMatch = useCallback(async (patientId: string, matchedPatientId: string) => {
    await confirmMpiMatch(patientId, matchedPatientId);
    setMpiResults(prev => prev.filter(m => m.matchedPatientId !== matchedPatientId));
  }, []);

  const rejectMatch = useCallback(async (patientId: string, matchedPatientId: string) => {
    await rejectMpiMatch(patientId, matchedPatientId);
    setMpiResults(prev => prev.filter(m => m.matchedPatientId !== matchedPatientId));
  }, []);

  return {
    searchResults,
    isSearching,
    searchError,
    mpiResults,
    performSearch,
    debouncedSearch,
    clearError,
    confirmMatch,
    rejectMatch,
  };
}
