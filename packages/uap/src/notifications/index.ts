import { create } from 'zustand';
import { secureId } from '../security/secureRandom';

export type NotificationChannel = 'push' | 'sms' | 'email' | 'in_app' | 'webhook';
export type NotificationPriority = 'low' | 'normal' | 'high' | 'critical';
export type NotificationStatus = 'pending' | 'sent' | 'delivered' | 'read' | 'failed';

export interface Notification {
  id: string;
  title: string;
  body: string;
  channel: NotificationChannel;
  priority: NotificationPriority;
  status: NotificationStatus;
  recipientId: string;
  recipientChannel?: string;
  templateId?: string;
  data?: Record<string, unknown>;
  createdAt: number;
  sentAt?: number;
  deliveredAt?: number;
  readAt?: number;
  retries: number;
  error?: string;
  category?: string;
  actions?: { label: string; action: string; url?: string }[];
}

export interface NotificationTemplate {
  id: string;
  name: string;
  channels: NotificationChannel[];
  subject: string;
  body: string;
  variables: string[];
  locale: string;
}

interface NotificationState {
  notifications: Notification[];
  templates: NotificationTemplate[];
  unreadCount: number;
  totalCount: number;

  addNotification: (notif: Omit<Notification, 'id' | 'createdAt' | 'status' | 'retries'>) => void;
  markRead: (id: string) => void;
  markAllRead: () => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
  addTemplate: (template: NotificationTemplate) => void;
  renderTemplate: (templateId: string, variables: Record<string, string>) => { subject: string; body: string } | null;
  sendNotification: (notifId: string) => Promise<boolean>;
  retryFailed: () => void;
  getByPriority: (priority: NotificationPriority) => Notification[];
}

export const useNotificationPlatform = create<NotificationState>((set, get) => ({
  notifications: [],
  templates: [],
  unreadCount: 0,
  totalCount: 0,

  addNotification: (notif) => {
    const notification: Notification = {
      ...notif,
      id: secureId('notif'),
      createdAt: Date.now(),
      status: 'pending',
      retries: 0,
    };
    set((state) => ({
      notifications: [notification, ...state.notifications],
      unreadCount: state.unreadCount + 1,
      totalCount: state.totalCount + 1,
    }));
  },

  markRead: (id) => {
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.id === id ? { ...n, status: 'read' as const, readAt: Date.now() } : n
      ),
      unreadCount: Math.max(0, state.unreadCount - 1),
    }));
  },

  markAllRead: () => {
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.status === 'delivered' || n.status === 'sent'
          ? { ...n, status: 'read' as const, readAt: Date.now() }
          : n
      ),
      unreadCount: 0,
    }));
  },

  removeNotification: (id) => {
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
      totalCount: state.totalCount - 1,
      unreadCount: state.notifications.find((n) => n.id === id && n.status !== 'read')
        ? state.unreadCount - 1
        : state.unreadCount,
    }));
  },

  clearAll: () => set({ notifications: [], unreadCount: 0, totalCount: 0 }),

  addTemplate: (template) => {
    set((state) => ({ templates: [...state.templates, template] }));
  },

  renderTemplate: (templateId, variables) => {
    const template = get().templates.find((t) => t.id === templateId);
    if (!template) return null;
    let subject = template.subject;
    let body = template.body;
    for (const [key, value] of Object.entries(variables)) {
      subject = subject.replace(`{{${key}}}`, value);
      body = body.replace(`{{${key}}}`, value);
    }
    return { subject, body };
  },

  sendNotification: async (notifId) => {
    const notif = get().notifications.find((n) => n.id === notifId);
    if (!notif) return false;
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.id === notifId ? { ...n, status: 'sent', sentAt: Date.now() } : n
      ),
    }));
    return true;
  },

  retryFailed: () => {
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.status === 'failed' && n.retries < 5
          ? { ...n, status: 'pending', retries: n.retries + 1 }
          : n
      ),
    }));
  },

  getByPriority: (priority) => get().notifications.filter((n) => n.priority === priority),
}));

export const scheduleNotification = (
  notif: Omit<Notification, 'id' | 'createdAt' | 'status' | 'retries'>,
  delayMs: number
): Promise<string> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const id = `scheduled-${Date.now()}`;
      useNotificationPlatform.getState().addNotification(notif);
      resolve(id);
    }, delayMs);
  });
};
