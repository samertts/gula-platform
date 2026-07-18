import { useState, useCallback } from 'react'

type LoginProps = {
  onLogin: (username: string, password: string) => Promise<void>
  error?: string | null
  loading?: boolean
}

export function Login({ onLogin, error, loading = false }: LoginProps) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    if (!username || !password) return
    await onLogin(username, password)
  }, [username, password, onLogin])

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: 'var(--bg-primary)',
      backgroundImage: 'radial-gradient(ellipse at top, var(--accent-primary-light) 0%, transparent 50%)',
      padding: '1rem'
    }}>
      <div style={{
        width: '100%',
        maxWidth: 420,
        backgroundColor: 'var(--bg-card)',
        border: '1px solid var(--border-primary)',
        borderRadius: 16,
        padding: '2.5rem 2rem',
        boxShadow: 'var(--shadow-xl)'
      }}>
        {/* Logo & Title */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{
            width: 72,
            height: 72,
            borderRadius: 16,
            backgroundColor: 'var(--accent-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1rem',
            fontSize: '2rem',
            color: 'white',
            fontWeight: 700
          }}>
            G
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
            GULA Radiology
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-tertiary)' }}>
            نظام معلومات الأشعة المتكامل
          </p>
        </div>

        {/* Error */}
        {error && (
          <div style={{
            padding: '12px 16px',
            backgroundColor: 'rgba(239,68,68,0.1)',
            border: '1px solid var(--border-danger)',
            borderRadius: 8,
            color: 'var(--text-danger)',
            fontSize: '0.875rem',
            marginBottom: '1rem',
            textAlign: 'center'
          }}>
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="input-group">
            <label className="input-label" htmlFor="username">اسم المستخدم</label>
            <input
              id="username"
              className="input"
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="أدخل اسم المستخدم"
              autoComplete="username"
              autoFocus
              disabled={loading}
              required
              dir="auto"
            />
          </div>

          <div className="input-group">
            <label className="input-label" htmlFor="password">كلمة المرور</label>
            <div style={{ position: 'relative' }}>
              <input
                id="password"
                className="input"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="أدخل كلمة المرور"
                autoComplete="current-password"
                disabled={loading}
                required
                style={{ paddingInlineEnd: '2.5rem' }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  insetInlineEnd: 8,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: 'var(--text-tertiary)',
                  fontSize: '0.8rem',
                  padding: 4
                }}
                tabIndex={-1}
              >
                {showPassword ? '🙈' : '👁'}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-lg"
            disabled={loading || !username || !password}
            style={{ width: '100%', justifyContent: 'center', marginTop: 8 }}
          >
            {loading ? (
              <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span className="skeleton" style={{ width: 16, height: 16, borderRadius: '50%', display: 'inline-block', backgroundColor: 'rgba(255,255,255,0.3)' }} />
                جاري تسجيل الدخول...
              </span>
            ) : 'تسجيل الدخول'}
          </button>
        </form>

        {/* Footer */}
        <div style={{
          textAlign: 'center',
          marginTop: '2rem',
          fontSize: '0.75rem',
          color: 'var(--text-tertiary)'
        }}>
          <p>GULA Platform v2.1.0 — نظام معلومات الأشعة</p>
          <p style={{ marginTop: 4 }}>© {new Date().getFullYear()} GULA. جميع الحقوق محفوظة</p>
        </div>
      </div>
    </div>
  )
}
