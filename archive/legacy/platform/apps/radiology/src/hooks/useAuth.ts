import { useState, useEffect, useCallback } from 'react'
import { api } from '@services/api'

export type User = {
  id: string
  username: string
  full_name: string
  email: string
  role: 'radiologist' | 'technician' | 'admin' | 'referring_physician' | 'scheduler' | 'viewer'
  lab_id: string
  specialization?: string
  license_number?: string
  signature?: string
}

type AuthState = {
  user: User | null
  loading: boolean
  error: string | null
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({
    user: null,
    loading: true,
    error: null
  })

  const fetchUser = useCallback(async () => {
    const token = api.getToken()
    if (!token) {
      setState({ user: null, loading: false, error: null })
      return
    }
    try {
      const user = await api.get<User>('/auth/me')
      setState({ user, loading: false, error: null })
    } catch {
      api.setToken(null)
      setState({ user: null, loading: false, error: null })
    }
  }, [])

  useEffect(() => {
    fetchUser()
  }, [fetchUser])

  const login = useCallback(async (username: string, password: string) => {
    setState(prev => ({ ...prev, loading: true, error: null }))
    try {
      const { access_token } = await api.post<{ access_token: string }>('/auth/login', { username, password })
      api.setToken(access_token)
      const user = await api.get<User>('/auth/me')
      setState({ user, loading: false, error: null })
      return user
    } catch (err) {
      const message = err instanceof Error ? err.message : 'فشل تسجيل الدخول'
      setState({ user: null, loading: false, error: message })
      throw err
    }
  }, [])

  const logout = useCallback(() => {
    api.setToken(null)
    setState({ user: null, loading: false, error: null })
  }, [])

  const hasRole = useCallback((...roles: string[]) => {
    return state.user ? roles.includes(state.user.role) : false
  }, [state.user])

  return { ...state, login, logout, fetchUser, hasRole }
}
