import React, { useState } from 'react'
import { apiPost } from '../services/api'

interface LoginProps {
  onLogin: () => void
}

export default function Login({ onLogin }: LoginProps) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')

    if (!username.trim() || !password.trim()) {
      setError('يرجى إدخال اسم المستخدم وكلمة المرور')
      return
    }

    setLoading(true)
    try {
      await apiPost('/auth/login', { username, password })
      onLogin()
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'فشل تسجيل الدخول',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div
        className="login-card fade-in"
        role="form"
        aria-label="نموذج تسجيل الدخول"
      >
        <div className="login-logo">
          <div
            style={{
              width: 64,
              height: 64,
              background: 'var(--accent-primary)',
              borderRadius: 'var(--radius-xl)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1rem',
              fontSize: '1.75rem',
              fontWeight: 800,
              color: 'white',
            }}
          >
            G
          </div>
          <h1>صيدلية جلا</h1>
          <p>GULA Pharmacy - نظام إدارة الصيدليات</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="login-username">
              اسم المستخدم
            </label>
            <input
              id="login-username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="أدخل اسم المستخدم"
              autoFocus
              autoComplete="username"
              disabled={loading}
              aria-required="true"
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="login-password">
              كلمة المرور
            </label>
            <div style={{ position: 'relative' }}>
              <input
                id="login-password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="أدخل كلمة المرور"
                autoComplete="current-password"
                disabled={loading}
                aria-required="true"
              />
              <button
                type="button"
                style={{
                  position: 'absolute',
                  left: '0.5rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  color: 'var(--text-muted)',
                  fontSize: '0.8rem',
                  padding: '0.25rem',
                }}
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? 'إخفاء كلمة المرور' : 'إظهار كلمة المرور'}
                tabIndex={-1}
              >
                {showPassword ? '🫣' : '👁️'}
              </button>
            </div>
          </div>

          {error && (
            <div
              className="alert alert-danger"
              role="alert"
              style={{ marginBottom: '1rem' }}
            >
              ⚠️ {error}
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary btn-lg"
            style={{ width: '100%', justifyContent: 'center' }}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner" />
                جاري تسجيل الدخول...
              </>
            ) : (
              'تسجيل الدخول'
            )}
          </button>
        </form>

        <div className="login-footer">
          <p>© {new Date().getFullYear()} GULA Platform v2.1.0</p>
          <p style={{ fontSize: '0.75rem', marginTop: '0.25rem' }}>
            جميع الحقوق محفوظة
          </p>
        </div>
      </div>
    </div>
  )
}
