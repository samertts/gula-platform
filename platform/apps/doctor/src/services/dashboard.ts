import { apiRequest } from './api';
import type { PatientSearchResult } from './patient';

export interface CriticalAlertRecord {
  id: number;
  order_id: number | null;
  critical_tests: unknown[];
  token_prefix?: string;
  created_at: string | null;
}

export interface CriticalAlertsResponse {
  count: number;
  alerts: CriticalAlertRecord[];
}

export async function getDoctorRecentPatients(page = 1, pageSize = 20): Promise<PatientSearchResult> {
  return apiRequest<PatientSearchResult>(`/patients/recent?page=${page}&pageSize=${pageSize}`);
}

export async function getDoctorCriticalAlerts(limit = 20): Promise<CriticalAlertsResponse> {
  return apiRequest<CriticalAlertsResponse>(`/ai/critical-alerts?limit=${limit}`);
}

export function formatCriticalTests(tests: unknown[]): string {
  const names = tests
    .map((test) => {
      if (typeof test === 'string') return test;
      if (typeof test === 'object' && test !== null && 'test_name' in test) {
        const value = (test as { test_name?: unknown }).test_name;
        return typeof value === 'string' ? value : null;
      }
      return null;
    })
    .filter((name): name is string => Boolean(name));
  return names.length > 0 ? names.join(', ') : 'Critical laboratory result';
}
