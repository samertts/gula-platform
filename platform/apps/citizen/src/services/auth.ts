import { apiRequest, setAuthToken } from './api';
import { ApiError } from './api';
import type { CitizenUser } from '../types';
import { openDB } from 'idb';

interface AuthResponse {
  token?: string;
  refreshToken?: string;
  user: CitizenUser;
}

interface OTPResponse {
  success: boolean;
  verificationId: string;
  expiresIn: number;
}

export async function loginWithNationalId(
  nationalId: string,
  otp: string,
): Promise<AuthResponse> {
  const response = await apiRequest<AuthResponse>('/auth/citizen/login-national', {
    method: 'POST',
    body: JSON.stringify({ nationalId, otp }),
  });
  setAuthToken(null);
  await storeUserData(response.user);
  return response;
}

export async function loginWithPhone(phone: string): Promise<OTPResponse> {
  return apiRequest<OTPResponse>('/auth/citizen/send-otp', {
    method: 'POST',
    body: JSON.stringify({ phone, channel: 'sms' }),
  });
}

export async function loginWithEmail(email: string): Promise<OTPResponse> {
  return apiRequest<OTPResponse>('/auth/citizen/send-otp', {
    method: 'POST',
    body: JSON.stringify({ email, channel: 'email' }),
  });
}

export async function verifyOTP(
  verificationId: string,
  otp: string,
): Promise<AuthResponse> {
  const response = await apiRequest<AuthResponse>('/auth/citizen/verify-otp', {
    method: 'POST',
    body: JSON.stringify({ verificationId, otp }),
  });
  setAuthToken(null);
  await storeUserData(response.user);
  return response;
}

export async function registerCitizen(
  data: {
    nationalId: string;
    name: string;
    phone: string;
    email?: string;
    dateOfBirth: string;
    gender: 'male' | 'female';
  },
): Promise<AuthResponse> {
  const response = await apiRequest<AuthResponse>('/auth/citizen/register', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  setAuthToken(null);
  await storeUserData(response.user);
  return response;
}

export async function refreshToken(): Promise<boolean> {
  try {
    await apiRequest('/auth/refresh', {
      method: 'POST',
      skipAuth: true,
    });
    return true;
  } catch {
    logout();
    return false;
  }
}

export async function getCurrentUser(): Promise<CitizenUser | null> {
  const cached = await getStoredUser();
  if (!navigator.onLine) return cached;

  try {
    const response = await apiRequest<{ user: CitizenUser }>('/auth/citizen/me');
    await storeUserData(response.user);
    return response.user;
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      await clearStoredUser();
      return null;
    }
    return cached;
  }
}

export async function updateProfile(data: Partial<CitizenUser>): Promise<CitizenUser> {
  const response = await apiRequest<{ user: CitizenUser }>('/auth/citizen/profile', {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
  await storeUserData(response.user);
  return response.user;
}

export function logout(): void {
  setAuthToken(null);
  void apiRequest('/auth/logout', { method: 'POST', skipAuth: true }).catch(() => undefined);
  localStorage.removeItem('gula_citizen_user');
}

async function storeUserData(user: CitizenUser): Promise<void> {
  try {
    const db = await openDB('gula-citizen-offline', 1);
    await db.put('cache', { key: 'current_user', data: user, timestamp: Date.now() });
  } catch {
    // Offline user display cache is non-authoritative and contains no credentials.
  }
}

async function clearStoredUser(): Promise<void> {
  localStorage.removeItem('gula_citizen_user');
  try {
    const db = await openDB('gula-citizen-offline', 1);
    await db.delete('cache', 'current_user');
  } catch {
    // Cache cleanup is best effort; it must never recreate authentication state.
  }
}

async function getStoredUser(): Promise<CitizenUser | null> {
  try {
    const db = await openDB('gula-citizen-offline', 1);
    const cached = await db.get('cache', 'current_user');
    if (cached?.data) return cached.data as CitizenUser;
  } catch {}
  return null;
}

export function isAuthenticated(): boolean {
  // The provider's server session bootstrap is the only authoritative signal.
  return false;
}
