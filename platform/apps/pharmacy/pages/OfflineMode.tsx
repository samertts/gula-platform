import React, { useState, useEffect } from 'react'
import { getPendingDispenses, getSyncLogs, clearSyncedDispenses, clearCache, getOfflineStats, cacheInventory, cachePatients } from '../services/offline'
import { getInventory } from '../services/inventory'

export default function OfflineMode() {
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  const [stats, setStats] = useState({ pending_count: 0, synced_count: 0, cached_inventory: 0, sync_log_count: 0 })
  const [pendingDispenses, setPendingDispenses] = useState<Record<string, unknown>[]>([])
  const [syncLogs, setSyncLogs] = useState<Record<string, unknown>[]>([])
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState<{ type: string; text: string } | null>(null)

  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    loadData()
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  async function loadData() {
    setLoading(true)
    try {
      const [s, p, logs] = await Promise.all([
        getOfflineStats(),
        getPendingDispenses(),
        getSyncLogs(),
      ])
      setStats(s)
      setPendingDispenses(p)
      setSyncLogs(logs)
    } catch {
      // handle error
    } finally {
      setLoading(false)
    }
  }

  async function handleCacheInventory() {
    try {
      const data = await getInventory({ page_size: 200 })
      await cacheInventory(data.items as unknown as Record<string, unknown>[])
      setMessage({ type: 'success', text: 'تم تخزين المخزون محلياً' })
      loadData()
    } catch {
      setMessage({ type: 'error', text: 'فشل تخزين المخزون' })
    }
  }

  async function handleSync() {
    setMessage({ type: 'info', text: 'جاري المزامنة...' })
    try {
      await clearSyncedDispenses()
      setMessage({ type: 'success', text: 'تمت المزامنة بنجاح' })
      loadData()
    } catch {
      setMessage({ type: 'error', text: 'فشلت المزامنة' })
    }
  }

  async function handleClearCache() {
    if (window.confirm('هل أنت متأكد من مسح جميع البيانات المخزنة محلياً؟')) {
      try {
        await clearCache()
        setMessage({ type: 'success', text: 'تم مسح الذاكرة المؤقتة' })
        loadData()
      } catch {
        setMessage({ type: 'error', text: 'فشل مسح الذاكرة المؤقتة' })
      }
    }
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">وضع عدم الاتصال</h1>
          <p className="page-subtitle">إدارة البيانات المحلية والمزامنة</p>
        </div>
        <button className="btn btn-primary" onClick={loadData}>
          🔄 تحديث
        </button>
      </div>

      <div className="alert alert-info" role="alert">
        ℹ️ يتيح وضع عدم الاتصال استمرار العمل عند انقطاع الاتصال بالخادم.
        سيتم حفظ عمليات الصرف محلياً ومزامنتها تلقائياً عند استعادة الاتصال.
      </div>

      {!isOnline && (
        <div className="offline-banner">
          📵 أنت حالياً في وضع عدم الاتصال
        </div>
      )}

      {message && (
        <div className={`alert alert-${message.type}`} role="alert" style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>{message.text}</span>
          <button className="btn btn-ghost btn-sm" onClick={() => setMessage(null)}>✕</button>
        </div>
      )}

      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-icon" style={{ background: 'rgba(239,68,68,0.15)', color: '#ef4444' }}>
            📵
          </div>
          <div className="kpi-value">
            <span className={`status-dot ${isOnline ? 'online' : 'offline'}`} style={{ display: 'inline-block', marginLeft: '0.5rem' }} />
            {isOnline ? 'متصل' : 'غير متصل'}
          </div>
          <div className="kpi-label">حالة الاتصال</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{ background: 'rgba(245,158,11,0.15)', color: '#f59e0b' }}>
            ⏳
          </div>
          <div className="kpi-value">{stats.pending_count}</div>
          <div className="kpi-label">معاملات معلقة</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{ background: 'rgba(34,197,94,0.15)', color: '#22c55e' }}>
            ✅
          </div>
          <div className="kpi-value">{stats.synced_count}</div>
          <div className="kpi-label">تمت المزامنة</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{ background: 'rgba(59,130,246,0.15)', color: '#3b82f6' }}>
            📦
          </div>
          <div className="kpi-value">{stats.cached_inventory}</div>
          <div className="kpi-label">مخزون مخبأ</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">البيانات المحلية</h3>
            <span className="badge badge-info">{stats.cached_inventory + stats.pending_count + stats.synced_count} عنصر</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0.75rem', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
              <span>المخزون المخبأ</span>
              <span style={{ fontWeight: 700 }}>{stats.cached_inventory} صنف</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0.75rem', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
              <span>معاملات الصرف المعلقة</span>
              <span style={{ fontWeight: 700 }}>{stats.pending_count}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0.75rem', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
              <span>سجل المزامنة</span>
              <span style={{ fontWeight: 700 }}>{stats.sync_log_count} إدخال</span>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <button className="btn btn-primary" onClick={handleCacheInventory} disabled={!isOnline}>
              📥 تخزين المخزون محلياً
            </button>
            <button className="btn btn-success" onClick={handleSync} disabled={!isOnline || stats.pending_count === 0}>
              🔄 مزامنة الآن
            </button>
            <button className="btn btn-danger" onClick={handleClearCache}>
              🗑️ مسح الذاكرة المؤقتة
            </button>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">المعاملات المعلقة</h3>
            <span className="badge badge-info">{pendingDispenses.length}</span>
          </div>
          {pendingDispenses.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">✅</div>
              <p>لا توجد معاملات معلقة</p>
            </div>
          ) : (
            <div>
              {pendingDispenses.slice(0, 10).map((disp, idx) => (
                <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid var(--border-color)', fontSize: '0.85rem' }}>
                  <span>{disp.prescription_id as string || `#${disp.id as number}`}</span>
                  <span className={`badge ${disp.status === 'pending' ? 'badge-warning' : 'badge-success'}`}>
                    {disp.status === 'pending' ? 'قيد الانتظار' : 'متزامن'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="card-title">سجل المزامنة</h3>
          <span className="badge badge-info">{syncLogs.length} إدخال</span>
        </div>
        {syncLogs.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📋</div>
            <p>لا توجد إدخالات في سجل المزامنة</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table role="grid" aria-label="سجل المزامنة">
              <thead>
                <tr>
                  <th>التاريخ</th>
                  <th>الإجراء</th>
                  <th>النوع</th>
                  <th>المعرف</th>
                  <th>الحالة</th>
                  <th>الخطأ</th>
                </tr>
              </thead>
              <tbody>
                {syncLogs.slice(0, 20).map((log, idx) => (
                  <tr key={idx}>
                    <td style={{ fontSize: '0.8rem' }}>{log.created_at as string ? new Date(log.created_at as string).toLocaleString('ar-IQ') : '-'}</td>
                    <td>{log.action as string}</td>
                    <td style={{ fontSize: '0.8rem' }}>{log.entity_type as string}</td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{log.entity_id as string}</td>
                    <td>
                      <span className={`badge ${log.status === 'success' ? 'badge-success' : 'badge-danger'}`}>
                        {log.status === 'success' ? 'نجاح' : 'فشل'}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--accent-danger)' }}>{(log.error as string) || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
