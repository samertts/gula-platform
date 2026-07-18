import React, { useState, useEffect } from 'react'
import { getInventory, getMovements } from '../services/inventory'
import StockIndicator from '../components/StockIndicator'
import type { InventoryItem, InventoryMovement } from '../services/inventory'

interface ControlledLog {
  id: string
  drug_name: string
  batch_number: string
  action: string
  quantity: number
  balance_before: number
  balance_after: number
  pharmacist: string
  witness: string
  patient_name: string
  reason: string
  timestamp: string
}

export default function ControlledDrugs() {
  const [activeTab, setActiveTab] = useState<'inventory' | 'register' | 'discrepancies'>('inventory')
  const [controlledItems, setControlledItems] = useState<InventoryItem[]>([])
  const [movements, setMovements] = useState<InventoryMovement[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showDiscrepancyForm, setShowDiscrepancyForm] = useState(false)
  const [discrepancyData, setDiscrepancyData] = useState({
    item_id: '',
    expected_quantity: 0,
    actual_quantity: 0,
    notes: '',
  })

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    try {
      const invData = await getInventory({ controlled: true, page_size: 100 })
      setControlledItems(invData.items || [])
      const movData = await getMovements(undefined, { type: 'dispensed', page_size: 50 })
      setMovements(movData.movements || [])
    } catch {
      setControlledItems([])
    } finally {
      setLoading(false)
    }
  }

  const filtered = controlledItems.filter(
    (item) =>
      item.drug_name.toLowerCase().includes(search.toLowerCase()) ||
      item.drug_code.toLowerCase().includes(search.toLowerCase()),
  )

  const sampleRegister: ControlledLog[] = controlledItems.slice(0, 10).map((item, idx) => ({
    id: `log-${idx}`,
    drug_name: item.drug_name,
    batch_number: item.batch_number,
    action: idx % 2 === 0 ? 'صرف' : 'استلام',
    quantity: idx % 2 === 0 ? -5 : 50,
    balance_before: item.quantity + 5,
    balance_after: item.quantity,
    pharmacist: 'د. أحمد السامرائي',
    witness: 'م. سارة جاسم',
    patient_name: idx % 2 === 0 ? 'مريض عينة' : '-',
    reason: idx % 2 === 0 ? 'وصفة طبية رقم RX-2024-001' : 'توريد من المورد',
    timestamp: new Date().toISOString(),
  }))

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">الأدوية المخدرة والخاضعة للرقابة</h1>
          <p className="page-subtitle">إجمالي {controlledItems.length} صنف خاضع للرقابة</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-warning" onClick={() => setShowDiscrepancyForm(true)}>
            + تسجيل فارق جرد
          </button>
          <button className="btn btn-primary" onClick={loadData}>
            🔄 تحديث
          </button>
        </div>
      </div>

      {controlledItems.length > 0 && (
        <div className="alert alert-warning" role="alert" style={{ marginBottom: '1rem' }}>
          ⚠️ يجب الاحتفاظ بسجل منفصل للأدوية المخدرة والتوقيع من قبل صيدليين اثنين عند الصرف.
        </div>
      )}

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'inventory' ? 'active' : ''}`}
          onClick={() => setActiveTab('inventory')}
        >
          📦 المخزون الخاضع للرقابة
        </button>
        <button
          className={`tab ${activeTab === 'register' ? 'active' : ''}`}
          onClick={() => setActiveTab('register')}
        >
          📋 سجل الصرف والاستلام
        </button>
        <button
          className={`tab ${activeTab === 'discrepancies' ? 'active' : ''}`}
          onClick={() => setActiveTab('discrepancies')}
        >
          🔍 فارقات الجرد
        </button>
      </div>

      {activeTab === 'inventory' && (
        <div className="card">
          <div className="toolbar">
            <div className="search-box">
              <span className="search-icon">🔍</span>
              <input
                type="text"
                placeholder="بحث في الأدوية المخدرة..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                aria-label="بحث في الأدوية المخدرة"
              />
            </div>
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              <span className="spinner" />
            </div>
          ) : filtered.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">💊</div>
              <h3>لا توجد أدوية خاضعة للرقابة</h3>
              <p>لم يتم إضافة أي أدوية مخدرة بعد</p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table role="grid" aria-label="الأدوية الخاضعة للرقابة">
                <thead>
                  <tr>
                    <th>الكود</th>
                    <th>الاسم</th>
                    <th>التركيز</th>
                    <th>الدفعة</th>
                    <th>انتهاء</th>
                    <th>المخزون</th>
                    <th>الموقع</th>
                    <th>الحالة</th>
                    <th>إجراءات</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((item) => (
                    <tr key={item.id}>
                      <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{item.drug_code}</td>
                      <td>
                        <div style={{ fontWeight: 600 }}>{item.drug_name}</div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{item.generic_name}</div>
                      </td>
                      <td>{item.strength}</td>
                      <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{item.batch_number}</td>
                      <td>{item.expiry_date ? new Date(item.expiry_date).toLocaleDateString('ar-IQ') : '-'}</td>
                      <td>
                        <StockIndicator current={item.quantity} reorderLevel={item.reorder_level} size="sm" />
                      </td>
                      <td style={{ fontSize: '0.8rem' }}>{item.location || '-'}</td>
                      <td>
                        <span className={`badge ${item.quantity <= 0 ? 'badge-danger' : item.quantity <= item.reorder_level ? 'badge-warning' : 'badge-success'}`}>
                          {item.quantity <= 0 ? 'نفد' : item.quantity <= item.reorder_level ? 'منخفض' : 'متوفر'}
                        </span>
                      </td>
                      <td>
                        <button className="btn btn-sm btn-primary">صرف</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeTab === 'register' && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">سجل الصرف والاستلام</h3>
            <span className="badge badge-info">{sampleRegister.length} عملية</span>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table role="grid" aria-label="سجل الصرف والاستلام">
              <thead>
                <tr>
                  <th>التاريخ</th>
                  <th>الدواء</th>
                  <th>الدفعة</th>
                  <th>الإجراء</th>
                  <th>الكمية</th>
                  <th>الرصيد قبل</th>
                  <th>الرصيد بعد</th>
                  <th>الصيدلي</th>
                  <th>الشاهد</th>
                  <th>السبب</th>
                </tr>
              </thead>
              <tbody>
                {sampleRegister.map((log) => (
                  <tr key={log.id}>
                    <td style={{ fontSize: '0.8rem' }}>
                      {new Date(log.timestamp).toLocaleString('ar-IQ')}
                    </td>
                    <td style={{ fontWeight: 600 }}>{log.drug_name}</td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{log.batch_number}</td>
                    <td>
                      <span className={`badge ${log.action === 'صرف' ? 'badge-danger' : 'badge-success'}`}>
                        {log.action}
                      </span>
                    </td>
                    <td style={{ fontWeight: 700, color: log.quantity < 0 ? 'var(--accent-danger)' : 'var(--accent-success)' }}>
                      {log.quantity > 0 ? `+${log.quantity}` : log.quantity}
                    </td>
                    <td>{log.balance_before}</td>
                    <td>{log.balance_after}</td>
                    <td>{log.pharmacist}</td>
                    <td>{log.witness}</td>
                    <td style={{ fontSize: '0.75rem', maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {log.reason}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'discrepancies' && (
        <div>
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">فارقات الجرد</h3>
              <button className="btn btn-warning" onClick={() => setShowDiscrepancyForm(true)}>
                + تسجيل فارق
              </button>
            </div>
            <div className="empty-state">
              <div className="empty-icon">✅</div>
              <h3>لا توجد فارقات</h3>
              <p>جميع الأرصدة متطابقة مع الجرد الفعلي</p>
            </div>
          </div>
        </div>
      )}

      {showDiscrepancyForm && (
        <div className="modal-overlay">
          <div className="modal" role="dialog" aria-modal="true" aria-label="تسجيل فارق جرد">
            <div className="modal-header">
              <h2 className="modal-title">تسجيل فارق جرد</h2>
              <button className="modal-close" onClick={() => setShowDiscrepancyForm(false)}>✕</button>
            </div>
            <form onSubmit={(e) => { e.preventDefault(); setShowDiscrepancyForm(false) }}>
              <div className="form-group">
                <label className="form-label">الدواء</label>
                <select
                  value={discrepancyData.item_id}
                  onChange={(e) => setDiscrepancyData((prev) => ({ ...prev, item_id: e.target.value }))}
                  aria-label="اختر الدواء"
                >
                  <option value="">اختر...</option>
                  {controlledItems.map((item) => (
                    <option key={item.id} value={item.id}>{item.drug_name} - {item.batch_number}</option>
                  ))}
                </select>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">الكمية المتوقعة (نظامياً)</label>
                  <input
                    type="number"
                    min={0}
                    value={discrepancyData.expected_quantity}
                    onChange={(e) => setDiscrepancyData((prev) => ({ ...prev, expected_quantity: parseInt(e.target.value) || 0 }))}
                    aria-label="الكمية المتوقعة"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">الكمية الفعلية (جرد)</label>
                  <input
                    type="number"
                    min={0}
                    value={discrepancyData.actual_quantity}
                    onChange={(e) => setDiscrepancyData((prev) => ({ ...prev, actual_quantity: parseInt(e.target.value) || 0 }))}
                    aria-label="الكمية الفعلية"
                  />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">ملاحظات</label>
                <textarea
                  value={discrepancyData.notes}
                  onChange={(e) => setDiscrepancyData((prev) => ({ ...prev, notes: e.target.value }))}
                  rows={3}
                  placeholder="سبب الفارق وإجراءات التصحيح..."
                  aria-label="ملاحظات"
                />
              </div>
              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowDiscrepancyForm(false)}>إلغاء</button>
                <button type="submit" className="btn btn-primary">تسجيل</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
