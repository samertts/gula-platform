import { apiGet } from '../client';
import type { DashboardStats, LabStats } from '../types';

export async function getDashboard(): Promise<DashboardStats> {
  return apiGet<DashboardStats>('/dashboard');
}

export async function getGreeting(): Promise<{ greeting: string; greeting_ar: string }> {
  return apiGet<{ greeting: string; greeting_ar: string }>('/greeting');
}

export async function getDailyTrends(days: number = 30): Promise<LabStats['daily_trends']> {
  return apiGet<LabStats['daily_trends']>('/stats/trends/daily', { days });
}

export async function getTopTests(days: number = 30, limit: number = 10): Promise<LabStats['top_tests']> {
  return apiGet<LabStats['top_tests']>('/stats/trends/tests', { days, limit });
}

export async function getFlagDistribution(days: number = 30): Promise<LabStats['flag_distribution']> {
  return apiGet<LabStats['flag_distribution']>('/stats/trends/flags', { days });
}

export async function getWeeklyPatients(days: number = 30): Promise<LabStats['weekly_patients']> {
  return apiGet<LabStats['weekly_patients']>('/stats/trends/patients', { days });
}

export async function getStatsSummary(): Promise<LabStats['summary']> {
  return apiGet<LabStats['summary']>('/stats/summary');
}

export async function getTurnaroundTime(days: number = 30): Promise<number> {
  return apiGet<number>('/stats/turnaround', { days });
}
