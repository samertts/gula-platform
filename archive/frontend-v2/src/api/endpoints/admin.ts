import { apiGet, apiPost, apiPut, apiPatch } from '../client';
import type { AdminStats, Lab, UserInfo, AuditLogEntry, PaginatedResponse } from '../types';

export async function getAdminStats(): Promise<AdminStats> {
  return apiGet<AdminStats>('/admin/stats');
}

export async function listAdminLabs(params?: { skip?: number; limit?: number }): Promise<PaginatedResponse<Lab>> {
  return apiGet<PaginatedResponse<Lab>>('/admin/labs', params as Record<string, any>);
}

export async function toggleLab(labId: string): Promise<Lab> {
  return apiPut<Lab>(`/admin/labs/${labId}/toggle`);
}

export async function activateLab(labId: string): Promise<Lab> {
  return apiPut<Lab>(`/admin/labs/${labId}/activate`);
}

export async function getPendingLabs(): Promise<Lab[]> {
  return apiGet<Lab[]>('/admin/labs/pending');
}

export async function createLab(data: {
  name: string;
  city: string;
  admin_email: string;
  admin_password: string;
  admin_name: string;
}): Promise<Lab> {
  return apiPost<Lab>('/admin/labs', data);
}

export async function listUsers(params?: {
  role?: string;
  lab_id?: string;
  skip?: number;
  limit?: number;
}): Promise<PaginatedResponse<UserInfo>> {
  return apiGet<PaginatedResponse<UserInfo>>('/admin/users', params as Record<string, any>);
}

export async function createUser(data: {
  name: string;
  email: string;
  password: string;
  role: string;
  lab_id: string;
}): Promise<UserInfo> {
  return apiPost<UserInfo>('/admin/users', data);
}

export async function updateUserRole(userId: string, role: string): Promise<UserInfo> {
  return apiPatch<UserInfo>(`/admin/users/${userId}/role`, { role });
}

export async function toggleUser(userId: string): Promise<UserInfo> {
  return apiPut<UserInfo>(`/admin/users/${userId}/toggle`);
}

export async function getAuditLogs(params?: {
  action?: string;
  user_id?: string;
  skip?: number;
  limit?: number;
}): Promise<PaginatedResponse<AuditLogEntry>> {
  return apiGet<PaginatedResponse<AuditLogEntry>>('/admin/audit-logs', params as Record<string, any>);
}

export async function getSecurityStatus(): Promise<any> {
  return apiGet<any>('/security/status');
}
