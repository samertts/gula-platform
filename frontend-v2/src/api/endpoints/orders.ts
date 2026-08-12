import { apiGet, apiPost } from '../client';
import type { LabOrder, CreateOrderRequest, CreateResultItem, PaginatedResponse } from '../types';

export async function listOrders(params?: { skip?: number; limit?: number; search?: string }): Promise<PaginatedResponse<LabOrder>> {
  return apiGet<PaginatedResponse<LabOrder>>('/orders', params as Record<string, any>);
}

export async function getOrder(orderId: string): Promise<LabOrder> {
  return apiGet<LabOrder>(`/orders/${orderId}`);
}

export async function createOrder(data: CreateOrderRequest): Promise<LabOrder> {
  return apiPost<LabOrder>('/orders', data);
}

export async function validateOrder(orderId: string): Promise<LabOrder> {
  return apiPost<LabOrder>(`/orders/${orderId}/validate`);
}

export async function cancelOrder(orderId: string): Promise<LabOrder> {
  return apiPost<LabOrder>(`/orders/${orderId}/cancel`);
}

export async function createBatchOrders(orders: CreateOrderRequest[]): Promise<LabOrder[]> {
  return apiPost<LabOrder[]>('/batch/orders', { orders });
}

export async function getTestProfiles(): Promise<any[]> {
  return apiGet<any[]>('/test-profiles');
}

export async function getOrderIntelligence(orderId: string): Promise<any> {
  return apiGet<any>(`/orders/${orderId}/intelligence`);
}

export async function analyzeResults(results: CreateResultItem[]): Promise<any> {
  return apiPost<any>('/analyze', { results });
}
