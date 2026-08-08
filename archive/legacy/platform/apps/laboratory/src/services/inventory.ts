import { apiRequest } from './api';
import type { InventoryItem } from '@/utils/types';

export interface InventoryListParams {
  page?: number;
  perPage?: number;
  category?: string;
  search?: string;
  lowStock?: boolean;
  expiring?: boolean;
  labId?: string;
}

export const inventoryService = {
  async list(params: InventoryListParams = {}): Promise<{ data: InventoryItem[]; total: number }> {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => { if (v !== undefined) query.set(k, String(v)); });
    return apiRequest(`/inventory?${query.toString()}`);
  },

  async getById(id: string): Promise<InventoryItem> {
    return apiRequest<InventoryItem>(`/inventory/${id}`);
  },

  async create(data: Partial<InventoryItem>): Promise<InventoryItem> {
    return apiRequest<InventoryItem>('/inventory', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async update(id: string, data: Partial<InventoryItem>): Promise<InventoryItem> {
    return apiRequest<InventoryItem>(`/inventory/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  async adjustQuantity(id: string, data: {
    adjustment: number;
    reason: string;
    performedBy: string;
  }): Promise<InventoryItem> {
    return apiRequest<InventoryItem>(`/inventory/${id}/adjust`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async getLowStock(params: { labId?: string } = {}): Promise<InventoryItem[]> {
    const query = new URLSearchParams();
    if (params.labId) query.set('lab_id', params.labId);
    return apiRequest<InventoryItem[]>(`/inventory/low-stock?${query.toString()}`);
  },

  async getExpiring(params: { labId?: string; days?: number } = {}): Promise<InventoryItem[]> {
    const query = new URLSearchParams();
    if (params.labId) query.set('lab_id', params.labId);
    if (params.days) query.set('days', String(params.days));
    return apiRequest<InventoryItem[]>(`/inventory/expiring?${query.toString()}`);
  },

  async getStats(params: { labId?: string } = {}): Promise<{
    total: number;
    lowStock: number;
    expiring: number;
    outOfStock: number;
    totalValue: number;
  }> {
    const query = new URLSearchParams();
    if (params.labId) query.set('lab_id', params.labId);
    return apiRequest(`/inventory/stats?${query.toString()}`);
  },
};
