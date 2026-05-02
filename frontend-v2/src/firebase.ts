import { initializeApp } from 'firebase/app';
import { getAuth, setPersistence, browserLocalPersistence } from 'firebase/auth';
import { getFirestore, doc, getDocFromServer, enableIndexedDbPersistence } from 'firebase/firestore';
import firebaseConfig from '../firebase-applet-config.json';

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);

// Explicitly set persistence to prevent certain internal state errors in iframes
setPersistence(auth, browserLocalPersistence).catch(err => {
  console.warn("Auth persistence could not be set:", err);
});

export const db = getFirestore(app, firebaseConfig.firestoreDatabaseId);

// Enable offline persistence
if (typeof window !== 'undefined') {
  enableIndexedDbPersistence(db).catch((err) => {
    if (err.code === 'failed-precondition') {
      console.warn('Firestore persistence failed: Multiple tabs open');
    } else if (err.code === 'unimplemented') {
      console.warn('Firestore persistence is not supported by this browser');
    }
  });
}

// Connection test as required by guidelines
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
      // Missing permissions is expected for 'test/connection' based on rules
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
  
  // Create a clean, flat object for auth info to avoid any circular refs from the user object
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

  // Ensure error.message is just a string and doesn't contain weird data if it's a Firestore error object
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
    // Only stringify if we're not likely to have circular structures
    // The current mapping should have fixed it, but let's be safe
    const serialized = JSON.stringify(errorInfo);
    throw new Error(serialized);
  } catch (stringifyError) {
    // Fallback if stringify still fails for some reason
    console.error("Failed to stringify Firestore error info:", stringifyError);
    throw new Error(`Firestore Error [${operationType}] on [${path}]: ${errorMessage}`);
  }
}
