import { GulaClient } from '../client';
import {
  DashboardSummary, StatsResponse, RevenueStats,
  PatientDemographics, TestPopularity, PeakHours,
} from '../types';

export class StatsAPI {
  constructor(private client: GulaClient) {}

  async general(): Promise<StatsResponse> {
    return this.client.get('/stats');
  }

  async dashboard(): Promise<DashboardSummary> {
    return this.client.get<DashboardSummary>('/stats/dashboard');
  }

  async lab(labId: number): Promise<StatsResponse> {
    return this.client.get(`/stats/lab/${labId}`);
  }

  async trends(params?: { period?: string; from?: string; to?: string }): Promise<StatsResponse> {
    return this.client.get('/stats/trends', params as Record<string, unknown>);
  }

  async comparison(params?: { period1?: string; period2?: string }): Promise<StatsResponse> {
    return this.client.get('/stats/comparison', params as Record<string, unknown>);
  }

  async export(params?: Record<string, unknown>): Promise<Blob> {
    const qs = new URLSearchParams(
      Object.entries(params ?? {}).map(([k, v]) => [k, String(v)])
    ).toString();
    return this.client.download(`/stats/export?${qs}`, 'stats.csv');
  }

  async patientDemographics(): Promise<PatientDemographics> {
    return this.client.get<PatientDemographics>('/stats/patient-demographics');
  }

  async testPopularity(): Promise<TestPopularity[]> {
    return this.client.get<TestPopularity[]>('/stats/test-popularity');
  }

  async peakHours(): Promise<PeakHours[]> {
    return this.client.get<PeakHours[]>('/stats/peak-hours');
  }

  async monthlyReport(params?: { year?: number; month?: number }): Promise<StatsResponse> {
    return this.client.get('/stats/monthly-report', params as Record<string, unknown>);
  }

  async revenue(): Promise<RevenueStats> {
    return this.client.get<RevenueStats>('/stats/revenue');
  }

  async mainDashboard(): Promise<DashboardSummary> {
    return this.client.get<DashboardSummary>('/dashboard');
  }

  async labDashboard(labId: number): Promise<DashboardSummary> {
    return this.client.get<DashboardSummary>(`/dashboard/lab/${labId}`);
  }
}
