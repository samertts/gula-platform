const API_BASE = import.meta.env.VITE_API_URL || '/api/v2'

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

  const h: Record<string, string> = {
    Accept: 'application/json',
    ...headers,
  }

  if (body && !(body instanceof FormData)) {
    h['Content-Type'] = 'application/json'
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    credentials: 'include',
    headers: h,
    body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
    signal,
  })

  if (res.status === 401) {
    // The server session is authoritative; redirect without client-side token handling.
    window.location.assign('/pharmacy/login?reason=session-expired')
    throw new Error('Unauthorized')
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `Request failed with ${res.status}`)
  }

  return res.json()
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
