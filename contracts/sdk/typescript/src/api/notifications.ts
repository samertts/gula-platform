import { GulaClient } from '../client';
import {
  NotifyRequest, NotificationRecord, NotificationPreferences,
  ListResponse, PaginationParams,
} from '../types';

export class NotificationsAPI {
  constructor(private client: GulaClient) {}

  async list(params?: PaginationParams & { read?: boolean; type?: string }): Promise<ListResponse<NotificationRecord>> {
    return this.client.get<ListResponse<NotificationRecord>>('/notifications', params as Record<string, unknown>);
  }

  async create(data: { title: string; body: string; type?: string }): Promise<NotificationRecord> {
    return this.client.post<NotificationRecord>('/notifications', data);
  }

  async markRead(id: number): Promise<NotificationRecord> {
    return this.client.put<NotificationRecord>(`/notifications/${id}/read`);
  }

  async markAllRead(): Promise<void> {
    return this.client.put('/notifications/read-all');
  }

  async delete(id: number): Promise<void> {
    return this.client.delete(`/notifications/${id}`);
  }

  async stats(): Promise<{ unread: number; total: number }> {
    return this.client.get('/notifications/stats');
  }

  async getPreferences(): Promise<NotificationPreferences> {
    return this.client.get<NotificationPreferences>('/notifications/preferences');
  }

  async updatePreferences(data: Partial<NotificationPreferences>): Promise<NotificationPreferences> {
    return this.client.put<NotificationPreferences>('/notifications/preferences', data);
  }

  async test(data: { channel: string }): Promise<void> {
    return this.client.post('/notifications/test', data);
  }

  async sendResult(data: NotifyRequest): Promise<void> {
    return this.client.post('/notify/send', data);
  }
}
