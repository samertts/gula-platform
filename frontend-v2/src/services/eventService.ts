import { apiGet, apiPost } from '../api/client';

export type GulaEventType =
  | 'RESULT_READY'
  | 'CRITICAL_ALERT'
  | 'CONSENT_GRANTED'
  | 'CONSENT_REVOKED'
  | 'ORDER_PLACED'
  | 'SLA_BREACH';

export interface GulaEvent {
  id?: string;
  type: GulaEventType;
  payload: any;
  recipientId: string;
  senderId: string;
  wing: 'citizen' | 'doctor' | 'lab';
  read: boolean;
  createdAt: any;
}

export const emitEvent = async (event: Omit<GulaEvent, 'createdAt' | 'read' | 'id'>) => {
  try {
    await apiPost('/events', event);
  } catch (error) {
    console.error('Failed to emit event:', error);
  }
};

export const subscribeToEvents = (userId: string, callback: (events: GulaEvent[]) => void) => {
  const poll = async () => {
    try {
      const result = await apiGet<{ data: GulaEvent[] }>('/events', { recipient_id: userId });
      callback(result.data || []);
    } catch {
      callback([]);
    }
  };
  poll();
  const interval = setInterval(poll, 30000);
  return () => clearInterval(interval);
};
