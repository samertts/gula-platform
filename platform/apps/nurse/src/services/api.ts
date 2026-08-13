import { createApiClient } from '@gula/ui-platform';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const backend = createApiClient({
  baseUrl: API_BASE,
  clientName: 'nurse-app',
  refreshPath: '/auth/refresh',
});

// Authentication is carried only by server-issued HttpOnly cookies.
export function setToken(_token: string | null) {
  return undefined;
}

export function getToken(): string | null {
  return null;
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  return backend.request<T>(endpoint, options);
}

export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint),
  post: <T>(endpoint: string, data?: unknown) =>
    request<T>(endpoint, { method: 'POST', body: JSON.stringify(data) }),
  put: <T>(endpoint: string, data?: unknown) =>
    request<T>(endpoint, { method: 'PUT', body: JSON.stringify(data) }),
  patch: <T>(endpoint: string, data?: unknown) =>
    request<T>(endpoint, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: <T>(endpoint: string) =>
    request<T>(endpoint, { method: 'DELETE' }),
};

export async function loginUser(email: string, password: string) {
  const data = await api.post<{ token: string; user: unknown }>('/auth/login', { email, password });
  setToken(data.token);
  return data;
}

export async function logoutUser() {
  try {
    await api.post('/auth/logout');
  } catch { /* ignore */ }
  setToken(null);
}
