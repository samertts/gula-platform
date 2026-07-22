import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from './AuthContext';
import { apiGet, apiPost, apiPut } from '../api/client';
import { toast } from 'sonner';

interface GulaNotification {
  id: string;
  type: string;
  title?: string;
  message?: string;
  recipientId: string;
  read: boolean;
  priority?: string;
  createdAt: string;
}

interface NotificationContextType {
  notifications: GulaNotification[];
  unreadCount: number;
  markAsRead: (id: string) => Promise<void>;
  markAllAsRead: () => Promise<void>;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState<GulaNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const previousIdsRef = useRef<Set<string>>(new Set());

  const fetchNotifications = useCallback(async () => {
    if (!user) {
      setNotifications([]);
      setUnreadCount(0);
      return;
    }

    try {
      const result = await apiGet<{ data: GulaNotification[] }>('/notifications', {
        recipient_id: user.id,
        limit: 50,
      });
      const items = result?.data || [];
      const unread = items.filter(n => !n.read).length;

      const currentIds = new Set(items.map(n => n.id));
      for (const notification of items) {
        if (!previousIdsRef.current.has(notification.id) && !notification.read) {
          toast[notification.priority === 'stat' ? 'error' : 'info'](
            notification.title || 'New Notification',
            { description: notification.message },
          );
        }
      }
      previousIdsRef.current = currentIds;

      setNotifications(items);
      setUnreadCount(unread);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  }, [user]);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  const markAsRead = async (id: string) => {
    try {
      await apiPut(`/notifications/${id}/read`, {});
      setNotifications(prev =>
        prev.map(n => (n.id === id ? { ...n, read: true } : n)),
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await apiPost('/notifications/read-all', {});
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch (error) {
      console.error('Error marking all as read:', error);
    }
  };

  return (
    <NotificationContext.Provider value={{ notifications, unreadCount, markAsRead, markAllAsRead }}>
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};
