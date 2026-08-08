import React, { useState, useEffect } from 'react'
import { getPrescriptions, updatePrescriptionStatus, cancelPrescription } from '../services/prescriptions'
import type { Prescription } from '../services/prescriptions'

export default function Prescriptions() {
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [selectedPrescription, setSelectedPrescription] = useState<Prescription | null>(null)
  const [page, setPage] = useState(1)

  useEffect(() => {
    loadPrescriptions()
  }, [statusFilter, page])

  async function loadPrescriptions() {
    setLoading(true)
    try {
      const data = await getPrescriptions({
        status: statusFilter || undefined,
        page,
        page_size: 20,
      })
      setPrescriptions(data.prescriptions || [])
    } catch {
      setPrescriptions([])
    } finally {
      setLoading(false)
    }
  }

  async function handleStatusChange(id: string, status: string) {
    try {
      await updatePrescriptionStatus(id, status)
      loadPrescriptions()
      if (selectedPrescription?.id === id) {
        setSelectedPrescription((prev) => prev ? { ...prev, status: status as Prescription['status'] } : null)
      }
    } catch {
      // handle error
    }
  }

  async function handleCancel(id: string) {
    const reason = prompt('سبب الإلغاء:')
    if (reason) {
      try {
        await cancelPrescription(id, reason)
        loadPrescriptions()
        setSelectedPrescription(null)
      } catch {
        // handle error
      }
    }
  }

  const statusLabels: Record<string, string> = {
    pending: 'قيد الانتظار',
    verified: 'تم التحقق',
    in_progress: 'قيد الصرف',
    dispensed: 'تم الصرف',
    partially_dispensed: 'صرف جزئي',
    cancelled: 'ملغي',
    expired: 'منتهي',
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">الوصفات الطبية</h1>
          <p className="page-subtitle">إدارة ومعالجة الوصفات الطبية</p>
        </div>
        <button className="btn btn-primary" onClick={loadPrescriptions}>
          🔄 تحديث
        </button>
      </div>

      <div className="toolbar">
        <div className="search-box">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            placeholder="بحث برقم الوصفة أو اسم المريض..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="بحث في الوصفات"
          />
        </div>
        <div className="filter-group">
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
            aria-label="تصفية بالحالة"
          >
            <option value="">الجميع</option>
            <option value="pending">قيد الانتظار</option>
            <option value="verified">تم التحقق</option>
            <option value="in_progress">قيد الصرف</option>
            <option value="dispensed">تم الصرف</option>
            <option value="partially_dispensed">صرف جزئي</option>
            <option value="cancelled">ملغي</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <span className="spinner" />
        </div>
      ) : (
        <div className="grid-2" style={{ alignItems: 'start' }}>
          <div className="card">
            <div style={{ overflowX: 'auto' }}>
              <table role="grid" aria-label="قائمة الوصفات">
                <thead>
                  <tr>
                    <th>الرقم</th>
                    <th>المريض</th>
                    <th>الطبيب</th>
                    <th>التاريخ</th>
                    <th>الحالة</th>
                    <th>خيارات</th>
                  </tr>
                </thead>
                <tbody>
                  {prescriptions.length === 0 ? (
                    <tr>
                      <td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                        لا توجد وصفات طبية
                      </td>
                    </tr>
                  ) : (
                    prescriptions.map((rx) => (
                      <tr
                        key={rx.id}
                        onClick={() => setSelectedPrescription(rx)}
                        style={{
                          cursor: 'pointer',
                          background: selectedPrescription?.id === rx.id ? 'var(--bg-hover)' : undefined,
                        }}
                      >
                        <td style={{ fontFamily: 'monospace', fontSize: '0.8rem', fontWeight: 600 }}>
                          {rx.prescription_number}
                        </td>
                        <td>{rx.patient_name}</td>
                        <td style={{ fontSize: '0.85rem' }}>{rx.doctor_name}</td>
                        <td style={{ fontSize: '0.8rem' }}>
                          {new Date(rx.issue_date).toLocaleDateString('ar-IQ')}
                        </td>
                        <td>
                          <span className={`badge ${
                            rx.status === 'pending' || rx.status === 'in_progress' ? 'badge-warning' :
                            rx.status === 'verified' ? 'badge-info' :
                            rx.status === 'dispensed' ? 'badge-success' :
                            rx.status === 'cancelled' ? 'badge-danger' : 'badge-neutral'
                          }`}>
                            {statusLabels[rx.status] || rx.status}
                          </span>
                        </td>
                        <td>
                          <div style={{ display: 'flex', gap: '0.25rem' }}>
                            <button
                              className="btn btn-sm btn-primary"
                              onClick={(e) => {
                                e.stopPropagation()
                                window.location.href = '/pharmacy/dispensing'
                              }}
                            >
                              صرف
                            </button>
                            {rx.status !== 'cancelled' && rx.status !== 'dispensed' && (
                              <button
                                className="btn btn-sm btn-danger"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleCancel(rx.id)
                                }}
                              >
                                إلغاء
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {selectedPrescription ? (
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">
                  تفاصيل الوصفة {selectedPrescription.prescription_number}
                </h3>
                <span className={`badge ${
                  selectedPrescription.status === 'dispensed' ? 'badge-success' : 'badge-info'
                }`}>
                  {statusLabels[selectedPrescription.status]}
                </span>
              </div>

              <div className="grid-2" style={{ marginBottom: '1rem' }}>
                <div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>المريض</p>
                  <p style={{ fontWeight: 600 }}>{selectedPrescription.patient_name}</p>
                </div>
                <div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>تاريخ الميلاد</p>
                  <p style={{ fontWeight: 600 }}>{selectedPrescription.patient_dob ? new Date(selectedPrescription.patient_dob).toLocaleDateString('ar-IQ') : '-'}</p>
                </div>
                <div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>الطبيب</p>
                  <p style={{ fontWeight: 600 }}>{selectedPrescription.doctor_name}</p>
                </div>
                <div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>المنشأة</p>
                  <p style={{ fontWeight: 600 }}>{selectedPrescription.facility}</p>
                </div>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>الأدوية:</p>
                {selectedPrescription.items.map((item, idx) => (
                  <div
                    key={item.id}
                    style={{
                      padding: '0.5rem 0.75rem',
                      background: 'var(--bg-primary)',
                      borderRadius: 'var(--radius-md)',
                      marginBottom: '0.375rem',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <div>
                      <span style={{ fontWeight: 600 }}>{item.drug_name}</span>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginRight: '0.5rem' }}>
                        {item.strength} - {item.dosage_form}
                      </span>
                    </div>
                    <div>
                      <span>{item.dose} {item.dose_unit}</span>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginRight: '0.5rem' }}>
                        {item.frequency}
                      </span>
                      {item.is_controlled && <span className="badge badge-danger" style={{ marginRight: '0.5rem' }}>مخدر</span>}
                    </div>
                  </div>
                ))}
              </div>

              {selectedPrescription.notes && (
                <div style={{ marginBottom: '1rem' }}>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>ملاحظات:</p>
                  <p style={{ fontSize: '0.85rem', background: 'var(--bg-primary)', padding: '0.5rem', borderRadius: 'var(--radius-md)' }}>
                    {selectedPrescription.notes}
                  </p>
                </div>
              )}

              <div style={{ display: 'flex', gap: '0.75rem' }}>
                {selectedPrescription.status === 'pending' && (
                  <button className="btn btn-primary" onClick={() => handleStatusChange(selectedPrescription.id, 'verified')}>
                    ✓ تأكيد الوصفة
                  </button>
                )}
                {selectedPrescription.status === 'verified' && (
                  <button className="btn btn-success" onClick={() => window.location.href = '/pharmacy/dispensing'}>
                    💊 صرف
                  </button>
                )}
                {selectedPrescription.status !== 'cancelled' && selectedPrescription.status !== 'dispensed' && (
                  <button className="btn btn-danger" onClick={() => handleCancel(selectedPrescription.id)}>
                    ✕ إلغاء
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="card">
              <div className="empty-state">
                <div className="empty-icon">📋</div>
                <h3>اختر وصفة</h3>
                <p>انقر على وصفة لعرض التفاصيل</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
