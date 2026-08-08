import { useState } from 'react'

type ContrastReaction = 'none' | 'mild' | 'moderate' | 'severe'
type ContrastType = 'iodinated' | 'gadolinium' | 'ultrasound' | 'other'

type ContrastAdministration = {
  id: string
  patient_name: string
  patient_id: string
  study_description: string
  modality: string
  contrast_type: ContrastType
  contrast_name: string
  dose_ml: number
  concentration: string
  route: 'IV' | 'IA' | 'oral' | 'other'
  injection_rate: string
  injection_time: string
  lot_number: string
  expiration_date: string
  administrator: string
  reaction: ContrastReaction
  reaction_description: string
  treatment: string
  creatinine_before: number
  creatinine_after?: number
  egfr: number
  notes: string
  administered_at: string
}

const CONTRAST_HISTORY: ContrastAdministration[] = [
  {
    id: 'cont_001', patient_name: 'أحمد محمد', patient_id: 'MRN-001',
    study_description: 'CT البطن والحوض', modality: 'CT',
    contrast_type: 'iodinated', contrast_name: 'Iohexol 300', dose_ml: 100,
    concentration: '300 mgI/mL', route: 'IV', injection_rate: '3 mL/s',
    injection_time: '30s', lot_number: 'LOT-12345', expiration_date: '2026-12-31',
    administrator: 'د. سارة علي', reaction: 'none', reaction_description: '',
    treatment: '', creatinine_before: 0.9, egfr: 85, notes: '', administered_at: '2026-07-15 10:30'
  },
  {
    id: 'cont_002', patient_name: 'فاطمة حسن', patient_id: 'MRN-045',
    study_description: 'MRI الرأس', modality: 'MR',
    contrast_type: 'gadolinium', contrast_name: 'Gadovist 1.0', dose_ml: 7.5,
    concentration: '1 mmol/mL', route: 'IV', injection_rate: '2 mL/s',
    injection_time: '15s', lot_number: 'LOT-67890', expiration_date: '2026-11-30',
    administrator: 'د. أحمد محمود', reaction: 'mild', reaction_description: 'غثيان خفيف',
    treatment: 'مراقبة', creatinine_before: 0.8, egfr: 90, notes: 'تحسن بعد 5 دقائق',
    administered_at: '2026-07-14 14:00'
  }
]

export function ContrastTracking() {
  const [administrations] = useState<ContrastAdministration[]>(CONTRAST_HISTORY)
  const [selectedAdmin, setSelectedAdmin] = useState<ContrastAdministration | null>(null)
  const [showNewModal, setShowNewModal] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  const filtered = administrations.filter(a =>
    !searchQuery || a.patient_name.includes(searchQuery) || a.patient_id.includes(searchQuery)
  )

  const getReactionColor = (reaction: ContrastReaction) => {
    switch (reaction) {
      case 'none': return 'var(--accent-success)'
      case 'mild': return 'var(--accent-warning)'
      case 'moderate': return 'var(--accent-danger)'
      case 'severe': return 'var(--accent-danger)'
    }
  }

  const getReactionLabel = (reaction: ContrastReaction) => {
    switch (reaction) {
      case 'none': return 'لا يوجد'
      case 'mild': return 'خفيف'
      case 'moderate': return 'متوسط'
      case 'severe': return 'شديد'
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>تتبع الصبغة</h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-tertiary)' }}>تتبع ومتابعة استخدام مواد الصبغة</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowNewModal(true)}>+ تسجيل جديد</button>
      </div>

      {/* Stats */}
      <div className="grid grid-4">
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--accent-primary)' }}>{administrations.length}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>إجمالي</div>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--accent-success)' }}>{administrations.filter(a => a.reaction === 'none').length}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>بدون تفاعل</div>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--accent-warning)' }}>{administrations.filter(a => a.reaction === 'mild').length}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>تفاعل خفيف</div>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--accent-danger)' }}>{administrations.filter(a => a.reaction === 'moderate' || a.reaction === 'severe').length}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>تفاعل متوسط/شديد</div>
        </div>
      </div>

      {/* Search */}
      <div className="card">
        <input className="input" placeholder="بحث باسم المريض أو الرقم..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
      </div>

      {/* Table */}
      <div className="card" style={{ padding: 0, overflow: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>التاريخ</th>
              <th>المريض</th>
              <th>الفحص</th>
              <th>نوع الصبغة</th>
              <th>الجرعة</th>
              <th>الكرياتينين</th>
              <th>eGFR</th>
              <th>التفاعل</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-tertiary)' }}>
                  لا توجد سجلات
                </td>
              </tr>
            ) : (
              filtered.map(admin => (
                <tr key={admin.id} style={{ cursor: 'pointer' }} onClick={() => setSelectedAdmin(admin)}>
                  <td style={{ fontSize: '0.8rem', whiteSpace: 'nowrap' }}>{admin.administered_at}</td>
                  <td>
                    <div style={{ fontWeight: 500, fontSize: '0.875rem' }}>{admin.patient_name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>{admin.patient_id}</div>
                  </td>
                  <td style={{ fontSize: '0.8rem' }}>{admin.study_description}</td>
                  <td>
                    <span className="badge badge-info">{admin.contrast_name}</span>
                  </td>
                  <td style={{ fontSize: '0.8rem' }}>{admin.dose_ml} mL</td>
                  <td style={{ fontSize: '0.8rem' }}>{admin.creatinine_before} mg/dL</td>
                  <td style={{ fontSize: '0.8rem' }}>{admin.egfr}</td>
                  <td>
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 4,
                      padding: '2px 8px',
                      borderRadius: 12,
                      fontSize: '0.75rem',
                      backgroundColor: `${getReactionColor(admin.reaction)}20`,
                      color: getReactionColor(admin.reaction),
                      fontWeight: 500
                    }}>
                      <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: getReactionColor(admin.reaction) }} />
                      {getReactionLabel(admin.reaction)}
                    </span>
                  </td>
                  <td>
                    <button className="btn btn-sm btn-ghost">👁</button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Detail modal */}
      {selectedAdmin && (
        <div className="modal-overlay" onClick={() => setSelectedAdmin(null)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 600 }}>
            <div className="modal-header">
              <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>تفاصيل إعطاء الصبغة</h2>
              <button className="btn btn-ghost btn-sm" onClick={() => setSelectedAdmin(null)}>✕</button>
            </div>
            <div className="modal-body">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div>
                  <label className="input-label">المريض</label>
                  <p style={{ fontWeight: 500 }}>{selectedAdmin.patient_name}</p>
                </div>
                <div>
                  <label className="input-label">رقم المريض</label>
                  <p>{selectedAdmin.patient_id}</p>
                </div>
                <div>
                  <label className="input-label">الفحص</label>
                  <p>{selectedAdmin.study_description}</p>
                </div>
                <div>
                  <label className="input-label">الجهاز</label>
                  <p>{selectedAdmin.modality}</p>
                </div>
                <div>
                  <label className="input-label">نوع الصبغة</label>
                  <p>{selectedAdmin.contrast_name} ({selectedAdmin.concentration})</p>
                </div>
                <div>
                  <label className="input-label">الجرعة</label>
                  <p>{selectedAdmin.dose_ml} mL — {selectedAdmin.route === 'IV' ? 'وريدي' : selectedAdmin.route === 'IA' ? 'شرياني' : selectedAdmin.route === 'oral' ? 'فموي' : 'آخر'}</p>
                </div>
                <div>
                  <label className="input-label">معدل الحقن</label>
                  <p>{selectedAdmin.injection_rate}</p>
                </div>
                <div>
                  <label className="input-label">رقم الدفعة</label>
                  <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>{selectedAdmin.lot_number}</p>
                </div>
                <div>
                  <label className="input-label">الكرياتينين</label>
                  <p>{selectedAdmin.creatinine_before} mg/dL</p>
                </div>
                <div>
                  <label className="input-label">eGFR</label>
                  <p>{selectedAdmin.egfr} mL/min/1.73m²</p>
                </div>
                <div>
                  <label className="input-label">التفاعل</label>
                  <span style={{
                    padding: '2px 8px',
                    borderRadius: 12,
                    fontSize: '0.8rem',
                    backgroundColor: `${getReactionColor(selectedAdmin.reaction)}20`,
                    color: getReactionColor(selectedAdmin.reaction)
                  }}>
                    {getReactionLabel(selectedAdmin.reaction)}
                  </span>
                </div>
                <div>
                  <label className="input-label">المُعطي</label>
                  <p>{selectedAdmin.administrator}</p>
                </div>
              </div>
              {selectedAdmin.reaction !== 'none' && (
                <div style={{ marginTop: 16, padding: 12, backgroundColor: 'rgba(239,68,68,0.1)', borderRadius: 8 }}>
                  <label className="input-label" style={{ color: 'var(--text-danger)' }}>تفاصيل التفاعل</label>
                  <p>{selectedAdmin.reaction_description}</p>
                  <label className="input-label" style={{ marginTop: 8 }}>العلاج</label>
                  <p>{selectedAdmin.treatment || '—'}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* New record modal */}
      {showNewModal && (
        <div className="modal-overlay" onClick={() => setShowNewModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 600 }}>
            <div className="modal-header">
              <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>تسجيل صبغة جديد</h2>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowNewModal(false)}>✕</button>
            </div>
            <div className="modal-body">
              <p style={{ color: 'var(--text-tertiary)', textAlign: 'center' }}>
                نموذج تسجيل الصبغة سيكون متاحاً هنا
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
