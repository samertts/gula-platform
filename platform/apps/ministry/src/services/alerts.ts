import { api } from './api';
import type { Alert } from './api';

export const alertsService = {
  getAlerts: (): Promise<Alert[]> => api.getAlerts(),
  acknowledge: (id: string): Promise<void> => api.acknowledgeAlert(id),
};

export interface AlertStats {
  total: number;
  critical: number;
  danger: number;
  warning: number;
  info: number;
  unacknowledged: number;
}

export function computeAlertStats(alerts: Alert[]): AlertStats {
  return {
    total: alerts.length,
    critical: alerts.filter(a => a.severity === 'critical').length,
    danger: alerts.filter(a => a.severity === 'danger').length,
    warning: alerts.filter(a => a.severity === 'warning').length,
    info: alerts.filter(a => a.severity === 'info').length,
    unacknowledged: alerts.filter(a => !a.acknowledged).length,
  };
}

export function getAlertsBySeverity(alerts: Alert[]): Record<string, Alert[]> {
  const grouped: Record<string, Alert[]> = { critical: [], danger: [], warning: [], info: [] };
  for (const alert of alerts) {
    if (grouped[alert.severity]) grouped[alert.severity].push(alert);
  }
  return grouped;
}

export function getAlertsByRegion(alerts: Alert[]): Map<string, Alert[]> {
  const map = new Map<string, Alert[]>();
  for (const alert of alerts) {
    const existing = map.get(alert.region) || [];
    existing.push(alert);
    map.set(alert.region, existing);
  }
  return map;
}

export function getAlertPriorityScore(alert: Alert): number {
  const severityScore = { critical: 100, danger: 70, warning: 40, info: 10 };
  const base = severityScore[alert.severity] || 0;
  const hoursOld = (Date.now() - new Date(alert.createdAt).getTime()) / 3600000;
  return Math.round(base + Math.max(0, 30 - hoursOld));
}
