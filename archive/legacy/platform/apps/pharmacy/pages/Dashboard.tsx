import React, { useState, useEffect } from 'react'
import { getInventory, getStockAlerts } from '../services/inventory'
import { getDispensingHistory } from '../services/dispensing'
import StockIndicator from '../components/StockIndicator'
import type { InventoryItem, StockAlert } from '../services/inventory'
import type { DispensingRecord } from '../services/dispensing'

const quickActions = [
  { label: 'صرف وصفة', icon: '💊', path: '/pharmacy/dispensing', color: '#3b82f6' },
  { label: 'مسح باركود', icon: '📷', path: '/pharmacy/barcode', color: '#22c55e' },
  { label: 'طلب توريد', icon: '📦', path: '/pharmacy/ordering', color: '#f59e0b' },
  { label: 'تدقيق مخزون', icon: '📋', path: '/pharmacy/inventory', color: '#8b5cf6' },
]

export default function Dashboard() {
  const [alerts, setAlerts] = useState<StockAlert[]>([])
  const [lowStockCount, setLowStockCount] = useState(0)
  const [expiringCount, setExpiringCount] = useState(0)
  const [dispensedToday, setDispensedToday] = useState(0)
  const [totalItems, setTotalItems] = useState(0)
  const [recentDispenses, setRecentDispenses] = useState<DispensingRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [currentTime, setCurrentTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 60000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    try {
      const [invData, alertData, dispData] = await Promise.all([
        getInventory({ page: 1, page_size: 1 }),
        getStockAlerts(),
        getDispensingHistory({
          date_from: new Date().toISOString().split('T')[0],
          page_size: 5,
        }),
      ])
      setTotalItems(invData.total)
      setAlerts(alertData.alerts || [])
      setLowStockCount(
        (alertData.alerts || []).filter((a) => a.alert_type === 'low_stock').length,
      )
      setExpiringCount(
        (alertData.alerts || []).filter(
          (a) => a.alert_type === 'expiring' || a.alert_type === 'expired',
        ).length,
      )
      setDispensedToday(dispData.total || 0)
      setRecentDispenses((dispData.records || []).slice(0, 5))
    } catch (err) {
      console.error('Failed to load dashboard data', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">لوحة التحكم</h1>
          <p className="page-subtitle">
            {currentTime.toLocaleDateString('ar-IQ', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-primary" onClick={loadData}>
            🔄 تحديث
          </button>
        </div>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-icon" style={{ background: 'rgba(59,130,246,0.15)', color: '#3b82f6' }}>
            📦
          </div>
          <div className="kpi-value">{loading ? '-' : totalItems}</div>
          <div className="kpi-label">إجمالي الأصناف</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{ background: 'rgba(239,68,68,0.15)', color: '#ef4444' }}>
            ⚠️
          </div>
          <div className="kpi-value">{loading ? '-' : lowStockCount}</div>
          <div className="kpi-label">مخزون منخفض</div>
          {lowStockCount > 0 && (
            <div className="kpi-change negative">يحتاج إلى طلب عاجل</div>
          )}
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{ background: 'rgba(245,158,11,0.15)', color: '#f59e0b' }}>
            ⏰
          </div>
          <div className="kpi-value">{loading ? '-' : expiringCount}</div>
          <div className="kpi-label">منتهٍ أو وشيك الانتهاء</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{ background: 'rgba(34,197,94,0.15)', color: '#22c55e' }}>
            💊
          </div>
          <div className="kpi-value">{loading ? '-' : dispensedToday}</div>
          <div className="kpi-label">تم صرفها اليوم</div>
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        {quickActions.map((action) => (
          <a
            key={action.path}
            href={action.path}
            className="card"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '1rem',
              textDecoration: 'none',
              transition: 'transform 0.15s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)'
            }}
          >
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: 'var(--radius-lg)',
                background: `${action.color}20`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.5rem',
              }}
            >
              {action.icon}
            </div>
            <div>
              <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                {action.label}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                انقر للدخول
              </div>
            </div>
          </a>
        ))}
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">تنبيهات المخزون</h3>
            <span className="badge badge-danger">{alerts.length}</span>
          </div>
          {alerts.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">✅</div>
              <p>لا توجد تنبيهات</p>
            </div>
          ) : (
            <div>
              {alerts.slice(0, 5).map((alert) => (
                <div
                  key={alert.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    padding: '0.625rem 0',
                    borderBottom: '1px solid var(--border-color)',
                  }}
                >
                  <span
                    className={`badge ${
                      alert.alert_type === 'expired'
                        ? 'badge-danger'
                        : alert.alert_type === 'expiring'
                          ? 'badge-warning'
                          : 'badge-danger'
                    }`}
                  >
                    {alert.alert_type === 'low_stock'
                      ? 'مخزون منخفض'
                      : alert.alert_type === 'expiring'
                        ? 'ينتهي قريباً'
                        : alert.alert_type === 'expired'
                          ? 'منتهي'
                          : 'زيادة مخزون'}
                  </span>
                  <span style={{ flex: 1, fontSize: '0.875rem' }}>
                    {alert.drug_name}
                  </span>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    {alert.current_quantity} / {alert.threshold}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">آخر عمليات الصرف</h3>
            <span className="badge badge-info">{dispensedToday}</span>
          </div>
          {recentDispenses.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">💊</div>
              <p>لا توجد عمليات صرف اليوم</p>
            </div>
          ) : (
            <div>
              {recentDispenses.map((disp) => (
                <div
                  key={disp.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    padding: '0.5rem 0',
                    borderBottom: '1px solid var(--border-color)',
                  }}
                >
                  <span style={{ fontSize: '1.25rem' }}>💊</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>
                      {disp.patient_name}
                    </div>
                    <div
                      style={{
                        fontSize: '0.75rem',
                        color: 'var(--text-secondary)',
                      }}
                    >
                      {disp.items.length} أصناف -{' '}
                      {new Date(disp.dispensed_at).toLocaleTimeString('ar-IQ')}
                    </div>
                  </div>
                  <span
                    className={`badge ${
                      disp.status === 'completed'
                        ? 'badge-success'
                        : disp.status === 'pending'
                          ? 'badge-warning'
                          : 'badge-info'
                    }`}
                  >
                    {disp.status === 'completed'
                      ? 'مكتمل'
                      : disp.status === 'pending'
                        ? 'قيد الانتظار'
                        : disp.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
