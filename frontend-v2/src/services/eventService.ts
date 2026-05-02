import { db } from '../firebase';
import { 
  collection, 
  addDoc, 
  serverTimestamp, 
  query, 
  where, 
  onSnapshot, 
  orderBy, 
  limit 
} from 'firebase/firestore';

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
    await addDoc(collection(db, 'events'), {
      ...event,
      read: false,
      createdAt: serverTimestamp()
    });
  } catch (error) {
    console.error('Failed to emit event:', error);
  }
};

export const subscribeToEvents = (userId: string, callback: (events: GulaEvent[]) => void) => {
  const q = query(
    collection(db, 'events'),
    where('recipientId', '==', userId),
    orderBy('createdAt', 'desc'),
    limit(20)
  );

  return onSnapshot(q, (snapshot) => {
    const events = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() } as GulaEvent));
    callback(events);
  }, (error) => {
    console.error("Error subscribing to events:", error);
  });
};
