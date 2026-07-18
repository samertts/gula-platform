import { useState, useCallback, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, Outlet, useNavigate, useLocation } from 'react-router-dom'
import { useTheme } from './hooks/useTheme'
import { useAuth, type User } from './hooks/useAuth'
import { Login } from '@pages/Login'
import { Dashboard } from '@pages/Dashboard'
import { Orders } from '@pages/Orders'
import { Scheduling } from '@pages/Scheduling'
import { Reports } from '@pages/Reports'
import { DICOMViewerPage } from '@pages/DICOMViewer'
import { Worklist } from '@pages/Worklist'
import { Protocols } from '@pages/Protocols'
import { ImageSharing } from '@pages/ImageSharing'
import { ContrastTracking } from '@pages/ContrastTracking'
import { CriticalFindings } from '@pages/CriticalFindings'
import { Quality } from '@pages/Quality'
import { Admin } from '@pages/Admin'
import { Settings } from '@pages/Settings'

type NavItem = {
  path: string
  label: string
  icon: string
  badge?: number | string
  roles?: string[]
}

const NAV_ITEMS: NavItem[] = [
  { path: '/dashboard', label: 'لوحة التحكم', icon: '📊' },
  { path: '/worklist', label: 'قائمة العمل', icon: '📋', badge: 12 },
  { path: '/orders', label: 'الطلبات', icon: '📝' },
  { path: '/scheduling', label: 'المواعيد', icon: '📅' },
  { path: '/reports', label: 'التقارير', icon: '📄' },
  { path: '/dicom-viewer', label: 'عارض الصور', icon: '🖼️' },
  { path: '/protocols', label: 'البروتوكولات', icon: '📋' },
  { path: '/critical-findings', label: 'نتائج حرجة', icon: '🚨', badge: '!' },
  { path: '/image-sharing', label: 'مشاركة الصور', icon: '🔗' },
  { path: '/contrast-tracking', label: 'تتبع الصبغة', icon: '💉' },
  { path: '/quality', label: 'الجودة', icon: '⭐' },
  { path: '/admin', label: 'الإدارة', icon: '⚙️', roles: ['admin'] },
  { path: '/settings', label: 'الإعدادات', icon: '🔧' }
]

function Sidebar({ collapsed, user, onLogout, onNavigate }: {
  collapsed: boolean
  user: User | null
  onLogout: () => void
  onNavigate: (path: string) => void
}) {
  const location = useLocation()
  const currentPath = location.pathname

  return (
    <aside className={`app-sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div style={{
        height: 'var(--header-height)',
        display: 'flex',
        alignItems: 'center',
        padding: collapsed ? '0 12px' : '0 16px',
        borderBottom: '1px solid var(--border-primary)',
        gap: 10
      }}>
        <div style={{
          width: 36, height: 36, borderRadius: 10,
          backgroundColor: 'var(--accent-primary)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'white', fontWeight: 700, fontSize: '1rem', flexShrink: 0
        }}>
          G
        </div>
        {!collapsed && (
          <div style={{ overflow: 'hidden' }}>
            <div style={{ fontSize: '0.95rem', fontWeight: 700, whiteSpace: 'nowrap' }}>GULA Radiology</div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-tertiary)', whiteSpace: 'nowrap' }}>RIS v2.1.0</div>
          </div>
        )}
      </div>

      <nav style={{ flex: 1, overflowY: 'auto', padding: '8px 0' }}>
        {NAV_ITEMS.map(item => {
          if (item.roles && user && !item.roles.includes(user.role)) return null
          const isActive = currentPath.startsWith(item.path)
          return (
            <button
              key={item.path}
              onClick={() => onNavigate(item.path)}
              style={{
                display: 'flex', alignItems: 'center', gap: 10, width: '100%',
                padding: collapsed ? '10px 14px' : '10px 16px',
                border: 'none',
                background: isActive ? 'var(--accent-primary-light)' : 'transparent',
                color: isActive ? 'var(--accent-primary)' : 'var(--text-secondary)',
                cursor: 'pointer', fontSize: '0.85rem',
                fontWeight: isActive ? 600 : 400,
                borderInlineStart: isActive ? '3px solid var(--accent-primary)' : '3px solid transparent'
              }}
              onMouseEnter={e => { if (!isActive) e.currentTarget.style.backgroundColor = 'var(--bg-hover)' }}
              onMouseLeave={e => { if (!isActive) e.currentTarget.style.backgroundColor = 'transparent' }}
              title={collapsed ? item.label : undefined}
            >
              <span style={{ fontSize: '1.1rem', flexShrink: 0 }}>{item.icon}</span>
              {!collapsed && (
                <>
                  <span style={{ flex: 1, textAlign: 'start' }}>{item.label}</span>
                  {item.badge && (
                    <span className="badge badge-danger" style={{ fontSize: '0.65rem', padding: '1px 6px' }}>
                      {item.badge}
                    </span>
                  )}
                </>
              )}
            </button>
          )
        })}
      </nav>

      {!collapsed && user && (
        <div style={{
          padding: '12px 16px', borderTop: '1px solid var(--border-primary)',
          display: 'flex', alignItems: 'center', gap: 10
        }}>
          <div style={{
            width: 32, height: 32, borderRadius: '50%', backgroundColor: 'var(--accent-primary)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'white', fontSize: '0.8rem', fontWeight: 700, flexShrink: 0
          }}>
            {user.full_name.charAt(0)}
          </div>
          <div style={{ flex: 1, overflow: 'hidden' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {user.full_name}
            </div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-tertiary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {user.role === 'radiologist' ? 'طبيب أشعة' :
               user.role === 'technician' ? 'فني أشعة' :
               user.role === 'admin' ? 'مدير نظام' : user.role}
            </div>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={onLogout} title="تسجيل خروج">🚪</button>
        </div>
      )}
    </aside>
  )
}

function AppLayout() {
  const { isDark, toggleTheme, toggleDir, dir } = useTheme()
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [headerTitle, setHeaderTitle] = useState('')

  useEffect(() => {
    const item = NAV_ITEMS.find(n => location.pathname.startsWith(n.path))
    setHeaderTitle(item?.label || 'GULA Radiology')
  }, [location.pathname])

  const handleLogout = useCallback(() => {
    logout()
    navigate('/login')
  }, [logout, navigate])

  return (
    <div className="app-layout">
      <Sidebar
        collapsed={sidebarCollapsed}
        user={user}
        onLogout={handleLogout}
        onNavigate={navigate}
      />
      <div className="app-main">
        <header className="app-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button className="btn btn-ghost btn-sm" onClick={() => setSidebarCollapsed(!sidebarCollapsed)}>
              {sidebarCollapsed ? '☰' : '✕'}
            </button>
            <h2 style={{ fontSize: '1rem', fontWeight: 600 }}>{headerTitle}</h2>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <button className="btn btn-ghost btn-sm" onClick={toggleTheme} title={isDark ? 'الوضع النهاري' : 'الوضع الليلي'}>
              {isDark ? '☀️' : '🌙'}
            </button>
            <button className="btn btn-ghost btn-sm" onClick={toggleDir} title={dir === 'rtl' ? 'English' : 'العربية'}>
              {dir === 'rtl' ? 'EN' : 'AR'}
            </button>
          </div>
        </header>
        <main className="app-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

function ProtectedRoute() {
  const { user, loading } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (!loading && !user) {
      navigate('/login', { replace: true })
    }
  }, [user, loading, navigate])

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', backgroundColor: 'var(--bg-primary)' }}>
        <div style={{ textAlign: 'center' }}>
          <div className="skeleton" style={{ width: 48, height: 48, borderRadius: '50%', margin: '0 auto 16px' }} />
          <div className="skeleton" style={{ width: 200, height: 16, margin: '0 auto' }} />
        </div>
      </div>
    )
  }

  if (!user) return null
  return <AppLayout />
}

function LoginPage() {
  const { login, error, loading } = useAuth()
  const navigate = useNavigate()

  const handleLogin = useCallback(async (username: string, password: string) => {
    try {
      await login(username, password)
      navigate('/dashboard', { replace: true })
    } catch {
      /* error handled by hook */
    }
  }, [login, navigate])

  return <Login onLogin={handleLogin} error={error} loading={loading} />
}

export default function App() {
  useTheme()

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/worklist" element={<Worklist />} />
          <Route path="/orders" element={<Orders />} />
          <Route path="/scheduling" element={<Scheduling />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/dicom-viewer" element={<DICOMViewerPage />} />
          <Route path="/protocols" element={<Protocols />} />
          <Route path="/critical-findings" element={<CriticalFindings />} />
          <Route path="/image-sharing" element={<ImageSharing />} />
          <Route path="/contrast-tracking" element={<ContrastTracking />} />
          <Route path="/quality" element={<Quality />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
