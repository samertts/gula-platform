import type { DiseaseOutbreak } from './api';

export interface SurveillanceSummary {
  totalActiveOutbreaks: number;
  diseasesUnderWatch: number;
  regionsAffected: number;
  totalCasesReported: number;
  reproductiveRate: number;
  criticalAlerts: number;
  trend: 'improving' | 'stable' | 'worsening';
}

export function computeSurveillanceSummary(outbreaks: DiseaseOutbreak[]): SurveillanceSummary {
  const totalActiveOutbreaks = outbreaks.filter(o => o.trend !== 'falling').length;
  const uniqueDiseases = new Set(outbreaks.map(o => o.disease)).size;
  const uniqueRegions = new Set(outbreaks.map(o => o.region)).size;
  const totalCases = outbreaks.reduce((sum, o) => sum + o.cases, 0);
  const avgR0 = outbreaks.length > 0
    ? outbreaks.reduce((sum, o) => sum + o.r0, 0) / outbreaks.length
    : 0;
  const criticalCount = outbreaks.filter(o => o.alertLevel === 'critical').length;
  const risingCount = outbreaks.filter(o => o.trend === 'rising').length;
  const fallingCount = outbreaks.filter(o => o.trend === 'falling').length;

  let trend: 'improving' | 'stable' | 'worsening';
  if (risingCount > fallingCount) trend = 'worsening';
  else if (fallingCount > risingCount) trend = 'improving';
  else trend = 'stable';

  return {
    totalActiveOutbreaks,
    diseasesUnderWatch: uniqueDiseases,
    regionsAffected: uniqueRegions,
    totalCasesReported: totalCases,
    reproductiveRate: Math.round(avgR0 * 10) / 10,
    criticalAlerts: criticalCount,
    trend,
  };
}

export function getOutbreaksByRegion(outbreaks: DiseaseOutbreak[]): Map<string, DiseaseOutbreak[]> {
  const map = new Map<string, DiseaseOutbreak[]>();
  for (const outbreak of outbreaks) {
    const existing = map.get(outbreak.region) || [];
    existing.push(outbreak);
    map.set(outbreak.region, existing);
  }
  return map;
}

export function getOutbreaksByDisease(outbreaks: DiseaseOutbreak[]): Map<string, DiseaseOutbreak[]> {
  const map = new Map<string, DiseaseOutbreak[]>();
  for (const outbreak of outbreaks) {
    const existing = map.get(outbreak.disease) || [];
    existing.push(outbreak);
    map.set(outbreak.disease, existing);
  }
  return map;
}
