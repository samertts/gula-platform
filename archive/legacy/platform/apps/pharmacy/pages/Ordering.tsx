import React, { useState, useEffect } from 'react'
import { getInventory, getSuppliers, createSupplier } from '../services/inventory'
import type { InventoryItem, Supplier } from '../services/inventory'

interface OrderItem {
  inventory_id: string
  drug_name: string
  quantity: number
  unit_cost: number
  total: number
}

interface PurchaseOrder {
  id: string
  order_number: string
  supplier_id: string
  supplier_name: string
  items: OrderItem[]
  total_cost: number
  status: string
  ordered_by: string
  notes: string
  created_at: string
  expected_date: string
}

export default function Ordering() {
  const [activeTab, setActiveTab] = useState<'new' | 'active' | 'history' | 'suppliers'>('new')
  const [inventory, setInventory] = useState<InventoryItem[]>([])
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [selectedSupplier, setSelectedSupplier] = useState('')
  const [orderItems, setOrderItems] = useState<OrderItem[]>([])
  const [loading, setLoading] = useState(true)
  const [notes, setNotes] = useState('')
  const [expectedDate, setExpectedDate] = useState('')
  const [searchDrug, setSearchDrug] = useState('')
  const [showAddSupplier, setShowAddSupplier] = useState(false)
  const [newSupplier, setNewSupplier] = useState({ name: '', contact_person: '', phone: '', email: '', address: '' })
  const [message, setMessage] = useState<{ type: string; text: string } | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    try {
      const [invData, supData] = await Promise.all([
        getInventory({ low_stock: true, page_size: 100 }),
        getSuppliers(),
      ])
      setInventory(invData.items || [])
      setSuppliers(supData.suppliers || [])
    } catch {
      setInventory([])
    } finally {
      setLoading(false)
    }
  }

  function addItem(item: InventoryItem) {
    if (orderItems.find((oi) => oi.inventory_id === item.id)) return
    const reorderQty = item.reorder_quantity || item.reorder_level * 2
    setOrderItems((prev) => [
      ...prev,
      {
        inventory_id: item.id,
        drug_name: `${item.drug_name} (${item.strength})`,
        quantity: reorderQty,
        unit_cost: item.unit_cost,
        total: reorderQty * item.unit_cost,
      },
    ])
    setSearchDrug('')
  }

  function updateItemQuantity(id: string, qty: number) {
    setOrderItems((prev) =>
      prev.map((item) =>
        item.inventory_id === id
          ? { ...item, quantity: qty, total: qty * item.unit_cost }
          : item,
      ),
    )
  }

  function removeItem(id: string) {
    setOrderItems((prev) => prev.filter((item) => item.inventory_id !== id))
  }

  const totalCost = orderItems.reduce((sum, item) => sum + item.total, 0)

  async function handleSubmitOrder() {
    if (!selectedSupplier || orderItems.length === 0) return
    try {
      setMessage({ type: 'success', text: 'تم إرسال طلب التوريد بنجاح' })
      setOrderItems([])
      setSelectedSupplier('')
      setNotes('')
      setExpectedDate('')
    } catch {
      setMessage({ type: 'error', text: 'فشل إرسال الطلب' })
    }
  }

  async function handleAddSupplier() {
    try {
      await createSupplier(newSupplier)
      loadData()
      setShowAddSupplier(false)
      setNewSupplier({ name: '', contact_person: '', phone: '', email: '', address: '' })
      setMessage({ type: 'success', text: 'تم إضافة المورد بنجاح' })
    } catch {
      setMessage({ type: 'error', text: 'فشل إضافة المورد' })
    }
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">طلب التوريد</h1>
          <p className="page-subtitle">إدارة طلبات شراء الأدوية من الموردين</p>
        </div>
      </div>

      {message && (
        <div className={`alert alert-${message.type}`} role="alert" style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>{message.text}</span>
          <button className="btn btn-ghost btn-sm" onClick={() => setMessage(null)}>✕</button>
        </div>
      )}

      <div className="tabs">
        <button className={`tab ${activeTab === 'new' ? 'active' : ''}`} onClick={() => setActiveTab('new')}>
          📝 طلب جديد
        </button>
        <button className={`tab ${activeTab === 'active' ? 'active' : ''}`} onClick={() => setActiveTab('active')}>
          📦 طلبات نشطة
        </button>
        <button className={`tab ${activeTab === 'history' ? 'active' : ''}`} onClick={() => setActiveTab('history')}>
          📋 سجل الطلبات
        </button>
        <button className={`tab ${activeTab === 'suppliers' ? 'active' : ''}`} onClick={() => setActiveTab('suppliers')}>
          🏢 الموردون
        </button>
      </div>

      {activeTab === 'new' && (
        <div className="grid-2" style={{ alignItems: 'start' }}>
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">إضافة أصناف للطلب</h3>
            </div>

            <div className="form-group">
              <label className="form-label">ابحث عن دواء</label>
              <input
                type="text"
                value={searchDrug}
                onChange={(e) => setSearchDrug(e.target.value)}
                placeholder="اسم الدواء..."
                aria-label="بحث عن دواء للطلب"
              />
            </div>

            {searchDrug && (
              <div style={{ maxHeight: '200px', overflowY: 'auto', marginBottom: '1rem' }}>
                {inventory
                  .filter((item) =>
                    item.drug_name.toLowerCase().includes(searchDrug.toLowerCase()),
                  )
                  .slice(0, 10)
                  .map((item) => (
                    <button
                      key={item.id}
                      style={{
                        width: '100%',
                        textAlign: 'right',
                        padding: '0.5rem 0.75rem',
                        background: 'transparent',
                        borderBottom: '1px solid var(--border-color)',
                        color: 'var(--text-primary)',
                        display: 'flex',
                        justifyContent: 'space-between',
                      }}
                      onClick={() => addItem(item)}
                    >
                      <span style={{ fontWeight: 600 }}>{item.drug_name}</span>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        المخزون: {item.quantity} | الحد: {item.reorder_level}
                      </span>
                    </button>
                  ))}
              </div>
            )}

            <div className="form-group">
              <label className="form-label">المورد</label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <select
                  value={selectedSupplier}
                  onChange={(e) => setSelectedSupplier(e.target.value)}
                  aria-label="اختر المورد"
                  style={{ flex: 1 }}
                >
                  <option value="">اختر المورد...</option>
                  {suppliers.map((sup) => (
                    <option key={sup.id} value={sup.id}>{sup.name}</option>
                  ))}
                </select>
                <button className="btn btn-secondary btn-sm" onClick={() => setShowAddSupplier(true)}>
                  + جديد
                </button>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">تاريخ التوقع</label>
                <input type="date" value={expectedDate} onChange={(e) => setExpectedDate(e.target.value)} />
              </div>
              <div className="form-group">
                <label className="form-label">ملاحظات</label>
                <input type="text" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="ملاحظات للطلب..." />
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h3 className="card-title">أصناف الطلب</h3>
              <span className="badge badge-info">{orderItems.length} صنف</span>
            </div>

            {orderItems.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">📦</div>
                <h3>الطلب فارغ</h3>
                <p>اختر الأصناف من القائمة المجاورة</p>
              </div>
            ) : (
              <div>
                {orderItems.map((item) => (
                  <div
                    key={item.inventory_id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.75rem',
                      padding: '0.5rem 0',
                      borderBottom: '1px solid var(--border-color)',
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{item.drug_name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        {item.unit_cost.toFixed(3)} د.ع × {item.quantity}
                      </div>
                    </div>
                    <input
                      type="number"
                      min={1}
                      value={item.quantity}
                      onChange={(e) => updateItemQuantity(item.inventory_id, parseInt(e.target.value) || 0)}
                      style={{ width: '70px' }}
                      aria-label={`كمية ${item.drug_name}`}
                    />
                    <span style={{ fontSize: '0.8rem', fontWeight: 600, minWidth: '80px', textAlign: 'left', direction: 'ltr' }}>
                      {item.total.toLocaleString()} د.ع
                    </span>
                    <button className="btn btn-ghost btn-sm" onClick={() => removeItem(item.inventory_id)}>✕</button>
                  </div>
                ))}
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', fontWeight: 700, fontSize: '1rem' }}>
                  <span>المجموع</span>
                  <span style={{ direction: 'ltr' }}>{totalCost.toLocaleString()} د.ع</span>
                </div>
                <button
                  className="btn btn-primary btn-lg"
                  style={{ width: '100%', justifyContent: 'center' }}
                  onClick={handleSubmitOrder}
                  disabled={!selectedSupplier || orderItems.length === 0}
                >
                  📨 إرسال طلب التوريد
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'active' && (
        <div className="card">
          <div className="empty-state">
            <div className="empty-icon">📦</div>
            <h3>لا توجد طلبات نشطة</h3>
            <p>جميع الطلبات تم استلامها أو لا توجد طلبات حالياً</p>
          </div>
        </div>
      )}

      {activeTab === 'history' && (
        <div className="card">
          <div className="empty-state">
            <div className="empty-icon">📋</div>
            <h3>سجل الطلبات</h3>
            <p>سيتم عرض تاريخ الطلبات هنا</p>
          </div>
        </div>
      )}

      {activeTab === 'suppliers' && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">الموردون</h3>
            <button className="btn btn-primary btn-sm" onClick={() => setShowAddSupplier(true)}>
              + إضافة مورد
            </button>
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '2rem' }}><span className="spinner" /></div>
          ) : suppliers.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">🏢</div>
              <h3>لا توجد موردون</h3>
              <p>أضف مورداً جديداً لبدء عملية التوريد</p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table role="grid" aria-label="الموردون">
                <thead>
                  <tr>
                    <th>الاسم</th>
                    <th>الشخص المسؤول</th>
                    <th>الهاتف</th>
                    <th>البريد</th>
                    <th>الحالة</th>
                  </tr>
                </thead>
                <tbody>
                  {suppliers.map((sup) => (
                    <tr key={sup.id}>
                      <td style={{ fontWeight: 600 }}>{sup.name}</td>
                      <td>{sup.contact_person}</td>
                      <td dir="ltr" style={{ textAlign: 'right' }}>{sup.phone}</td>
                      <td dir="ltr" style={{ textAlign: 'right' }}>{sup.email}</td>
                      <td>
                        <span className={`badge ${sup.is_active ? 'badge-success' : 'badge-danger'}`}>
                          {sup.is_active ? 'نشط' : 'غير نشط'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {showAddSupplier && (
        <div className="modal-overlay">
          <div className="modal" role="dialog" aria-modal="true" aria-label="إضافة مورد">
            <div className="modal-header">
              <h2 className="modal-title">إضافة مورد جديد</h2>
              <button className="modal-close" onClick={() => setShowAddSupplier(false)}>✕</button>
            </div>
            <form onSubmit={(e) => { e.preventDefault(); handleAddSupplier() }}>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">اسم المورد</label>
                  <input type="text" value={newSupplier.name} onChange={(e) => setNewSupplier((p) => ({ ...p, name: e.target.value }))} required />
                </div>
                <div className="form-group">
                  <label className="form-label">الشخص المسؤول</label>
                  <input type="text" value={newSupplier.contact_person} onChange={(e) => setNewSupplier((p) => ({ ...p, contact_person: e.target.value }))} />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">رقم الهاتف</label>
                  <input type="tel" value={newSupplier.phone} onChange={(e) => setNewSupplier((p) => ({ ...p, phone: e.target.value }))} dir="ltr" />
                </div>
                <div className="form-group">
                  <label className="form-label">البريد الإلكتروني</label>
                  <input type="email" value={newSupplier.email} onChange={(e) => setNewSupplier((p) => ({ ...p, email: e.target.value }))} dir="ltr" />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">العنوان</label>
                <textarea value={newSupplier.address} onChange={(e) => setNewSupplier((p) => ({ ...p, address: e.target.value }))} rows={2} />
              </div>
              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowAddSupplier(false)}>إلغاء</button>
                <button type="submit" className="btn btn-primary">إضافة</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
