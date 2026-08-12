import React, { useState, useEffect } from 'react'
import { getInventory, getMovements, adjustStock } from '../services/inventory'
import InventoryTable from '../components/InventoryTable'
import StockIndicator from '../components/StockIndicator'
import type { InventoryItem, InventoryMovement } from '../services/inventory'

export default function StockManagement() {
  const [activeTab, setActiveTab] = useState<'overview' | 'movements' | 'adjust'>('overview')
  const [items, setItems] = useState<InventoryItem[]>([])
  const [movements, setMovements] = useState<InventoryMovement[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null)
  const [showAdjust, setShowAdjust] = useState(false)
  const [adjustData, setAdjustData] = useState({
    quantity: 0,
    type: 'adjusted',
    notes: '',
    reference: '',
  })
  const [message, setMessage] = useState<{ type: string; text: string } | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    try {
      const [invData, movData] = await Promise.all([
        getInventory({ page_size: 100 }),
        getMovements(undefined, { page_size: 50 }),
      ])
      setItems(invData.items || [])
      setMovements(movData.movements || [])
    } catch {
      // swallow
    } finally {
      setLoading(false)
    }
  }

  async function handleAdjust(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedItem) return
    try {
      await adjustStock(selectedItem.id, adjustData)
      setMessage({ type: 'success', text: `تم تعديل مخزون ${selectedItem.drug_name} بنجاح` })
      setShowAdjust(false)
      loadData()
    } catch {
      setMessage({ type: 'error', text: 'فشل تعديل المخزون' })
    }
  }

  const lowStockItems = items.filter((i) => i.quantity <= i.reorder_level)
  const outOfStock = items.filter((i) => i.quantity <= 0)
  const expiringItems = items.filter(
    (i) =>
      i.expiry_date &&
      new Date(i.expiry_date) < new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
  )

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">إدارة المخزون</h1>
          <p className="page-subtitle">مراقبة وتحريك وتعديل المخزون</p>
        </div>
        <button className="btn btn-primary" onClick={loadData}>
          🔄 تحديث
        </button>
      </div>

      {message && (
        <div className={`alert alert-${message.type}`} role="alert" style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>{message.text}</span>
          <button className="btn btn-ghost btn-sm" onClick={() => setMessage(null)}>✕</button>
        </div>
      )}

      <div className="kpi-grid" style={{ marginBottom: '1rem' }}>
        <div className="kpi-card">
          <div className="kpi-icon" style={{ background: 'rgba(239,68,68,0.15)', color: '#ef4444' }}>
            🚫
          </div>
          <div className="kpi-value">{outOfStock.length}</div>
          <div className="kpi-label">نفد من المخزون</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{ background: 'rgba(245,158,11,0.15)', color: '#f59e0b' }}>
            ⚠️
          </div>
          <div className="kpi-value">{lowStockItems.length}</div>
          <div className="kpi-label">مخزون منخفض</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{ background: 'rgba(245,158,11,0.15)', color: '#f59e0b' }}>
            ⏰
          </div>
          <div className="kpi-value">{expiringItems.length}</div>
          <div className="kpi-label">ينتهي خلال 30 يوماً</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{ background: 'rgba(34,197,94,0.15)', color: '#22c55e' }}>
            📦
          </div>
          <div className="kpi-value">{items.length}</div>
          <div className="kpi-label">إجمالي الأصناف</div>
        </div>
      </div>

      <div className="tabs">
        <button className={`tab ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}>
          📊 نظرة عامة
        </button>
        <button className={`tab ${activeTab === 'movements' ? 'active' : ''}`} onClick={() => setActiveTab('movements')}>
          🔄 حركات المخزون
        </button>
        <button className={`tab ${activeTab === 'adjust' ? 'active' : ''}`} onClick={() => setActiveTab('adjust')}>
          ✏️ تعديل المخزون
        </button>
      </div>

      {activeTab === 'overview' && (
        <div className="card">
          <div className="toolbar">
            <div className="search-box">
              <span className="search-icon">🔍</span>
              <input type="text" placeholder="بحث..." value={search} onChange={(e) => setSearch(e.target.value)} />
            </div>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table role="grid" aria-label="نظرة عامة على المخزون">
              <thead>
                <tr>
                  <th>الاسم</th>
                  <th>الكمية</th>
                  <th>حد الطلب</th>
                  <th>الحالة</th>
                  <th>انتهاء</th>
                  <th>الموقع</th>
                </tr>
              </thead>
              <tbody>
                {items.length === 0 ? (
                  <tr><td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>لا توجد أصناف</td></tr>
                ) : (
                  items.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <div style={{ fontWeight: 600 }}>{item.drug_name}</div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{item.generic_name}</div>
                      </td>
                      <td style={{ fontWeight: 700 }}>{item.quantity}</td>
                      <td>{item.reorder_level}</td>
                      <td>
                        <StockIndicator current={item.quantity} reorderLevel={item.reorder_level} size="sm" />
                      </td>
                      <td style={{ color: new Date(item.expiry_date) < new Date() ? 'var(--accent-danger)' : new Date(item.expiry_date) < new Date(Date.now() + 30 * 864e5) ? 'var(--accent-warning)' : undefined }}>
                        {item.expiry_date ? new Date(item.expiry_date).toLocaleDateString('ar-IQ') : '-'}
                      </td>
                      <td style={{ fontSize: '0.8rem' }}>{item.location || '-'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'movements' && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">حركات المخزون</h3>
            <span className="badge badge-info">{movements.length} حركة</span>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table role="grid" aria-label="حركات المخزون">
              <thead>
                <tr>
                  <th>التاريخ</th>
                  <th>النوع</th>
                  <th>الكمية</th>
                  <th>رقم الدفعة</th>
                  <th>المرجع</th>
                  <th>ملاحظات</th>
                  <th>بواسطة</th>
                </tr>
              </thead>
              <tbody>
                {movements.length === 0 ? (
                  <tr><td colSpan={7} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>لا توجد حركات</td></tr>
                ) : (
                  movements.map((mov) => (
                    <tr key={mov.id}>
                      <td style={{ fontSize: '0.8rem' }}>{new Date(mov.created_at).toLocaleString('ar-IQ')}</td>
                      <td>
                        <span className={`badge ${
                          mov.type === 'received' ? 'badge-success' :
                          mov.type === 'dispensed' ? 'badge-danger' :
                          mov.type === 'returned' ? 'badge-info' :
                          mov.type === 'wasted' ? 'badge-warning' : 'badge-neutral'
                        }`}>
                          {mov.type === 'received' ? 'استلام' :
                           mov.type === 'dispensed' ? 'صرف' :
                           mov.type === 'returned' ? 'مرتجع' :
                           mov.type === 'wasted' ? 'تالف' :
                           mov.type === 'adjusted' ? 'تسوية' : 'تحويل'}
                        </span>
                      </td>
                      <td style={{ fontWeight: 700, color: mov.quantity > 0 ? 'var(--accent-success)' : 'var(--accent-danger)' }}>
                        {mov.quantity > 0 ? `+${mov.quantity}` : mov.quantity}
                      </td>
                      <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{mov.batch_number}</td>
                      <td style={{ fontSize: '0.8rem' }}>{mov.reference || '-'}</td>
                      <td style={{ fontSize: '0.8rem', maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {mov.notes || '-'}
                      </td>
                      <td style={{ fontSize: '0.8rem' }}>{mov.performed_by}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'adjust' && (
        <div className="grid-2" style={{ alignItems: 'start' }}>
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">اختيار صنف للتعديل</h3>
            </div>
            <div className="form-group">
              <input type="text" placeholder="بحث..." value={search} onChange={(e) => setSearch(e.target.value)} />
            </div>
            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
              {items
                .filter((i) => i.drug_name.toLowerCase().includes(search.toLowerCase()))
                .map((item) => (
                  <button
                    key={item.id}
                    style={{
                      width: '100%',
                      textAlign: 'right',
                      padding: '0.625rem',
                      background: selectedItem?.id === item.id ? 'var(--bg-hover)' : 'transparent',
                      borderBottom: '1px solid var(--border-color)',
                      color: 'var(--text-primary)',
                    }}
                    onClick={() => { setSelectedItem(item); setShowAdjust(true) }}
                  >
                    <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{item.drug_name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', justifyContent: 'space-between' }}>
                      <span>{item.generic_name}</span>
                      <span>المخزون: {item.quantity}</span>
                    </div>
                  </button>
                ))}
            </div>
          </div>

          <div className="card">
            {showAdjust && selectedItem ? (
              <div>
                <div className="card-header">
                  <h3 className="card-title">تعديل مخزون {selectedItem.drug_name}</h3>
                </div>
                <div style={{ marginBottom: '1rem' }}>
                  <StockIndicator current={selectedItem.quantity} reorderLevel={selectedItem.reorder_level} size="lg" showLabel />
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                    المخزون الحالي: <strong>{selectedItem.quantity}</strong> | حد الطلب: {selectedItem.reorder_level} | كمية الطلب: {selectedItem.reorder_quantity}
                  </div>
                </div>
                <form onSubmit={handleAdjust}>
                  <div className="form-group">
                    <label className="form-label">نوع الحركة</label>
                    <select value={adjustData.type} onChange={(e) => setAdjustData((p) => ({ ...p, type: e.target.value }))}>
                      <option value="received">استلام</option>
                      <option value="dispensed">صرف</option>
                      <option value="returned">مرتجع</option>
                      <option value="wasted">تالف / هالك</option>
                      <option value="adjusted">تسوية جرد</option>
                      <option value="transferred">تحويل</option>
                    </select>
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-label">الكمية</label>
                      <input
                        type="number"
                        value={adjustData.quantity}
                        onChange={(e) => setAdjustData((p) => ({ ...p, quantity: parseInt(e.target.value) || 0 }))}
                        min={1}
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">رقم المرجع</label>
                      <input
                        type="text"
                        value={adjustData.reference}
                        onChange={(e) => setAdjustData((p) => ({ ...p, reference: e.target.value }))}
                        placeholder="رقم الوصل / الوصفة..."
                      />
                    </div>
                  </div>
                  <div className="form-group">
                    <label className="form-label">ملاحظات</label>
                    <textarea
                      value={adjustData.notes}
                      onChange={(e) => setAdjustData((p) => ({ ...p, notes: e.target.value }))}
                      rows={3}
                      placeholder="سبب التعديل..."
                      required
                    />
                  </div>
                  <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                    <button type="button" className="btn btn-secondary" onClick={() => setShowAdjust(false)}>إلغاء</button>
                    <button type="submit" className="btn btn-primary">تأكيد التعديل</button>
                  </div>
                </form>
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-icon">✏️</div>
                <h3>اختر صنفاً</h3>
                <p>اختر صنفاً من القائمة لتعديل مخزونه</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
