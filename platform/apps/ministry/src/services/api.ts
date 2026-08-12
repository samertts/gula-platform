export interface MinistryUser {
  id: string;
  name: string;
  email: string;
  role: 'minister' | 'deputy' | 'director' | 'analyst' | 'viewer';
  permissions: string[];
}

export interface KpiMetric {
  id: string;
  label: string;
  labelAr: string;
  value: number;
  unit: string;
  trend: number;
  trendUp: boolean;
  icon: string;
  color: string;
}

export interface RegionData {
  id: string;
  name: string;
  nameAr: string;
  governorate: string;
  population: number;
  activeLabs: number;
  activeHospitals: number;
  bedOccupancy: number;
  casesToday: number;
  totalCases: number;
  deaths: number;
  recoveries: number;
  vaccinationRate: number;
  riskLevel: 'low' | 'moderate' | 'high' | 'critical';
  lat: number;
  lng: number;
}

export interface DiseaseOutbreak {
  id: string;
  disease: string;
  diseaseAr: string;
  region: string;
  cases: number;
  deaths: number;
  r0: number;
  trend: 'rising' | 'stable' | 'falling';
  alertLevel: 'info' | 'warning' | 'danger' | 'critical';
  detectedAt: string;
}

export interface Alert {
  id: string;
  title: string;
  titleAr: string;
  description: string;
  descriptionAr: string;
  severity: 'info' | 'warning' | 'danger' | 'critical';
  region: string;
  source: string;
  createdAt: string;
  acknowledged: boolean;
}

export interface HospitalStat {
  id: string;
  name: string;
  nameAr: string;
  region: string;
  totalBeds: number;
  occupiedBeds: number;
  icuBeds: number;
  icuOccupied: number;
  ventilators: number;
  ventilatorsUsed: number;
  admissions24h: number;
  discharges24h: number;
  deaths24h: number;
}

export interface LabStat {
  id: string;
  name: string;
  nameAr: string;
  region: string;
  testsToday: number;
  testsThisWeek: number;
  testsThisMonth: number;
  avgTatHours: number;
  pendingTests: number;
  criticalResults: number;
  instruments: number;
  status: 'online' | 'degraded' | 'offline';
}

export interface VaccinationData {
  region: string;
  totalVaccinated: number;
  partiallyVaccinated: number;
  fullyVaccinated: number;
  boosterReceived: number;
  coveragePercent: number;
  dosesAdministered: number;
}

export interface MortalityRecord {
  region: string;
  totalDeaths: number;
  maleDeaths: number;
  femaleDeaths: number;
  infantDeaths: number;
  maternalDeaths: number;
  causeDistribution: { cause: string; count: number }[];
}

export interface BirthRecord {
  region: string;
  totalBirths: number;
  maleBirths: number;
  femaleBirths: number;
  homeBirths: number;
  hospitalBirths: number;
  registeredLate: number;
}

export interface WorkforceData {
  region: string;
  doctors: number;
  nurses: number;
  pharmacists: number;
  labTechs: number;
  adminStaff: number;
  specialists: { field: string; count: number }[];
  vacancies: number;
}

export interface MedicationSupply {
  medication: string;
  medicationAr: string;
  stockLevel: number;
  reorderLevel: number;
  monthlyConsumption: number;
  leadTimeDays: number;
  supplier: string;
  status: 'adequate' | 'low' | 'critical' | 'out_of_stock';
  region: string;
}

export interface BloodSupply {
  bloodType: string;
  unitsAvailable: number;
  unitsNeeded: number;
  donationsToday: number;
  expiringSoon: number;
  region: string;
}

export interface ResourceMetric {
  resource: string;
  resourceAr: string;
  totalAvailable: number;
  totalRequired: number;
  utilizationPercent: number;
  region: string;
  status: 'sufficient' | 'insufficient' | 'critical';
}

export interface EmergencyResponse {
  id: string;
  incident: string;
  incidentAr: string;
  region: string;
  severity: 'local' | 'regional' | 'national';
  status: 'active' | 'contained' | 'resolved';
  teamsDeployed: number;
  casualties: number;
  startedAt: string;
  updatedAt: string;
}

export interface ReportConfig {
  title: string;
  type: 'summary' | 'detailed' | 'comparative' | 'trend';
  regions: string[];
  dateFrom: string;
  dateTo: string;
  sections: string[];
  format: 'pdf' | 'csv' | 'xlsx';
}

export interface NationalReport {
  id: string;
  title: string;
  titleAr: string;
  type: string;
  generatedAt: string;
  period: string;
  status: 'generating' | 'ready' | 'failed';
  url?: string;
}

const API_BASE = 'https://api.gula.health/api/v1';

function isIsolatedDemoMode(): boolean {
  return import.meta.env.VITE_DEMO_MODE === 'true'
    && typeof window !== 'undefined'
    && sessionStorage.getItem('gula_ministry_demo_mode') === 'enabled';
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  if (isIsolatedDemoMode() && path.startsWith('/ministry/')) {
    throw new Error('Demo mode blocks live Ministry API calls; synthetic fixtures are required.');
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export const api = {
  getSession: () => request<{ user: MinistryUser; demo_mode?: boolean }>('/auth/session'),
  getKpis: (region?: string) => request<KpiMetric[]>(`/ministry/kpis${region ? `?region=${region}` : ''}`),
  getRegions: () => request<RegionData[]>('/ministry/regions'),
  getDiseaseSurveillance: () => request<DiseaseOutbreak[]>('/ministry/surveillance'),
  getHospitalStats: (region?: string) => request<HospitalStat[]>(`/ministry/hospitals${region ? `?region=${region}` : ''}`),
  getLabStats: (region?: string) => request<LabStat[]>(`/ministry/labs${region ? `?region=${region}` : ''}`),
  getAlerts: () => request<Alert[]>('/ministry/alerts'),
  acknowledgeAlert: (id: string) => request<void>(`/ministry/alerts/${id}/acknowledge`, { method: 'POST' }),
  getVaccinationData: () => request<VaccinationData[]>('/ministry/vaccination'),
  getMortalityData: () => request<MortalityRecord[]>('/ministry/mortality'),
  getBirthData: () => request<BirthRecord[]>('/ministry/births'),
  getWorkforceData: () => request<WorkforceData[]>('/ministry/workforce'),
  getMedicationSupply: () => request<MedicationSupply[]>('/ministry/medications'),
  getBloodSupply: () => request<BloodSupply[]>('/ministry/blood'),
  getResources: () => request<ResourceMetric[]>('/ministry/resources'),
  getEmergencyResponses: () => request<EmergencyResponse[]>('/ministry/emergencies'),
  getReports: () => request<NationalReport[]>('/ministry/reports'),
  generateReport: (config: ReportConfig) => request<NationalReport>('/ministry/reports/generate', { method: 'POST', body: JSON.stringify(config) }),
  getRegionalAnalytics: (region: string) => request<any>(`/ministry/analytics/${region}`),
};
