import { apiRequest } from './api';

export interface Asset {
  id: string;
  name: string;
  nameAr: string;
  type: string;
  typeAr: string;
  model: string;
  serialNumber: string;
  manufacturer: string;
  department: string;
  departmentAr: string;
  location: string;
  locationAr: string;
  purchaseDate: string;
  purchaseCost: number;
  currentValue: number;
  warrantyExpiry: string;
  status: 'operational' | 'under_maintenance' | 'repair' | 'decommissioned' | 'reserve';
  condition: 'excellent' | 'good' | 'fair' | 'poor';
  lastMaintenanceDate: string | null;
  nextMaintenanceDate: string | null;
  maintenanceInterval: number;
  maintenanceIntervalUnit: 'days' | 'months' | 'years';
  totalMaintenanceCost: number;
  assignedTo: string;
  assignedToAr: string;
  notes: string;
  createdAt: string;
  updatedAt: string;
}

export interface AssetMaintenanceRecord {
  id: string;
  assetId: string;
  type: 'preventive' | 'corrective' | 'emergency' | 'inspection';
  description: string;
  descriptionAr: string;
  performedBy: string;
  performedByAr: string;
  cost: number;
  date: string;
  nextScheduledDate: string | null;
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled';
  notes: string;
}

export async function getAssets(params?: {
  department?: string;
  status?: string;
  type?: string;
  search?: string;
}): Promise<Asset[]> {
  const searchParams = new URLSearchParams();
  if (params?.department) searchParams.set('department', params.department);
  if (params?.status) searchParams.set('status', params.status);
  if (params?.type) searchParams.set('type', params.type);
  if (params?.search) searchParams.set('search', params.search);
  const qs = searchParams.toString();
  return apiRequest(`/hospital/assets${qs ? `?${qs}` : ''}`);
}

export async function getAsset(id: string): Promise<Asset> {
  return apiRequest(`/hospital/assets/${id}`);
}

export async function getAssetMaintenanceHistory(assetId: string): Promise<AssetMaintenanceRecord[]> {
  return apiRequest(`/hospital/assets/${assetId}/maintenance`);
}

export async function scheduleMaintenance(
  assetId: string,
  data: {
    type: AssetMaintenanceRecord['type'];
    description: string;
    descriptionAr: string;
    scheduledDate: string;
    notes?: string;
  },
): Promise<AssetMaintenanceRecord> {
  return apiRequest(`/hospital/assets/${assetId}/maintenance`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getAssetStats(): Promise<{
  total: number;
  operational: number;
  underMaintenance: number;
  decommissioned: number;
  totalValue: number;
  totalMaintenanceCost: number;
  overdueMaintenance: number;
}> {
  return apiRequest('/hospital/assets/stats');
}
