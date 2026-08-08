import React, { useState, useEffect } from 'react'
import { getPrescriptions, getPrescription, dispensePrescription, searchPatients, getPatient, getPatientPrescriptions } from '../services/dispensing'
import { checkInteractions } from '../services/interactions'
import DispenseForm from '../components/DispenseForm'
import InteractionAlert from '../components/InteractionAlert'
import type { Prescription, Patient } from '../services/dispensing'
import type { InteractionCheckResult } from '../services/interactions'
import { savePendingDispense } from '../services/offline'

export default function Dispensing() {
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([])
  const [selectedPrescription, setSelectedPrescription] = useState<Prescription | null>(null)
  const [patientSearch, setPatientSearch] = useState('')
  const [patients, setPatients] = useState<Patient[]>([])
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null)
  const [patientPrescriptions, setPatientPrescriptions] = useState<Prescription[]>([])
  const [statusFilter, setStatusFilter] = useState('pending')
  const [loading, setLoading] = useState(true)
  const [interactionResult, setInteractionResult] = useState<InteractionCheckResult | null>(null)
  const [showInteractionAlert, setShowInteractionAlert] = useState(false)
  const [showBarcodeScan, setShowBarcodeScan] = useState(false)
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  const [message, setMessage] = useState<{ type: string; text: string } | null>(null)

  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  useEffect(() => {
    if (statusFilter) loadPrescriptions()
  }, [statusFilter])

  async function loadPrescriptions() {
    setLoading(true)
    try {
      const data = await getPrescriptions({ status: statusFilter, page_size: 50 })
      setPrescriptions(data.prescriptions || [])
    } catch {
      setPrescriptions([])
    } finally {
      setLoading(false)
    }
  }

  async function handlePatientSearch(query: string) {
    setPatientSearch(query)
    if (query.length < 3) {
      setPatients([])
      return
    }
    try {
      const data = await searchPatients(query)
      setPatients(data.patients || [])
    } catch {
      setPatients([])
    }
  }

  async function handleSelectPatient(patient: Patient) {
    setSelectedPatient(patient)
    setPatients([])
    setPatientSearch(patient.full_name)
    try {
      const data = await getPatientPrescriptions(patient.id)
      setPatientPrescriptions(data.prescriptions || [])
    } catch {
      setPatientPrescriptions([])
    }
  }

  async function handleSelectPrescription(prescription: Prescription) {
    setSelectedPrescription(prescription)
  }

  async function handleCheckInteractions(drugCodes: string[]) {
    try {
      const result = await checkInteractions(drugCodes, selectedPatient?.id)
      setInteractionResult(result)
      setShowInteractionAlert(true)
    } catch {
      setMessage({ type: 'error', text: 'فشل فحص التفاعلات' })
    }
  }

  async function handleDispense(data: { items: { inventory_id: string; quantity: number; batch_number: string }[]; notes: string }) {
    try {
      if (isOnline) {
        await dispensePrescription({
          prescription_id: selectedPrescription!.id,
          patient_id: selectedPrescription!.patient_id,
          pharmacist_id: 'current-user',
          items: data.items,
          notes: data.notes,
        })
        setMessage({ type: 'success', text: 'تم صرف الوصفة بنجاح' })
      } else {
        await savePendingDispense({
          prescription_id: selectedPrescription!.id,
          patient_id: selectedPrescription!.patient_id,
          items: data.items,
          notes: data.notes,
        })
        setMessage({ type: 'success', text: 'تم حفظ الصرف محلياً وسيتم المزامنة لاحقاً' })
      }
      setSelectedPrescription(null)
      loadPrescriptions()
    } catch (err) {
      setMessage({ type: 'error', text: err instanceof Error ? err.message : 'فشل الصرف' })
    }
  }

  function clearMessage() {
    setMessage(null)
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">صرف الأدوية</h1>
          <p className="page-subtitle">
            {isOnline ? (
              <span className="status-indicator">
                <span className="status-dot online" /> متصل
              </span>
            ) : (
              <span className="status-indicator">
                <span className="status-dot offline" /> غير متصل - وضع عدم الاتصال
              </span>
            )}
          </p>
        </div>
        <button className="btn btn-primary" onClick={loadPrescriptions}>
          🔄 تحديث
        </button>
      </div>

      {!isOnline && (
        <div className="offline-banner">
          📵 وضع عدم الاتصال - سيتم حفظ عمليات الصرف محلياً
        </div>
      )}

      {message && (
        <div className={`alert alert-${message.type}`} role="alert" style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>{message.text}</span>
          <button className="btn btn-ghost btn-sm" onClick={clearMessage}>✕</button>
        </div>
      )}

      {!selectedPrescription ? (
        <div className="grid-2">
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">بحث عن مريض</h3>
            </div>
            <div className="form-group">
              <label className="form-label">ابحث باسم المريض أو رقم الملف</label>
              <input
                type="text"
                value={patientSearch}
                onChange={(e) => handlePatientSearch(e.target.value)}
                placeholder="أدخل اسم المريض..."
                aria-label="بحث عن مريض"
              />
            </div>
            {patients.length > 0 && (
              <div style={{ marginTop: '0.5rem' }}>
                {patients.map((p) => (
                  <button
                    key={p.id}
                    style={{
                      width: '100%',
                      textAlign: 'right',
                      padding: '0.625rem',
                      background: selectedPatient?.id === p.id ? 'var(--bg-hover)' : 'transparent',
                      borderBottom: '1px solid var(--border-color)',
                      color: 'var(--text-primary)',
                    }}
                    onClick={() => handleSelectPatient(p)}
                  >
                    <div style={{ fontWeight: 600 }}>{p.full_name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      {p.patient_id} - {p.phone}
                    </div>
                  </button>
                ))}
              </div>
            )}
            {selectedPatient && (
              <div style={{ marginTop: '1rem', padding: '0.75rem', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
                <strong>{selectedPatient.full_name}</strong>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  رقم الملف: {selectedPatient.patient_id} | هاتف: {selectedPatient.phone}
                </div>
                {selectedPatient.allergies?.length > 0 && (
                  <div style={{ marginTop: '0.5rem' }}>
                    <span className="badge badge-danger">حساسية: {selectedPatient.allergies.join(', ')}</span>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="card">
            <div className="card-header">
              <h3 className="card-title">الوصفات الطبية</h3>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  aria-label="تصفية الحالة"
                  style={{ width: 'auto' }}
                >
                  <option value="pending">قيد الانتظار</option>
                  <option value="verified">تم التحقق</option>
                  <option value="in_progress">قيد الصرف</option>
                  <option value="dispensed">تم الصرف</option>
                </select>
              </div>
            </div>

            {loading ? (
              <div style={{ textAlign: 'center', padding: '2rem' }}>
                <span className="spinner" />
              </div>
            ) : (
              <div>
                {(selectedPatient ? patientPrescriptions : prescriptions).length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-icon">📋</div>
                    <p>لا توجد وصفات طبية</p>
                  </div>
                ) : (
                  (selectedPatient ? patientPrescriptions : prescriptions).map((rx) => (
                    <button
                      key={rx.id}
                      style={{
                        width: '100%',
                        textAlign: 'right',
                        padding: '0.75rem',
                        background: 'transparent',
                        borderBottom: '1px solid var(--border-color)',
                        color: 'var(--text-primary)',
                      }}
                      onClick={() => handleSelectPrescription(rx)}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <strong>{rx.prescription_number}</strong>
                        <span className={`badge ${
                          rx.status === 'pending' ? 'badge-warning' :
                          rx.status === 'verified' ? 'badge-info' :
                          rx.status === 'dispensed' ? 'badge-success' : 'badge-neutral'
                        }`}>
                          {rx.status === 'pending' ? 'قيد الانتظار' :
                           rx.status === 'verified' ? 'تم التحقق' :
                           rx.status === 'in_progress' ? 'قيد الصرف' :
                           rx.status === 'dispensed' ? 'تم الصرف' : rx.status}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                        {rx.patient_name} - د. {rx.doctor_name}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.125rem' }}>
                        {rx.items.length} أصناف - {new Date(rx.issue_date).toLocaleDateString('ar-IQ')}
                        {rx.is_controlled && <span className="badge badge-danger" style={{ marginRight: '0.5rem' }}>مخدر</span>}
                      </div>
                    </button>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div>
          {showInteractionAlert && interactionResult ? (
            <InteractionAlert
              interactions={interactionResult.interactions}
              allergies={interactionResult.allergies}
              foodInteractions={interactionResult.food_interactions}
              duplicateTherapy={interactionResult.duplicate_therapy}
              riskScore={interactionResult.risk_score}
              onAcknowledge={() => { setShowInteractionAlert(false) }}
              onCancel={() => { setSelectedPrescription(null); setShowInteractionAlert(false) }}
            />
          ) : (
            <DispenseForm
              prescription={selectedPrescription}
              onSubmit={handleDispense}
              onCancel={() => setSelectedPrescription(null)}
              onCheckInteractions={handleCheckInteractions}
            />
          )}
        </div>
      )}
    </div>
  )
}
