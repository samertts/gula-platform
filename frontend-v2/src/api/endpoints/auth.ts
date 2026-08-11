import { apiGet, apiPost, clearTokens } from '../client';
import type { LoginResponse, UserInfo } from '../types';

export async function login(email: string, password: string): Promise<LoginResponse> {
  return apiPost<LoginResponse>('/login', { email, password }, { skipAuth: true });
}

export async function logout(): Promise<void> {
  try {
    await apiPost('/logout', undefined, { skipAuth: true });
  } finally {
    clearTokens();
  }
}

export async function refreshToken(refresh_token?: string): Promise<{ token: string; refresh_token: string }> {
  // Web callers should omit the argument so the backend reads the HttpOnly cookie.
  // The optional body is retained only for existing non-browser callers.
  return apiPost<{ token: string; refresh_token: string }>(
    '/auth/refresh',
    refresh_token ? { refresh_token } : {},
    { skipAuth: true },
  );
}

export interface SessionResponse {
  user: UserInfo;
  demo_mode: boolean;
}

export async function getSession(): Promise<SessionResponse> {
  return apiGet<SessionResponse>('/session');
}

export async function register(data: {
  email: string;
  password: string;
  name: string;
  phone?: string;
  national_id?: string;
  role?: string;
}): Promise<{ message: string; user: UserInfo }> {
  return apiPost('/register', data, { skipAuth: true });
}

export async function forgotPassword(email: string): Promise<{ message: string }> {
  return apiPost<{ message: string }>('/auth/forgot-password', { email }, { skipAuth: true });
}

export async function resetPassword(token: string, new_password: string): Promise<{ message: string }> {
  return apiPost<{ message: string }>('/auth/reset-password', { token, new_password }, { skipAuth: true });
}

export interface AuthState {
  isAuthenticated: boolean;
  user: UserInfo | null;
}
