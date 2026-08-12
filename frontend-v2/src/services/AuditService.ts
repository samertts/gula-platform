import { apiGet, apiPost } from '../api/client';
import type { PaginatedResponse } from '../api/types';

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  userId: string;
  userEmail: string;
  action: string;
  resource: string;
  resourceId: string;
  changes?: { before: any; after: any };
  metadata: {
    ip: string;
    userAgent: string;
    severity: 'info' | 'warning' | 'critical';
  };
}

export const AuditService = {
  async log(params: {
    action: string;
    resource: string;
    resourceId: string;
    changes?: { before: any; after: any };
    severity?: 'info' | 'warning' | 'critical';
  }) {
    try {
      await apiPost('/audit/logs', {
        action: params.action,
        resource_type: params.resource,
        resource_id: params.resourceId,
        changes: params.changes || null,
        severity: params.severity || 'info',
      });
    } catch (error) {
      console.error('Audit Logging Failed:', error);
    }
  },

  async getLogs(params?: {
    resourceId?: string;
    action?: string;
    user_id?: string;
    skip?: number;
    limit?: number;
  }): Promise<AuditLogEntry[]> {
    try {
      const response = await apiGet<PaginatedResponse<AuditLogEntry>>('/audit/logs', params as Record<string, any>);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch audit logs:', error);
      return [];
    }
  },
};
