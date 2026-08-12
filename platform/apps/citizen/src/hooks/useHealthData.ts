import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useHealth } from '../contexts/HealthContext';
import { useBackendResource } from '@gula/ui-platform';
import { getCitizenDashboard, getLabResults, getRadiologyReports, getPrescriptions, getVaccinations, getMedicalHistory, getHealthScore } from '../services/healthData';
import type { CitizenDashboard } from '../services/healthData';
import type { LabResult, RadiologyReport, Prescription, Vaccination, HealthRecord, HealthScore } from '../types';

export function useCitizenDashboard() {
  const { user } = useAuth();
  const loadDashboard = useCallback(() => getCitizenDashboard(), []);
  return useBackendResource<CitizenDashboard>(loadDashboard, Boolean(user));
}

export function useHealthData() {
  const { user } = useAuth();
  const health = useHealth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    if (!user) return;
    setIsLoading(true);
    setError(null);

    try {
      const [results, reports, prescriptions, vaccinations, history, score] = await Promise.all([
        getLabResults(user.id),
        getRadiologyReports(user.id),
        getPrescriptions(user.id),
        getVaccinations(user.id),
        getMedicalHistory(user.id),
        getHealthScore(user.id),
      ]);

      health.setLabResults(results);
      health.setRadiologyReports(reports);
      health.setPrescriptions(prescriptions);
      health.setVaccinations(vaccinations);
      health.setMedicalHistory(history);
      if (score) health.setHealthScore(score);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return {
    ...health,
    isLoading,
    error,
    refetch: fetchAll,
  };
}

export function useLabResults() {
  const { user } = useAuth();
  const [data, setData] = useState<LabResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    if (!user) return;
    setIsLoading(true);
    try {
      const results = await getLabResults(user.id);
      setData(results);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  useEffect(() => { fetch(); }, [fetch]);

  return { data, isLoading, error, refetch: fetch };
}

export function useRadiologyReports() {
  const { user } = useAuth();
  const [data, setData] = useState<RadiologyReport[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    if (!user) return;
    setIsLoading(true);
    try {
      const reports = await getRadiologyReports(user.id);
      setData(reports);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  useEffect(() => { fetch(); }, [fetch]);

  return { data, isLoading, error, refetch: fetch };
}

export function usePrescriptions() {
  const { user } = useAuth();
  const [data, setData] = useState<Prescription[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    if (!user) return;
    setIsLoading(true);
    try {
      const results = await getPrescriptions(user.id);
      setData(results);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  useEffect(() => { fetch(); }, [fetch]);

  return { data, isLoading, error, refetch: fetch };
}

export function useVaccinations() {
  const { user } = useAuth();
  const [data, setData] = useState<Vaccination[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    if (!user) return;
    setIsLoading(true);
    try {
      const results = await getVaccinations(user.id);
      setData(results);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  useEffect(() => { fetch(); }, [fetch]);

  return { data, isLoading, error, refetch: fetch };
}

export function useMedicalHistory() {
  const { user } = useAuth();
  const [data, setData] = useState<HealthRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    if (!user) return;
    setIsLoading(true);
    try {
      const history = await getMedicalHistory(user.id);
      setData(history);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  useEffect(() => { fetch(); }, [fetch]);

  return { data, isLoading, error, refetch: fetch };
}

export function useHealthScore() {
  const { user } = useAuth();
  const [data, setData] = useState<HealthScore | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetch = useCallback(async () => {
    if (!user) return;
    setIsLoading(true);
    try {
      const score = await getHealthScore(user.id);
      setData(score);
    } catch {
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  useEffect(() => { fetch(); }, [fetch]);

  return { data, isLoading, refetch: fetch };
}
