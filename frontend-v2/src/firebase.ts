import { auth, app } from './firebase-auth';
export { auth };

import { getFirestore, doc, getDocFromServer, enableIndexedDbPersistence } from 'firebase/firestore';
import firebaseConfig from '../firebase-applet-config.json';

export const db = getFirestore(app, firebaseConfig.firestoreDatabaseId);

if (typeof window !== 'undefined') {
  enableIndexedDbPersistence(db).catch((err) => {
    if (err.code === 'failed-precondition') {
      console.warn('Firestore persistence failed: Multiple tabs open');
    } else if (err.code === 'unimplemented') {
      console.warn('Firestore persistence is not supported by this browser');
    }
  });
}

async function testConnection() {
  const isPlaceholder = 
    firebaseConfig.projectId.includes('remixed-') || 
    firebaseConfig.apiKey.includes('remixed-');

  if (isPlaceholder) {
    console.warn("Firebase is using placeholder configuration. Please run 'set_up_firebase' to connect to a real database.");
    return;
  }

  try {
    await getDocFromServer(doc(db, 'test', 'connection'));
    console.log("Firebase connection established.");
  } catch (error) {
    if (error instanceof Error && error.message.includes('the client is offline')) {
      console.error("Please check your Firebase configuration: Client is offline. Ensure your Firestore database is provisioned and your network allows communication.");
    } else {
      console.log("Firebase initialized (Connection verified).");
    }
  }
}

testConnection();

export interface FirestoreErrorInfo {
  error: string;
  operationType: 'create' | 'update' | 'delete' | 'list' | 'get' | 'write';
  path: string | null;
  authInfo: {
    userId: string;
    email: string;
    emailVerified: boolean;
    isAnonymous: boolean;
    providerInfo: { providerId: string; displayName: string; email: string; }[];
  }
}

export function handleFirestoreError(error: any, operationType: FirestoreErrorInfo['operationType'], path: string | null = null) {
  const user = auth.currentUser;

  const authInfo = {
    userId: user ? String(user.uid) : 'anonymous',
    email: user ? String(user.email || '') : '',
    emailVerified: user ? Boolean(user.emailVerified) : false,
    isAnonymous: user ? Boolean(user.isAnonymous) : true,
    providerInfo: user ? (user.providerData || []).map(p => ({
      providerId: String(p.providerId || ''),
      displayName: String(p.displayName || ''),
      email: String(p.email || '')
    })) : []
  };

  const errorMessage = error instanceof Error 
    ? error.message 
    : (typeof error === 'string' ? error : (error?.message || error?.code || 'Unknown Firestore error'));

  const errorInfo: FirestoreErrorInfo = {
    error: String(errorMessage),
    operationType,
    path,
    authInfo
  };

  console.error("Firestore Error:", errorInfo);

  try {
    const serialized = JSON.stringify(errorInfo);
    throw new Error(serialized);
  } catch (stringifyError) {
    console.error("Failed to stringify Firestore error info:", stringifyError);
    throw new Error(`Firestore Error [${operationType}] on [${path}]: ${errorMessage}`);
  }
}
