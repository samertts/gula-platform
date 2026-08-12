import { ApiClientError as SharedApiClientError, createApiClient } from '@gula/ui-platform'

const API_BASE = import.meta.env.VITE_API_URL || '/api'
const backend = createApiClient({
  baseUrl: API_BASE,
  clientName: 'radiology-app',
  refreshPath: '/auth/refresh',
})

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
  constructor(private baseUrl: string) {}

  // Compatibility methods intentionally do not retain browser credentials.
  setToken(_token: string | null) {
    return undefined
  }

  getToken(): string | null {
    return null
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
    try {
      return await backend.request<T>(path, {
        method,
        headers,
        body,
        query: params,
        signal,
      })
    } catch (error) {
      if (error instanceof SharedApiClientError) {
        throw new ApiError(error.status, error.message, error.contract)
      }
      if (error instanceof ApiError) throw error
      throw new ApiError(0, error instanceof Error ? error.message : 'تعذر الاتصال بالخادم')
    }
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
