const API_BASE = '/api/v1';

let authToken: string | null = localStorage.getItem('gula-nurse-token');

export function setToken(token: string | null) {
  authToken = token;
  if (token) {
    localStorage.setItem('gula-nurse-token', token);
  } else {
    localStorage.removeItem('gula-nurse-token');
  }
}

export function getToken(): string | null {
  return authToken;
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: response.statusText }));
    throw new Error(error.message || `HTTP ${response.status}`);
  }

  return response.json();
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
