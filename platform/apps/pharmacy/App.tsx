import React, { useState, useEffect } from 'react'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Inventory from './pages/Inventory'
import Dispensing from './pages/Dispensing'
import ControlledDrugs from './pages/ControlledDrugs'
import Interactions from './pages/Interactions'
import Prescriptions from './pages/Prescriptions'
import BarcodeScanning from './pages/BarcodeScanning'
import Ordering from './pages/Ordering'
import StockManagement from './pages/StockManagement'
import ExpiryTracking from './pages/ExpiryTracking'
import Returns from './pages/Returns'
import Reports from './pages/Reports'
import PharmaceuticalCare from './pages/PharmaceuticalCare'
import OfflineMode from './pages/OfflineMode'
import Settings from './pages/Settings'
import { apiRequest } from './services/api'

type Page =
  | 'dashboard'
  | 'inventory'
  | 'dispensing'
  | 'controlled-drugs'
  | 'interactions'
  | 'prescriptions'
  | 'barcode'
  | 'ordering'
  | 'stock'
  | 'expiry'
  | 'returns'
  | 'reports'
  | 'care'
  | 'offline'
  | 'settings'

const navItems: {
  page: Page
  label: string
  icon: string
  badge?: number
}[] = [
  { page: 'dashboard', label: 'لوحة التحكم', icon: '📊' },
  { page: 'dispensing', label: 'صرف الأدوية', icon: '💊', badge: 12 },
  { page: 'prescriptions', label: 'الوصفات الطبية', icon: '📋', badge: 8 },
  { page: 'inventory', label: 'المخزون', icon: '📦' },
  { page: 'ordering', label: 'طلب توريد', icon: '🚚' },
  { page: 'stock', label: 'إدارة المخزون', icon: '📊' },
  { page: 'controlled-drugs', label: 'الأدوية المخدرة', icon: '🔒' },
  { page: 'interactions', label: 'التفاعلات', icon: '🔬' },
  { page: 'expiry', label: 'تواريخ الانتهاء', icon: '⏰' },
  { page: 'barcode', label: 'مسح باركود', icon: '📷' },
  { page: 'returns', label: 'مرتجعات وتوالف', icon: '↩️' },
  { page: 'reports', label: 'التقارير', icon: '📈' },
  { page: 'care', label: 'الرعاية الصيدلانية', icon: '🩺' },
  { page: 'offline', label: 'وضع عدم الاتصال', icon: '📵' },
  { page: 'settings', label: 'الإعدادات', icon: '⚙️' },
]

const pageComponents: Record<Page, React.FC> = {
  dashboard: Dashboard,
  inventory: Inventory,
  dispensing: Dispensing,
  'controlled-drugs': ControlledDrugs,
  interactions: Interactions,
  prescriptions: Prescriptions,
  barcode: BarcodeScanning,
  ordering: Ordering,
  stock: StockManagement,
  expiry: ExpiryTracking,
  returns: Returns,
  reports: Reports,
  care: PharmaceuticalCare,
  offline: OfflineMode,
  settings: Settings,
}

const pageLabels: Record<Page, string> = {
  dashboard: 'لوحة التحكم',
  inventory: 'المخزون',
  dispensing: 'صرف الأدوية',
  'controlled-drugs': 'الأدوية المخدرة',
  interactions: 'التفاعلات الدوائية',
  prescriptions: 'الوصفات الطبية',
  barcode: 'مسح الباركود',
  ordering: 'طلب التوريد',
  stock: 'إدارة المخزون',
  expiry: 'تواريخ الانتهاء',
  returns: 'المرتجعات والتوالف',
  reports: 'التقارير',
  care: 'الرعاية الصيدلانية',
  offline: 'وضع عدم الاتصال',
  settings: 'الإعدادات',
}

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [authLoading, setAuthLoading] = useState(true)
  const [currentPage, setCurrentPage] = useState<Page>('dashboard')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [globalSearch, setGlobalSearch] = useState('')

  function handleLogin() {
    setIsAuthenticated(true)
    setCurrentPage('dashboard')
  }

  function handleLogout() {
    void apiRequest('/auth/logout', { method: 'POST' }).catch(() => undefined)
    setIsAuthenticated(false)
  }

  function navigate(page: Page) {
    setCurrentPage(page)
    setSidebarOpen(false)
  }

  useEffect(() => {
    let active = true
    apiRequest('/auth/session')
      .then(() => { if (active) setIsAuthenticated(true) })
      .catch(() => { if (active) setIsAuthenticated(false) })
      .finally(() => { if (active) setAuthLoading(false) })
    return () => { active = false }
  }, [])

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') setSidebarOpen(false)
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  if (authLoading) {
    return <div style={{ padding: '2rem', textAlign: 'center' }}>جارٍ التحقق من الجلسة…</div>
  }

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />
  }

  const PageComponent = pageComponents[currentPage]

  return (
    <div className="layout">
      <aside
        className={`sidebar ${sidebarOpen ? 'open' : ''}`}
        role="navigation"
        aria-label="القائمة الرئيسية"
      >
        <div className="sidebar-logo">
          <div
            style={{
              width: 36,
              height: 36,
              background: 'var(--accent-primary)',
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 800,
              color: 'white',
              fontSize: '1rem',
              flexShrink: 0,
            }}
          >
            G
          </div>
          <div>
            <h1 style={{ fontSize: '1rem' }}>صيدلية جلا</h1>
            <span style={{ fontSize: '0.65rem' }}>GULA Pharmacy v2.1.0</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <button
              key={item.page}
              className={currentPage === item.page ? 'active' : ''}
              onClick={() => navigate(item.page)}
              aria-current={currentPage === item.page ? 'page' : undefined}
              aria-label={item.label}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
              {item.badge && (
                <span className="nav-badge" aria-label={`${item.badge} جديد`}>
                  {item.badge}
                </span>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <button
            className="btn btn-ghost"
            style={{
              width: '100%',
              justifyContent: 'flex-start',
              color: 'var(--accent-danger)',
            }}
            onClick={handleLogout}
            aria-label="تسجيل الخروج"
          >
            🚪 تسجيل الخروج
          </button>
        </div>
      </aside>

      <main className="main-content" role="main">
        <header className="header" role="banner">
          <div className="header-left">
            <button
              className="btn btn-ghost btn-icon mobile-menu-btn"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              aria-label="فتح القائمة"
              style={{ display: 'none' }}
            >
              ☰
            </button>
            <h2 style={{ fontSize: '1.125rem', fontWeight: 700 }}>
              {pageLabels[currentPage]}
            </h2>
          </div>
          <div className="header-right">
            <div className="header-search">
              <span className="search-icon">🔍</span>
              <input
                type="text"
                placeholder="بحث سريع..."
                value={globalSearch}
                onChange={(e) => setGlobalSearch(e.target.value)}
                aria-label="بحث سريع"
              />
            </div>
            <button
              className="btn btn-ghost btn-icon"
              onClick={() => navigate('offline')}
              aria-label="حالة الاتصال"
              title={navigator.onLine ? 'متصل' : 'غير متصل'}
            >
              {navigator.onLine ? '🟢' : '🟡'}
            </button>
            <button
              className="btn btn-ghost btn-icon"
              onClick={() => navigate('settings')}
              aria-label="الإعدادات"
            >
              ⚙️
            </button>
          </div>
        </header>

        <div className="page-content">
          <PageComponent />
        </div>
      </main>
    </div>
  )
}
