const API_BASE = import.meta.env.VITE_API_URL || '/api'

interface RequestConfig {
  method?: string
  headers?: Record<string, string>
  body?: unknown
  params?: Record<string, string | number | boolean | undefined>
  signal?: AbortSignal
}

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public details?: unknown
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

class ApiClient {
  private token: string | null = null

  constructor(private baseUrl: string) {
    this.token = typeof window !== 'undefined'
      ? localStorage.getItem('gula_radiology_token')
      : null
  }

  setToken(token: string | null) {
    this.token = token
    if (token) {
      localStorage.setItem('gula_radiology_token', token)
    } else {
      localStorage.removeItem('gula_radiology_token')
    }
  }

  getToken(): string | null {
    return this.token
  }

  private buildUrl(path: string, params?: Record<string, string | number | boolean | undefined>): string {
    const url = new URL(`${this.baseUrl}${path}`, window.location.origin)
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          url.searchParams.set(key, String(value))
        }
      })
    }
    return url.toString()
  }

  async request<T>(path: string, config: RequestConfig = {}): Promise<T> {
    const { method = 'GET', headers = {}, body, params, signal } = config

    const requestHeaders: Record<string, string> = {
      'Accept': 'application/json',
      ...headers
    }

    if (this.token) {
      requestHeaders['Authorization'] = `Bearer ${this.token}`
    }

    if (body && !(body instanceof FormData)) {
      requestHeaders['Content-Type'] = 'application/json'
    }

    const response = await fetch(this.buildUrl(path, params), {
      method,
      headers: requestHeaders,
      body: body instanceof FormData ? body as FormData : body ? JSON.stringify(body) : undefined,
      signal
    })

    if (!response.ok) {
      let errorDetails: unknown
      try {
        errorDetails = await response.json()
      } catch {
        errorDetails = await response.text()
      }
      throw new ApiError(
        response.status,
        (errorDetails as Record<string, unknown>)?.message as string || response.statusText,
        errorDetails
      )
    }

    if (response.status === 204) {
      return undefined as T
    }

    return response.json()
  }

  get<T>(path: string, params?: Record<string, string | number | boolean | undefined>, signal?: AbortSignal): Promise<T> {
    return this.request<T>(path, { method: 'GET', params, signal })
  }

  post<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, { method: 'POST', body })
  }

  put<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, { method: 'PUT', body })
  }

  patch<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, { method: 'PATCH', body })
  }

  delete<T>(path: string): Promise<T> {
    return this.request<T>(path, { method: 'DELETE' })
  }

  upload<T>(path: string, formData: FormData): Promise<T> {
    return this.request<T>(path, { method: 'POST', body: formData })
  }
}

export const api = new ApiClient(API_BASE)
export { ApiError }
export type { RequestConfig }

export type PaginatedResponse<T> = {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export type ApiResponse<T> = {
  data: T
  message?: string
  success: boolean
}
