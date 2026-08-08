import type { KpiMetric, RegionData, HospitalStat, LabStat } from './api';

export interface AggregateStatistics {
  totalPopulation: number;
  totalActiveLabs: number;
  totalHospitals: number;
  totalBeds: number;
  bedOccupancyRate: number;
  totalCasesToday: number;
  totalDeaths: number;
  totalRecoveries: number;
  averageVaccinationRate: number;
  regionsWithCriticalRisk: number;
  nationalTestTAT: number;
  pendingTests: number;
}

export function computeAggregateStats(
  regions: RegionData[],
  hospitals: HospitalStat[],
  labs: LabStat[],
  kpis: KpiMetric[],
): AggregateStatistics {
  const totalPopulation = regions.reduce((sum, r) => sum + r.population, 0);
  const totalActiveLabs = regions.reduce((sum, r) => sum + r.activeLabs, 0);
  const totalHospitals = regions.reduce((sum, r) => sum + r.activeHospitals, 0);
  const totalBeds = hospitals.reduce((sum, h) => sum + h.totalBeds, 0);
  const occupiedBeds = hospitals.reduce((sum, h) => sum + h.occupiedBeds, 0);
  const totalCasesToday = regions.reduce((sum, r) => sum + r.casesToday, 0);
  const totalDeaths = regions.reduce((sum, r) => sum + r.deaths, 0);
  const totalRecoveries = regions.reduce((sum, r) => sum + r.recoveries, 0);
  const avgVaccination = regions.length > 0
    ? regions.reduce((sum, r) => sum + r.vaccinationRate, 0) / regions.length
    : 0;
  const criticalRegions = regions.filter(r => r.riskLevel === 'critical').length;
  const avgTAT = labs.length > 0
    ? labs.reduce((sum, l) => sum + l.avgTatHours, 0) / labs.length
    : 0;
  const pendingTests = labs.reduce((sum, l) => sum + l.pendingTests, 0);

  return {
    totalPopulation,
    totalActiveLabs,
    totalHospitals,
    totalBeds,
    bedOccupancyRate: totalBeds > 0 ? Math.round((occupiedBeds / totalBeds) * 100) : 0,
    totalCasesToday,
    totalDeaths,
    totalRecoveries,
    averageVaccinationRate: Math.round(avgVaccination),
    regionsWithCriticalRisk: criticalRegions,
    nationalTestTAT: Math.round(avgTAT * 10) / 10,
    pendingTests,
  };
}

export function getRegionalRanking(regions: RegionData[], metric: keyof RegionData): RegionData[] {
  return [...regions].sort((a, b) => {
    const valA = Number(a[metric]) || 0;
    const valB = Number(b[metric]) || 0;
    return valB - valA;
  });
}

export function getTimeSeriesTrend(data: number[]): { direction: 'up' | 'down' | 'stable'; percent: number } {
  if (data.length < 2) return { direction: 'stable', percent: 0 };
  const recent = data.slice(-3);
  const older = data.slice(0, -3);
  if (older.length === 0) return { direction: 'stable', percent: 0 };
  const recentAvg = recent.reduce((a, b) => a + b, 0) / recent.length;
  const olderAvg = older.reduce((a, b) => a + b, 0) / older.length;
  const change = olderAvg > 0 ? ((recentAvg - olderAvg) / olderAvg) * 100 : 0;
  return {
    direction: change > 5 ? 'up' : change < -5 ? 'down' : 'stable',
    percent: Math.round(Math.abs(change) * 10) / 10,
  };
}
