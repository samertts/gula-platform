import { useState, useEffect, useCallback } from 'react'
import { worklistService, type WorklistItem, type WorklistStatus } from '@services/worklist'
import { dicomService, type DicomStudy, type Modality } from '@services/dicom'
import { OrderEntry } from '@components/OrderEntry'

type Tab = 'all' | 'pending' | 'in_progress' | 'completed' | 'cancelled'

export function Orders() {
  const [orders, setOrders] = useState<WorklistItem[]>([])
  const [studies, setStudies] = useState<DicomStudy[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<Tab>('all')
  const [showOrderEntry, setShowOrderEntry] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [modalityFilter, setModalityFilter] = useState<Modality | ''>('')
  const [statusFilter, setStatusFilter] = useState<WorklistStatus | ''>('')
  const [selectedOrder, setSelectedOrder] = useState<WorklistItem | null>(null)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)

  const fetchOrders = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const filters: Record<string, string> = {}
      if (activeTab === 'pending') filters.status = 'scheduled'
      else if (activeTab === 'in_progress') filters.status = 'started'
      else if (activeTab === 'completed') filters.status = 'completed'
      else if (activeTab === 'cancelled') filters.status = 'cancelled'
      if (modalityFilter) filters.modality = modalityFilter
      if (statusFilter) filters.status = statusFilter
      if (searchQuery) filters.patient_name = searchQuery

      const res = await worklistService.getWorklist({
        ...filters,
        page,
        limit: 20
      })
      setOrders(res.items)
      setTotalPages(res.total_pages)

      // Load studies for completed orders
      if (res.items.some(i => i.status === 'completed')) {
        const studiesRes = await dicomService.searchStudies({ limit: 20 })
        setStudies(studiesRes.items || [])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'فشل تحميل الطلبات')
    } finally {
      setLoading(false)
    }
  }, [activeTab, modalityFilter, statusFilter, searchQuery, page])

  useEffect(() => {
    fetchOrders()
  }, [fetchOrders])

  useEffect(() => {
    setPage(1)
  }, [activeTab, modalityFilter, searchQuery])

  const handleStatusChange = useCallback(async (id: string, status: WorklistStatus) => {
    try {
      await worklistService.updateWorklistStatus(id, status)
      setOrders(prev => prev.map(o => o.id === id ? { ...o, status } : o))
    } catch (err) {
      console.error('Failed to update status:', err)
    }
  }, [])

  const handleOrderSubmit = useCallback(async (data: Record<string, unknown>) => {
    try {
      await worklistService.createWorklistItem(data as unknown as WorklistItem)
      setShowOrderEntry(false)
      fetchOrders()
    } catch (err) {
      console.error('Failed to create order:', err)
    }
  }, [fetchOrders])

  const getModalityColor = (modality: string) => {
    const colors: Record<string, string> = {
      CT: '#3b82f6', MR: '#8b5cf6', US: '#22c55e', XA: '#ef4444',
      CR: '#f59e0b', DX: '#f59e0b', MG: '#ec4899', NM: '#06b6d4', PT: '#14b8a6'
    }
    return colors[modality] || '#94a3b8'
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: 'all', label: 'الكل' },
    { id: 'pending', label: 'معلقة' },
    { id: 'in_progress', label: 'قيد الإجراء' },
    { id: 'completed', label: 'مكتملة' },
    { id: 'cancelled', label: 'ملغية' }
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>إدارة الطلبات</h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-tertiary)' }}>إدارة طلبات فحوصات الأشعة</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowOrderEntry(true)}>
          + طلب جديد
        </button>
      </div>

      {/* Search & Filters */}
      <div className="card" style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 200 }}>
          <input
            className="input"
            placeholder="بحث باسم المريض..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
          />
        </div>
        <select className="select" value={modalityFilter} onChange={e => setModalityFilter(e.target.value as Modality | '')} style={{ width: 120 }}>
          <option value="">كل الأجهزة</option>
          <option value="CT">CT</option>
          <option value="MR">MR</option>
          <option value="US">US</option>
          <option value="XA">XA</option>
          <option value="CR">CR</option>
          <option value="MG">MG</option>
          <option value="NM">NM</option>
          <option value="PT">PT</option>
        </select>
        <select className="select" value={statusFilter} onChange={e => setStatusFilter(e.target.value as WorklistStatus | '')} style={{ width: 130 }}>
          <option value="">كل الحالات</option>
          <option value="scheduled">مجدول</option>
          <option value="arrived">وصل</option>
          <option value="started">قيد الإجراء</option>
          <option value="completed">مكتمل</option>
          <option value="cancelled">ملغي</option>
        </select>
        <button className="btn btn-ghost" onClick={() => { setSearchQuery(''); setModalityFilter(''); setStatusFilter('') }}>
          مسح
        </button>
      </div>

      {/* Tabs */}
      <div className="tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Order entry modal */}
      {showOrderEntry && (
        <div className="modal-overlay" onClick={() => setShowOrderEntry(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 800 }}>
            <div className="modal-header">
              <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>طلب فحص جديد</h2>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowOrderEntry(false)}>✕</button>
            </div>
            <div className="modal-body">
              <OrderEntry
                onSubmit={(data) => {
                  handleOrderSubmit(data as unknown as Record<string, unknown>)
                  setShowOrderEntry(false)
                }}
                onCancel={() => setShowOrderEntry(false)}
              />
            </div>
          </div>
        </div>
      )}

      {/* Orders table */}
      {loading ? (
        <div className="card" style={{ padding: 0 }}>
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="skeleton" style={{ height: 48, margin: 8 }} />
          ))}
        </div>
      ) : error ? (
        <div className="card empty-state">
          <div className="empty-state-icon">⚠️</div>
          <p style={{ color: 'var(--text-danger)' }}>{error}</p>
          <button className="btn btn-primary mt-md" onClick={fetchOrders}>إعادة المحاولة</button>
        </div>
      ) : orders.length === 0 ? (
        <div className="card empty-state">
          <div className="empty-state-icon">📋</div>
          <p>لا توجد طلبات</p>
          <button className="btn btn-primary mt-md" onClick={() => setShowOrderEntry(true)}>إنشاء طلب جديد</button>
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>الحالة</th>
                <th>المريض</th>
                <th>الفحص</th>
                <th>الجهاز</th>
                <th>التاريخ</th>
                <th>الطبيب المحول</th>
                <th>الأولوية</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {orders.map(order => (
                <tr key={order.id} style={{ cursor: 'pointer' }} onClick={() => setSelectedOrder(order)}>
                  <td>
                    <span className={`badge ${
                      order.status === 'completed' ? 'badge-success' :
                      order.status === 'started' ? 'badge-warning' :
                      order.status === 'arrived' ? 'badge-primary' :
                      order.status === 'scheduled' ? 'badge-info' : 'badge-neutral'
                    }`}>
                      {order.status === 'completed' ? 'مكتمل' :
                       order.status === 'started' ? 'قيد الإجراء' :
                       order.status === 'arrived' ? 'وصل' :
                       order.status === 'scheduled' ? 'مجدول' : 'ملغي'}
                    </span>
                  </td>
                  <td>
                    <div style={{ fontWeight: 500, fontSize: '0.875rem' }}>{order.patient_name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>{order.patient_id}</div>
                  </td>
                  <td>
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 4,
                      padding: '2px 8px',
                      borderRadius: 4,
                      fontSize: '0.75rem',
                      fontWeight: 500,
                      backgroundColor: getModalityColor(order.modality),
                      color: 'white'
                    }}>
                      {order.modality}
                    </span>
                    <span style={{ fontSize: '0.8rem', marginInlineStart: 8 }}>
                      {order.procedure_description || order.study_description}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.8rem' }}>{order.scheduled_station}</td>
                  <td style={{ fontSize: '0.8rem', whiteSpace: 'nowrap' }}>
                    {order.scheduled_date}<br />
                    <span style={{ color: 'var(--text-tertiary)', fontSize: '0.75rem' }}>{order.scheduled_time}</span>
                  </td>
                  <td style={{ fontSize: '0.8rem' }}>{order.requesting_physician}</td>
                  <td>
                    <span className={`badge ${
                      order.priority === 'stat' ? 'badge-danger' :
                      order.priority === 'urgent' ? 'badge-warning' : 'badge-info'
                    }`}>
                      {order.priority === 'stat' ? 'طوارئ' : order.priority === 'urgent' ? 'عاجل' : 'روتيني'}
                    </span>
                  </td>
                  <td>
                    <select
                      className="select"
                      value={order.status}
                      onChange={e => handleStatusChange(order.id, e.target.value as WorklistStatus)}
                      onClick={e => e.stopPropagation()}
                      style={{ fontSize: '0.75rem', padding: '2px 4px', width: 100 }}
                    >
                      <option value="scheduled">مجدول</option>
                      <option value="arrived">وصل</option>
                      <option value="started">قيد الإجراء</option>
                      <option value="completed">مكتمل</option>
                      <option value="cancelled">ملغي</option>
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="pagination">
              <button className="pagination-btn" disabled={page === 1} onClick={() => setPage(p => p - 1)}>‹</button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map(p => (
                <button
                  key={p}
                  className={`pagination-btn ${p === page ? 'active' : ''}`}
                  onClick={() => setPage(p)}
                >
                  {p}
                </button>
              ))}
              <button className="pagination-btn" disabled={page === totalPages} onClick={() => setPage(p => p + 1)}>›</button>
            </div>
          )}
        </div>
      )}

      {/* Order detail modal */}
      {selectedOrder && (
        <div className="modal-overlay" onClick={() => setSelectedOrder(null)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 600 }}>
            <div className="modal-header">
              <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>تفاصيل الطلب</h2>
              <button className="btn btn-ghost btn-sm" onClick={() => setSelectedOrder(null)}>✕</button>
            </div>
            <div className="modal-body">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div>
                  <label className="input-label">المريض</label>
                  <p style={{ fontWeight: 500 }}>{selectedOrder.patient_name}</p>
                </div>
                <div>
                  <label className="input-label">رقم المريض</label>
                  <p>{selectedOrder.patient_id}</p>
                </div>
                <div>
                  <label className="input-label">الفحص</label>
                  <p>{selectedOrder.procedure_description || selectedOrder.study_description}</p>
                </div>
                <div>
                  <label className="input-label">الجهاز</label>
                  <p>{selectedOrder.modality} — {selectedOrder.scheduled_station}</p>
                </div>
                <div>
                  <label className="input-label">التاريخ</label>
                  <p>{selectedOrder.scheduled_date} {selectedOrder.scheduled_time}</p>
                </div>
                <div>
                  <label className="input-label">الطبيب المحول</label>
                  <p>{selectedOrder.requesting_physician}</p>
                </div>
                <div>
                  <label className="input-label">الأولوية</label>
                  <span className={`badge ${
                    selectedOrder.priority === 'stat' ? 'badge-danger' :
                    selectedOrder.priority === 'urgent' ? 'badge-warning' : 'badge-info'
                  }`}>
                    {selectedOrder.priority === 'stat' ? 'طوارئ' : selectedOrder.priority === 'urgent' ? 'عاجل' : 'روتيني'}
                  </span>
                </div>
                <div>
                  <label className="input-label">مدة الفحص</label>
                  <p>{selectedOrder.duration_minutes} دقيقة</p>
                </div>
                {selectedOrder.contrast_required && (
                  <div style={{ gridColumn: '1 / -1' }}>
                    <label className="input-label">الصبغة</label>
                    <p>{selectedOrder.contrast_details || 'مطلوب صبغة'}</p>
                  </div>
                )}
                {selectedOrder.notes && (
                  <div style={{ gridColumn: '1 / -1' }}>
                    <label className="input-label">ملاحظات</label>
                    <p>{selectedOrder.notes}</p>
                  </div>
                )}
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setSelectedOrder(null)}>إغلاق</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
