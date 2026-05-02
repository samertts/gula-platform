import React, { createContext, useContext, useState, useEffect } from 'react';
import { 
  collection, 
  query, 
  where, 
  onSnapshot, 
  orderBy, 
  limit,
  updateDoc,
  doc,
  writeBatch
} from 'firebase/firestore';
import { auth, db } from '../firebase';
import { GulaEvent } from '../types/domain';
import { toast } from 'sonner';

interface NotificationContextType {
  notifications: GulaEvent[];
  unreadCount: number;
  markAsRead: (id: string) => Promise<void>;
  markAllAsRead: () => Promise<void>;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<GulaEvent[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    const user = auth.currentUser;
    if (!user) {
      setNotifications([]);
      setUnreadCount(0);
      return;
    }

    // Listen to notifications for the current user or broadcasted to everyone
    const q = query(
      collection(db, 'events'),
      where('recipientId', 'in', [user.uid, 'all']),
      orderBy('createdAt', 'desc'),
      limit(50)
    );

    let isInitialLoad = true;
    const unsubscribe = onSnapshot(q, (snapshot) => {
      const newNotifications: GulaEvent[] = [];
      let newUnreadCount = 0;

      snapshot.docs.forEach(doc => {
        const data = doc.data() as Omit<GulaEvent, 'id'>;
        const notification = { id: doc.id, ...data };
        newNotifications.push(notification);
        if (!notification.read) {
          newUnreadCount++;
        }
      });

      // Show toast for new unread notifications
      if (!isInitialLoad) {
        snapshot.docChanges().forEach(change => {
          if (change.type === 'added') {
            const data = change.doc.data() as GulaEvent;
            if (!data.read) {
               toast[data.priority === 'stat' ? 'error' : 'info'](data.title || 'New Notification', {
                 description: data.message,
               });
            }
          }
        });
      }

      setNotifications(newNotifications);
      setUnreadCount(newUnreadCount);
      isInitialLoad = false;
    }, (error) => {
      console.error("Error listening to notifications:", error);
    });

    return () => unsubscribe();
  }, []);

  const markAsRead = async (id: string) => {
    try {
      await updateDoc(doc(db, 'events', id), { read: true });
    } catch (error) {
      console.error("Error marking notification as read:", error);
    }
  };

  const markAllAsRead = async () => {
    const unread = notifications.filter(n => !n.read);
    if (unread.length === 0) return;

    try {
      const batch = writeBatch(db);
      unread.forEach(n => {
        batch.update(doc(db, 'events', n.id), { read: true });
      });
      await batch.commit();
    } catch (error) {
      console.error("Error marking all as read:", error);
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
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};
