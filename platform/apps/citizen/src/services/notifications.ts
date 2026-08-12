import { apiRequest } from './api';
import { cacheNotifications, getCachedNotifications } from './offline';
import type { Notification } from '../types';

type NotificationPermissionListener = (permission: NotificationPermission) => void;

const listeners: Set<NotificationPermissionListener> = new Set();

export function addNotificationListener(listener: NotificationPermissionListener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export async function requestPermission(): Promise<NotificationPermission> {
  if (!('Notification' in window)) {
    return 'denied';
  }

  try {
    const permission = await Notification.requestPermission();
    if (permission === 'granted') {
      await registerPushSubscription();
    }
    listeners.forEach((l) => l(permission));
    return permission;
  } catch {
    return 'denied';
  }
}

async function registerPushSubscription(): Promise<void> {
  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: import.meta.env.VITE_VAPID_PUBLIC_KEY,
    });

    await apiRequest('/notifications/push/register', {
      method: 'POST',
      body: JSON.stringify({ subscription: subscription.toJSON() }),
    });
  } catch (error) {
    console.error('Push registration failed:', error);
  }
}

export async function getNotifications(): Promise<Notification[]> {
  if (!navigator.onLine) {
    return getCachedNotifications();
  }

  try {
    const response = await apiRequest<{ notifications: Notification[] }>('/citizen/notifications');
    await cacheNotifications(response.notifications);
    return response.notifications;
  } catch {
    return getCachedNotifications();
  }
}

export async function markAsRead(notificationId: string): Promise<void> {
  await apiRequest(`/notifications/${notificationId}/read`, {
    method: 'POST',
  });
}

export async function markAllAsRead(): Promise<void> {
  await apiRequest('/notifications/read-all', {
    method: 'POST',
  });
}

export async function deleteNotification(notificationId: string): Promise<void> {
  await apiRequest(`/notifications/${notificationId}`, {
    method: 'DELETE',
  });
}

export async function getUnreadCount(): Promise<number> {
  try {
    const response = await apiRequest<{ count: number }>('/citizen/notifications/unread-count');
    return response.count;
  } catch {
    const cached = await getCachedNotifications();
    return cached.filter((n) => !n.read).length;
  }
}

export function showLocalNotification(title: string, body: string, icon?: string): void {
  if (!('Notification' in window) || Notification.permission !== 'granted') return;

  navigator.serviceWorker.ready.then((registration) => {
    const options: NotificationOptions & { vibrate?: number[] } = {
      body,
      icon: icon || '/icons/icon-192x192.png',
      badge: '/icons/icon-96x96.png',
      vibrate: [200, 100, 200],
    };
    registration.showNotification(title, options);
  });
}
