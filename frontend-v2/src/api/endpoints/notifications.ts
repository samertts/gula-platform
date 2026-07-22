import { apiGet, apiPost } from '../client';
import type { NotificationRecord } from '../types';

export async function sendNotification(orderId: string, channel: 'whatsapp' | 'sms'): Promise<{ url: string }> {
  return apiPost<{ url: string }>('/notify/send', { order_id: orderId, channel });
}

export async function getNotificationHistory(orderId: string): Promise<NotificationRecord[]> {
  return apiGet<NotificationRecord[]>(`/notify/history/${orderId}`);
}
