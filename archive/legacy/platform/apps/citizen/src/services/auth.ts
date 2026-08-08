import { apiRequest, setAuthToken, getAuthToken } from './api';
import type { CitizenUser } from '../types';
import { openDB } from 'idb';

interface AuthResponse {
  token: string;
  refreshToken: string;
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
  setAuthToken(response.token);
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
  setAuthToken(response.token);
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
  setAuthToken(response.token);
  await storeUserData(response.user);
  return response;
}

export async function refreshToken(): Promise<string | null> {
  const refreshTokenStr = localStorage.getItem('gula_citizen_refresh');
  if (!refreshTokenStr) return null;

  try {
    const response = await apiRequest<{ token: string }>('/auth/citizen/refresh', {
      method: 'POST',
      body: JSON.stringify({ refreshToken: refreshTokenStr }),
      skipAuth: true,
    });
    setAuthToken(response.token);
    return response.token;
  } catch {
    logout();
    return null;
  }
}

export async function getCurrentUser(): Promise<CitizenUser | null> {
  const cached = await getStoredUser();
  if (!navigator.onLine) return cached;

  try {
    const response = await apiRequest<{ user: CitizenUser }>('/auth/citizen/me');
    await storeUserData(response.user);
    return response.user;
  } catch {
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
  localStorage.removeItem('gula_citizen_refresh');
  localStorage.removeItem('gula_citizen_user');
}

async function storeUserData(user: CitizenUser): Promise<void> {
  try {
    const db = await openDB('gula-citizen-offline', 1);
    await db.put('cache', { key: 'current_user', data: user, timestamp: Date.now() });
    localStorage.setItem('gula_citizen_user', JSON.stringify(user));
  } catch {
    localStorage.setItem('gula_citizen_user', JSON.stringify(user));
  }
}

async function getStoredUser(): Promise<CitizenUser | null> {
  try {
    const raw = localStorage.getItem('gula_citizen_user');
    if (raw) return JSON.parse(raw);
  } catch {}
  return null;
}

export function isAuthenticated(): boolean {
  return !!getAuthToken() || !!localStorage.getItem('gula_citizen_user');
}
