import { ApiClientError, createApiClient } from '../../../ui'

const API_BASE = import.meta.env.VITE_API_URL || '/api/v2'
const backend = createApiClient({
  baseUrl: API_BASE,
  clientName: 'pharmacy-app',
  refreshPath: '/auth/refresh',
})

interface ApiOptions {
  method?: string
  body?: unknown
  headers?: Record<string, string>
  signal?: AbortSignal
}

// Authentication is carried only by server-issued HttpOnly cookies.
export function setToken(_token: string | null) {
  return undefined
}

export function getToken(): string | null {
  return null
}

export async function apiRequest<T = unknown>(
  path: string,
  options: ApiOptions = {},
): Promise<T> {
  const { method = 'GET', body, headers = {}, signal } = options
  try {
    return await backend.request<T>(path, {
      method,
      body,
      headers,
      signal,
    })
  } catch (error) {
    if (error instanceof ApiClientError && error.status === 401) {
      window.location.assign('/pharmacy/login?reason=session-expired')
    }
    throw error instanceof Error ? error : new Error('تعذر الاتصال بالخادم')
  }
}

export function apiGet<T = unknown>(path: string, signal?: AbortSignal) {
  return apiRequest<T>(path, { signal })
}

export function apiPost<T = unknown>(path: string, body: unknown, signal?: AbortSignal) {
  return apiRequest<T>(path, { method: 'POST', body, signal })
}

export function apiPut<T = unknown>(path: string, body: unknown, signal?: AbortSignal) {
  return apiRequest<T>(path, { method: 'PUT', body, signal })
}

export function apiDelete<T = unknown>(path: string, signal?: AbortSignal) {
  return apiRequest<T>(path, { method: 'DELETE', signal })
}
