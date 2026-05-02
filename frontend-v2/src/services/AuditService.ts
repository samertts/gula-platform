import { 
  collection, 
  addDoc, 
  serverTimestamp, 
  query, 
  where, 
  orderBy, 
  limit, 
  getDocs 
} from 'firebase/firestore';
import { db, auth, handleFirestoreError } from '../firebase';
import { AuditLogEntry } from '../types/domain';

export const AuditService = {
  async log(params: {
    action: string;
    resource: string;
    resourceId: string;
    changes?: { before: any; after: any };
    severity?: AuditLogEntry['metadata']['severity'];
  }) {
    const user = auth.currentUser;
    if (!user) return;

    try {
      await addDoc(collection(db, 'audit_logs'), {
        timestamp: serverTimestamp(),
        userId: user.uid,
        userEmail: user.email,
        action: params.action,
        resource: params.resource,
        resourceId: params.resourceId,
        changes: params.changes || null,
        metadata: {
          ip: 'client-side-logged', // In a real system, this would be server-side
          userAgent: navigator.userAgent,
          severity: params.severity || 'info'
        }
      });
    } catch (error) {
      console.error("Audit Logging Failed:", error);
      // We don't throw here to avoid blocking the main operation
    }
  },

  async getLogs(resourceId?: string) {
    try {
      let q = query(
        collection(db, 'audit_logs'), 
        orderBy('timestamp', 'desc'), 
        limit(100)
      );
      
      if (resourceId) {
        q = query(q, where('resourceId', '==', resourceId));
      }

      const snapshot = await getDocs(q);
      return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
    } catch (error) {
      handleFirestoreError(error, 'list', 'audit_logs');
      return [];
    }
  }
};
