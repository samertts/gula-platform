import { useState, useEffect, useCallback } from 'react'
import { worklistService, type WorklistItem, type WorklistStatus, type WorklistFilter } from '@services/worklist'
import type { Modality } from '@services/dicom'
import { WorklistTable } from '@components/WorklistTable'

export function Worklist() {
  const [items, setItems] = useState<WorklistItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedItem, setSelectedItem] = useState<WorklistItem | null>(null)
  const [filter, setFilter] = useState<WorklistFilter>({})
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [autoRefresh, setAutoRefresh] = useState(true)

  const fetchWorklist = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await worklistService.getWorklist({
        ...filter,
        page,
        limit: 25
      })
      setItems(res.items)
      setTotalPages(res.total_pages)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'فشل تحميل قائمة العمل')
    } finally {
      setLoading(false)
    }
  }, [filter, page])

  useEffect(() => {
    fetchWorklist()
  }, [fetchWorklist])

  useEffect(() => {
    setPage(1)
  }, [filter])

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!autoRefresh) return
    const interval = setInterval(fetchWorklist, 30000)
    return () => clearInterval(interval)
  }, [fetchWorklist, autoRefresh])

  const handleStatusChange = useCallback(async (id: string, status: WorklistStatus) => {
    try {
      await worklistService.updateWorklistStatus(id, status)
      setItems(prev => prev.map(item => item.id === id ? { ...item, status } : item))

      if (status === 'arrived') {
        await worklistService.markArrived(id)
      } else if (status === 'started') {
        await worklistService.markStarted(id)
      } else if (status === 'completed') {
        const user = localStorage.getItem('gula_radiology_user_name') || 'مسؤول'
        await worklistService.markCompleted(id, user)
      }
    } catch (err) {
      console.error('Failed to update status:', err)
    }
  }, [])

  const handleSelectItem = useCallback((item: WorklistItem) => {
    setSelectedItem(item)
  }, [])

  const today = new Date().toISOString().split('T')[0]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>قائمة العمل</h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-tertiary)' }}>
            قائمة عمل أجهزة الأشعة (MWL)
            {items.length > 0 && <span style={{ marginInlineStart: 8 }}>— {items.length} فحص</span>}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.8rem', cursor: 'pointer' }}>
            <input type="checkbox" checked={autoRefresh} onChange={e => setAutoRefresh(e.target.checked)} />
            تحديث تلقائي
          </label>
          <button className="btn btn-secondary btn-sm" onClick={fetchWorklist}>
            ↻ تحديث
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card" style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div className="input-group" style={{ minWidth: 150 }}>
          <label className="input-label">تاريخ البدء</label>
          <input
            className="input"
            type="date"
            value={filter.date_from || today}
            onChange={e => setFilter(prev => ({ ...prev, date_from: e.target.value }))}
          />
        </div>
        <div className="input-group" style={{ minWidth: 150 }}>
          <label className="input-label">تاريخ الانتهاء</label>
          <input
            className="input"
            type="date"
            value={filter.date_to || ''}
            onChange={e => setFilter(prev => ({ ...prev, date_to: e.target.value }))}
          />
        </div>
        <div className="input-group" style={{ minWidth: 120 }}>
          <label className="input-label">الجهاز</label>
          <select
            className="select"
            value={filter.modality || ''}
            onChange={e => setFilter(prev => ({ ...prev, modality: e.target.value as Modality | undefined }))}
          >
            <option value="">الكل</option>
            {['CT', 'MR', 'US', 'XA', 'CR', 'DX', 'MG', 'NM', 'PT'].map(m => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>
        <div className="input-group" style={{ minWidth: 120 }}>
          <label className="input-label">الحالة</label>
          <select
            className="select"
            value={filter.status || ''}
            onChange={e => setFilter(prev => ({ ...prev, status: e.target.value as WorklistStatus | undefined }))}
          >
            <option value="">الكل</option>
            <option value="scheduled">مجدول</option>
            <option value="arrived">وصل</option>
            <option value="started">قيد الإجراء</option>
            <option value="completed">مكتمل</option>
            <option value="cancelled">ملغي</option>
          </select>
        </div>
        <div className="input-group" style={{ minWidth: 150 }}>
          <label className="input-label">المحطة</label>
          <input
            className="input"
            value={filter.station || ''}
            onChange={e => setFilter(prev => ({ ...prev, station: e.target.value }))}
            placeholder="اسم المحطة"
          />
        </div>
        <div className="input-group" style={{ minWidth: 150 }}>
          <label className="input-label">المريض</label>
          <input
            className="input"
            value={filter.patient_name || ''}
            onChange={e => setFilter(prev => ({ ...prev, patient_name: e.target.value }))}
            placeholder="بحث..."
          />
        </div>
        <button className="btn btn-ghost btn-sm" onClick={() => setFilter({})}>
          مسح الكل
        </button>
      </div>

      {/* Error */}
      {error && (
        <div style={{ padding: 12, backgroundColor: 'rgba(239,68,68,0.1)', border: '1px solid var(--border-danger)', borderRadius: 8, color: 'var(--text-danger)', fontSize: '0.875rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span>{error}</span>
          <button className="btn btn-sm btn-ghost" onClick={fetchWorklist}>إعادة</button>
        </div>
      )}

      {/* Worklist table */}
      <WorklistTable
        items={items}
        loading={loading}
        selectedId={selectedItem?.id}
        onSelect={handleSelectItem}
        onStatusChange={handleStatusChange}
      />

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          <button className="pagination-btn" disabled={page === 1} onClick={() => setPage(p => p - 1)}>‹</button>
          {Array.from({ length: Math.min(totalPages, 10) }, (_, i) => {
            let pageNum: number
            if (totalPages <= 10) {
              pageNum = i + 1
            } else if (page <= 5) {
              pageNum = i + 1
            } else if (page >= totalPages - 4) {
              pageNum = totalPages - 9 + i
            } else {
              pageNum = page - 5 + i
            }
            return (
              <button
                key={pageNum}
                className={`pagination-btn ${pageNum === page ? 'active' : ''}`}
                onClick={() => setPage(pageNum)}
              >
                {pageNum}
              </button>
            )
          })}
          <button className="pagination-btn" disabled={page === totalPages} onClick={() => setPage(p => p + 1)}>›</button>
        </div>
      )}

      {/* Item detail panel */}
      {selectedItem && (
        <div className="modal-overlay" onClick={() => setSelectedItem(null)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 640 }}>
            <div className="modal-header">
              <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>تفاصيل الفحص</h2>
              <button className="btn btn-ghost btn-sm" onClick={() => setSelectedItem(null)}>✕</button>
            </div>
            <div className="modal-body">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div style={{ gridColumn: '1 / -1', display: 'flex', gap: 8, alignItems: 'center' }}>
                  <span className={`badge ${
                    selectedItem.priority === 'stat' ? 'badge-danger' :
                    selectedItem.priority === 'urgent' ? 'badge-warning' : 'badge-info'
                  }`} style={{ fontSize: '0.85rem' }}>
                    {selectedItem.priority === 'stat' ? '🔴 طوارئ' :
                     selectedItem.priority === 'urgent' ? '🟡 عاجل' : '🔵 روتيني'}
                  </span>
                  <span className={`badge ${
                    selectedItem.status === 'completed' ? 'badge-success' :
                    selectedItem.status === 'started' ? 'badge-warning' :
                    selectedItem.status === 'arrived' ? 'badge-primary' :
                    selectedItem.status === 'scheduled' ? 'badge-info' : 'badge-neutral'
                  }`}>
                    {selectedItem.status === 'completed' ? 'مكتمل' :
                     selectedItem.status === 'started' ? 'قيد الإجراء' :
                     selectedItem.status === 'arrived' ? 'وصل' :
                     selectedItem.status === 'scheduled' ? 'مجدول' : 'ملغي'}
                  </span>
                </div>
                <div>
                  <label className="input-label">رقم الإحالة</label>
                  <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>{selectedItem.accession_number}</p>
                </div>
                <div>
                  <label className="input-label">المريض</label>
                  <p style={{ fontWeight: 500, fontSize: '1rem' }}>{selectedItem.patient_name}</p>
                </div>
                <div>
                  <label className="input-label">رقم المريض</label>
                  <p>{selectedItem.patient_id}</p>
                </div>
                <div>
                  <label className="input-label">العمر / الجنس</label>
                  <p>{selectedItem.patient_age} / {selectedItem.patient_sex === 'M' ? 'ذكر' : selectedItem.patient_sex === 'F' ? 'أنثى' : 'آخر'}</p>
                </div>
                <div>
                  <label className="input-label">تاريخ الميلاد</label>
                  <p>{selectedItem.patient_birth_date}</p>
                </div>
                <div style={{ gridColumn: '1 / -1' }}>
                  <label className="input-label">الفحص</label>
                  <p style={{ fontWeight: 500 }}>{selectedItem.procedure_description || selectedItem.study_description}</p>
                </div>
                <div>
                  <label className="input-label">الجهاز</label>
                  <p>{selectedItem.modality}</p>
                </div>
                <div>
                  <label className="input-label">المحطة</label>
                  <p>{selectedItem.scheduled_station} ({selectedItem.scheduled_aet})</p>
                </div>
                <div>
                  <label className="input-label">الموعد</label>
                  <p>{selectedItem.scheduled_date} {selectedItem.scheduled_time}</p>
                </div>
                <div>
                  <label className="input-label">المدة</label>
                  <p>{selectedItem.duration_minutes} دقيقة</p>
                </div>
                <div>
                  <label className="input-label">الطبيب المحول</label>
                  <p>{selectedItem.requesting_physician}</p>
                </div>
                <div>
                  <label className="input-label">القسم المحول</label>
                  <p>{selectedItem.requesting_department || '—'}</p>
                </div>
                {selectedItem.contrast_required && (
                  <div style={{ gridColumn: '1 / -1' }}>
                    <label className="input-label">الصبغة</label>
                    <p>{selectedItem.contrast_details || 'مطلوب صبغة'}</p>
                  </div>
                )}
                {selectedItem.notes && (
                  <div style={{ gridColumn: '1 / -1' }}>
                    <label className="input-label">ملاحظات</label>
                    <p>{selectedItem.notes}</p>
                  </div>
                )}
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setSelectedItem(null)}>إغلاق</button>
              {selectedItem.status !== 'completed' && selectedItem.status !== 'cancelled' && (
                <div style={{ display: 'flex', gap: 8 }}>
                  {selectedItem.status === 'scheduled' && (
                    <button className="btn btn-primary" onClick={() => { handleStatusChange(selectedItem.id, 'arrived'); setSelectedItem(null) }}>
                      تأكيد الوصول
                    </button>
                  )}
                  {selectedItem.status === 'arrived' && (
                    <button className="btn btn-warning" onClick={() => { handleStatusChange(selectedItem.id, 'started'); setSelectedItem(null) }}>
                      بدء الفحص
                    </button>
                  )}
                  {selectedItem.status === 'started' && (
                    <button className="btn btn-success" onClick={() => { handleStatusChange(selectedItem.id, 'completed'); setSelectedItem(null) }}>
                      إكمال الفحص
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
