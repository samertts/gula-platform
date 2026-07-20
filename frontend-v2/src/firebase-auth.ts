import { initializeApp } from 'firebase/app';
import { getAuth, setPersistence, browserLocalPersistence } from 'firebase/auth';
import firebaseConfig from '../firebase-applet-config.json';

const app = initializeApp(firebaseConfig);

export const auth = getAuth(app);
export { app };

setPersistence(auth, browserLocalPersistence).catch(err => {
  console.warn("Auth persistence could not be set:", err);
});
