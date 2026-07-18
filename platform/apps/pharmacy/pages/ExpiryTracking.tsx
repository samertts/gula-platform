import React, { useState, useEffect } from 'react'
import { getInventory } from '../services/inventory'
import type { InventoryItem } from '../services/inventory'

export default function ExpiryTracking() {
  const [items, setItems] = useState<InventoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('all')
  const [search, setSearch] = useState('')

  useEffect(() => { loadData() }, [])

  async function loadData() {
    setLoading(true)
    try {
      const data = await getInventory({ page_size: 200 })
      setItems(data.items || [])
    } catch {
      setItems([])
    } finally {
      setLoading(false)
    }
  }

  const now = new Date()
  const in30Days = new Date(now.getTime() + 30 * 864e5)
  const in90Days = new Date(now.getTime() + 90 * 864e5)

  const expired = items.filter((i) => i.expiry_date && new Date(i.expiry_date) < now)
  const expiringSoon = items.filter(
    (i) => i.expiry_date && new Date(i.expiry_date) >= now && new Date(i.expiry_date) <= in30Days,
  )
  const expiringSoon90 = items.filter(
    (i) => i.expiry_date && new Date(i.expiry_date) > in30Days && new Date(i.expiry_date) <= in90Days,
  )
  const valid = items.filter(
    (i) => !i.expiry_date || new Date(i.expiry_date) > in90Days,
  )

  function getFilteredItems() {
    switch (filter) {
      case 'expired': return expired
      case 'expiring-30': return expiringSoon
      case 'expiring-90': return expiringSoon90
      case 'valid': return valid
      default: return items
    }
  }

  const displayItems = getFilteredItems().filter(
    (i) =>
      i.drug_name.toLowerCase().includes(search.toLowerCase()) ||
      i.batch_number.toLowerCase().includes(search.toLowerCase()),
  )

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">تتبع تواريخ الانتهاء</h1>
          <p className="page-subtitle">مراقبة وإدارة تواريخ صلاحية الأدوية</p>
        </div>
        <button className="btn btn-primary" onClick={loadData}>🔄 تحديث</button>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card" onClick={() => setFilter('expired')} style={{ cursor: 'pointer', border: filter === 'expired' ? '2px solid var(--accent-danger)' : undefined }}>
          <div className="kpi-icon" style={{ background: 'rgba(239,68,68,0.15)', color: '#ef4444' }}>❌</div>
          <div className="kpi-value">{expired.length}</div>
          <div className="kpi-label">منتهي الصلاحية</div>
          {expired.length > 0 && <div className="kpi-change negative">يجب التخلص منها فوراً</div>}
        </div>
        <div className="kpi-card" onClick={() => setFilter('expiring-30')} style={{ cursor: 'pointer', border: filter === 'expiring-30' ? '2px solid var(--accent-warning)' : undefined }}>
          <div className="kpi-icon" style={{ background: 'rgba(245,158,11,0.15)', color: '#f59e0b' }}>⏰</div>
          <div className="kpi-value">{expiringSoon.length}</div>
          <div className="kpi-label">تنتهي خلال 30 يوماً</div>
          {expiringSoon.length > 0 && <div className="kpi-change negative">يحتاج إلى تصريف عاجل</div>}
        </div>
        <div className="kpi-card" onClick={() => setFilter('expiring-90')} style={{ cursor: 'pointer', border: filter === 'expiring-90' ? '2px solid var(--accent-info)' : undefined }}>
          <div className="kpi-icon" style={{ background: 'rgba(56,189,248,0.15)', color: '#38bdf8' }}>📅</div>
          <div className="kpi-value">{expiringSoon90.length}</div>
          <div className="kpi-label">تنتهي خلال 31-90 يوماً</div>
        </div>
        <div className="kpi-card" onClick={() => setFilter('valid')} style={{ cursor: 'pointer', border: filter === 'valid' ? '2px solid var(--accent-success)' : undefined }}>
          <div className="kpi-icon" style={{ background: 'rgba(34,197,94,0.15)', color: '#22c55e' }}>✅</div>
          <div className="kpi-value">{valid.length}</div>
          <div className="kpi-label">صالحة لأكثر من 90 يوماً</div>
        </div>
      </div>

      <div className="toolbar">
        <div className="search-box">
          <span className="search-icon">🔍</span>
          <input type="text" placeholder="بحث باسم الدواء أو رقم الدفعة..." value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <div className="filter-group">
          <select value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="all">الجميع</option>
            <option value="expired">منتهي الصلاحية</option>
            <option value="expiring-30">تنتهي خلال 30 يوماً</option>
            <option value="expiring-90">تنتهي خلال 90 يوماً</option>
            <option value="valid">صالحة</option>
          </select>
        </div>
      </div>

      <div className="card">
        {loading ? (
          <div style={{ textAlign: 'center', padding: '2rem' }}><span className="spinner" /></div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table role="grid" aria-label="تتبع تواريخ الانتهاء">
              <thead>
                <tr>
                  <th>الاسم</th>
                  <th>رقم الدفعة</th>
                  <th>الكمية</th>
                  <th>تاريخ الانتهاء</th>
                  <th>الأيام المتبقية</th>
                  <th>الحالة</th>
                  <th>إجراءات</th>
                </tr>
              </thead>
              <tbody>
                {displayItems.length === 0 ? (
                  <tr><td colSpan={7} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>لا توجد أصناف في هذا التصنيف</td></tr>
                ) : (
                  displayItems.sort((a, b) => {
                    if (!a.expiry_date) return 1
                    if (!b.expiry_date) return -1
                    return new Date(a.expiry_date).getTime() - new Date(b.expiry_date).getTime()
                  }).map((item) => {
                    const expiryDate = item.expiry_date ? new Date(item.expiry_date) : null
                    const daysLeft = expiryDate ? Math.ceil((expiryDate.getTime() - now.getTime()) / 864e5) : null
                    const isExpired = daysLeft !== null && daysLeft <= 0
                    const isCritical = daysLeft !== null && daysLeft > 0 && daysLeft <= 30

                    return (
                      <tr key={item.id} style={{
                        background: isExpired ? 'rgba(239,68,68,0.05)' : isCritical ? 'rgba(245,158,11,0.05)' : undefined,
                      }}>
                        <td>
                          <div style={{ fontWeight: 600 }}>{item.drug_name}</div>
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{item.generic_name}</div>
                        </td>
                        <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{item.batch_number}</td>
                        <td style={{ fontWeight: 700 }}>{item.quantity} {item.unit}</td>
                        <td style={{
                          fontWeight: 700,
                          color: isExpired ? 'var(--accent-danger)' : isCritical ? 'var(--accent-warning)' : undefined,
                        }}>
                          {expiryDate ? expiryDate.toLocaleDateString('ar-IQ') : '-'}
                        </td>
                        <td style={{
                          fontWeight: 700,
                          color: isExpired ? 'var(--accent-danger)' : isCritical ? 'var(--accent-warning)' : 'var(--text-secondary)',
                        }}>
                          {daysLeft !== null ? (isExpired ? `منذ ${Math.abs(daysLeft)} يوم` : `${daysLeft} يوم`) : '-'}
                        </td>
                        <td>
                          <span className={`badge ${isExpired ? 'badge-danger' : isCritical ? 'badge-warning' : 'badge-success'}`}>
                            {isExpired ? 'منتهي' : isCritical ? 'وشيك' : 'صالحة'}
                          </span>
                        </td>
                        <td>
                          <div style={{ display: 'flex', gap: '0.25rem' }}>
                            {isExpired && <button className="btn btn-sm btn-danger">تالف</button>}
                            {isCritical && !isExpired && <button className="btn btn-sm btn-warning">تنبيه</button>}
                            {!isExpired && <button className="btn btn-sm btn-primary">صرف</button>}
                          </div>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
