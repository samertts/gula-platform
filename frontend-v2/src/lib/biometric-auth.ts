import { browserLocalPersistence, setPersistence, signInWithEmailAndPassword, createUserWithEmailAndPassword, sendPasswordResetEmail, User } from 'firebase/auth';
import { doc, getDoc, setDoc, serverTimestamp } from 'firebase/firestore';
import { auth, db } from '../firebase';

interface WebAuthnCredential {
  credentialId: string;
  publicKey: string;
  counter: number;
  transports?: AuthenticatorTransport[];
  createdAt: number;
  deviceName: string;
}

interface BiometricSession {
  authenticated: boolean;
  userId: string;
  method: 'webauthn' | 'password' | 'fallback';
  timestamp: number;
  expiresAt: number;
}

const SESSION_DURATION_MS = 24 * 60 * 60 * 1000;
const WEBAUTHN_COLLECTION = 'webauthn_credentials';

function base64UrlToArrayBuffer(base64Url: string): ArrayBuffer {
  const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
  const padding = base64.length % 4 === 0 ? '' : '='.repeat(4 - (base64.length % 4));
  const binary = atob(base64 + padding);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes.buffer;
}

function arrayBufferToBase64Url(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  const binary = String.fromCharCode(...bytes);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function isWebAuthnSupported(): boolean {
  return typeof window !== 'undefined' && !!window.PublicKeyCredential;
}

async function getDeviceName(): Promise<string> {
  if (typeof window === 'undefined') return 'Unknown Device';
  const ua = navigator.userAgent;
  if (ua.includes('Android')) return `Android - ${ua.match(/Android\s[\d.]+/)?.[0] || 'Unknown'}`;
  if (ua.includes('iPhone') || ua.includes('iPad')) return `iOS - ${ua.match(/OS\s[\d_]+/)?.[0]?.replace(/_/g, '.') || 'Unknown'}`;
  if (ua.includes('Windows')) return `Windows - ${ua.match(/Windows\sNT\s[\d.]+/)?.[0] || 'Unknown'}`;
  if (ua.includes('Mac OS')) return `macOS - ${ua.match(/Mac\sOS\sX\s[\d_]+/)?.[0]?.replace(/_/g, '.') || 'Unknown'}`;
  if (ua.includes('Linux')) return 'Linux Desktop';
  return 'Unknown Device';
}

async function getStoredCredentials(userId: string): Promise<WebAuthnCredential[]> {
  try {
    const ref = doc(db, WEBAUTHN_COLLECTION, userId);
    const snap = await getDoc(ref);
    return snap.exists() ? (snap.data().credentials || []) : [];
  } catch {
    return [];
  }
}

async function saveCredential(userId: string, credential: WebAuthnCredential): Promise<void> {
  const ref = doc(db, WEBAUTHN_COLLECTION, userId);
  const snap = await getDoc(ref);
  const existing = snap.exists() ? (snap.data().credentials || []) : [];
  existing.push(credential);
  await setDoc(ref, { credentials: existing, updatedAt: serverTimestamp() }, { merge: true });
}

async function removeCredential(userId: string, credentialId: string): Promise<void> {
  const ref = doc(db, WEBAUTHN_COLLECTION, userId);
  const snap = await getDoc(ref);
  if (!snap.exists()) return;
  const existing: WebAuthnCredential[] = snap.data().credentials || [];
  const filtered = existing.filter(c => c.credentialId !== credentialId);
  await setDoc(ref, { credentials: filtered, updatedAt: serverTimestamp() }, { merge: true });
}

export async function generateRegistrationOptions(userId: string, userEmail: string, userDisplayName: string): Promise<PublicKeyCredentialCreationOptions> {
  const challenge = crypto.getRandomValues(new Uint8Array(32));
  const userIdEnc = new TextEncoder().encode(userId);
  return {
    challenge,
    rp: { name: 'GULA Platform', id: window.location.hostname },
    user: { id: userIdEnc, name: userEmail, displayName: userDisplayName },
    pubKeyCredParams: [
      { type: 'public-key', alg: -7 },
      { type: 'public-key', alg: -257 },
    ],
    timeout: 60000,
    attestation: 'none',
    authenticatorSelection: {
      authenticatorAttachment: 'platform',
      userVerification: 'required',
      residentKey: 'preferred',
    },
  };
}

export async function registerBiometric(userId: string, userEmail: string, userDisplayName: string): Promise<{ success: boolean; error?: string }> {
  if (!isWebAuthnSupported()) return { success: false, error: 'WebAuthn not supported in this browser' };

  try {
    const options = await generateRegistrationOptions(userId, userEmail, userDisplayName);
    const cred = await navigator.credentials.create({ publicKey: options }) as PublicKeyCredential;
    const response = cred.response as AuthenticatorAttestationResponse;

    const newCredential: WebAuthnCredential = {
      credentialId: arrayBufferToBase64Url(cred.rawId),
      publicKey: arrayBufferToBase64Url(response.getPublicKey()!),
      counter: 0,
      transports: response.getTransports?.() || [],
      createdAt: Date.now(),
      deviceName: await getDeviceName(),
    };

    await saveCredential(userId, newCredential);
    return { success: true };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : 'Unknown error during registration' };
  }
}

export async function generateAuthenticationOptions(userId: string): Promise<PublicKeyCredentialRequestOptions | null> {
  const credentials = await getStoredCredentials(userId);
  if (credentials.length === 0) return null;

  const allowCredentials: PublicKeyCredentialDescriptor[] = credentials.map(c => ({
    id: base64UrlToArrayBuffer(c.credentialId),
    type: 'public-key' as PublicKeyCredentialType,
    transports: c.transports || ['internal'],
  }));

  return {
    challenge: crypto.getRandomValues(new Uint8Array(32)),
    timeout: 60000,
    rpId: window.location.hostname,
    allowCredentials,
    userVerification: 'required',
  };
}

export async function authenticateBiometric(userId: string): Promise<BiometricSession | null> {
  if (!isWebAuthnSupported()) return null;

  try {
    const options = await generateAuthenticationOptions(userId);
    if (!options) return null;

    const cred = await navigator.credentials.get({ publicKey: options }) as PublicKeyCredential;
    if (!cred) return null;

    const session: BiometricSession = {
      authenticated: true,
      userId,
      method: 'webauthn',
      timestamp: Date.now(),
      expiresAt: Date.now() + SESSION_DURATION_MS,
    };
    sessionStorage.setItem('gula_biometric_session', JSON.stringify(session));
    return session;
  } catch (err) {
    console.error('Biometric authentication failed:', err);
    return null;
  }
}

export async function checkBiometricSession(): Promise<BiometricSession | null> {
  try {
    const raw = sessionStorage.getItem('gula_biometric_session');
    if (!raw) return null;
    const session: BiometricSession = JSON.parse(raw);
    if (session.expiresAt < Date.now()) {
      sessionStorage.removeItem('gula_biometric_session');
      return null;
    }
    return session;
  } catch {
    return null;
  }
}

export async function clearBiometricSession(): Promise<void> {
  sessionStorage.removeItem('gula_biometric_session');
}

export async function listBiometricDevices(userId: string): Promise<WebAuthnCredential[]> {
  return getStoredCredentials(userId);
}

export async function removeBiometricDevice(userId: string, credentialId: string): Promise<void> {
  await removeCredential(userId, credentialId);
}

export async function loginWithPassword(email: string, password: string): Promise<{ user: User | null; error?: string }> {
  try {
    await setPersistence(auth, browserLocalPersistence);
    const result = await signInWithEmailAndPassword(auth, email, password);
    return { user: result.user };
  } catch (err: any) {
    const code = err.code || '';
    const messages: Record<string, string> = {
      'auth/user-not-found': 'No account found with this email',
      'auth/wrong-password': 'Invalid password',
      'auth/invalid-credential': 'Invalid email or password',
      'auth/too-many-requests': 'Too many attempts. Try again later',
      'auth/user-disabled': 'This account has been disabled',
    };
    return { user: null, error: messages[code] || err.message || 'Login failed' };
  }
}

export async function registerWithPassword(email: string, password: string): Promise<{ user: User | null; error?: string }> {
  try {
    const result = await createUserWithEmailAndPassword(auth, email, password);
    return { user: result.user };
  } catch (err: any) {
    const code = err.code || '';
    const messages: Record<string, string> = {
      'auth/email-already-in-use': 'An account with this email already exists',
      'auth/weak-password': 'Password must be at least 6 characters',
      'auth/invalid-email': 'Invalid email address',
    };
    return { user: null, error: messages[code] || err.message || 'Registration failed' };
  }
}

export async function resetPassword(email: string): Promise<{ success: boolean; error?: string }> {
  try {
    await sendPasswordResetEmail(auth, email);
    return { success: true };
  } catch (err: any) {
    return { success: false, error: err.message || 'Failed to send reset email' };
  }
}

export async function isBiometricAvailable(): Promise<boolean> {
  if (!isWebAuthnSupported()) return false;
  try {
    const available = await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
    return available;
  } catch {
    return false;
  }
}

export async function getBiometricPlatformType(): Promise<'touchid' | 'faceid' | 'fingerprint' | 'windows_hello' | 'android_biometric' | 'none'> {
  const ua = navigator.userAgent;
  if (ua.includes('iPhone') || ua.includes('iPad')) {
    const match = ua.match(/iPhone\sOS\s([\d_]+)/);
    const major = match ? parseInt(match[1].split('_')[0]) : 0;
    return major >= 10 ? 'faceid' : 'touchid';
  }
  if (ua.includes('Mac OS') && ua.includes('Safari')) return 'touchid';
  if (ua.includes('Windows') && ua.includes('Edge')) return 'windows_hello';
  if (ua.includes('Android') && ua.includes('Chrome')) return 'android_biometric';
  if (ua.includes('Linux') && ua.includes('Firefox')) return 'fingerprint';
  return 'none';
}

export type { WebAuthnCredential, BiometricSession };
