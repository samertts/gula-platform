import { useState, useCallback } from 'react'

type ProtocolStep = {
  id: string
  order: number
  name: string
  description: string
  duration_minutes: number
  contrast: boolean
  contrast_volume?: string
  contrast_rate?: string
  instructions: string
  images_required: string
}

type Protocol = {
  id: string
  name: string
  code: string
  modality: string
  body_part: string
  description: string
  preparation: string
  contraindications: string
  steps: ProtocolStep[]
  contrast_default: boolean
  contrast_type: string
  contrast_max_dose: string
  radiation_dose: string
  is_active: boolean
  created_by: string
  created_at: string
  updated_at: string
}

const PROTOCOLS: Protocol[] = [
  {
    id: 'prot_001', name: 'CT الرأس بدون صبغة', code: 'CT_HEAD_NC', modality: 'CT',
    body_part: 'الرأس', description: 'فحص مقطعي للرأس بدون حقن صبغة', preparation: 'لا يوجد تحضير خاص',
    contraindications: 'الحمل', contrast_default: false, contrast_type: '', contrast_max_dose: '',
    radiation_dose: '2 mSv', is_active: true, created_by: 'د. أحمد', created_at: '2026-01-15', updated_at: '2026-03-01',
    steps: [
      { id: 'step_1', order: 1, name: 'مسح موضعي (Topogram)', description: 'مسح أولي لتحديد المنطقة', duration_minutes: 1, contrast: false, instructions: 'وضع المريض مستلقياً', images_required: '2 صور' },
      { id: 'step_2', order: 2, name: 'مسح محوري', description: 'مسح محوري للدماغ', duration_minutes: 5, contrast: false, instructions: 'من قاعدة الجمجمة إلى القمة', images_required: '30-40 صورة' },
      { id: 'step_3', order: 3, name: 'إعادة البناء', description: 'إعادة بناء الصور بالخوارزميات المناسبة', duration_minutes: 2, contrast: false, instructions: 'نافذة عظمية ونافذة نسيجية', images_required: 'جميع الصور' }
    ]
  },
  {
    id: 'prot_002', name: 'CT البطن والحوض مع صبغة', code: 'CT_ABD_PELVIS_C', modality: 'CT',
    body_part: 'البطن والحوض', description: 'فحص مقطعي للبطن والحوض مع حقن صبغة وريدي',
    preparation: 'صيام 4-6 ساعات', contraindications: 'حساسية اليود، الحمل، الفشل الكلوي',
    contrast_default: true, contrast_type: 'Iohexol 300 mgI/mL', contrast_max_dose: '100 mL',
    radiation_dose: '8 mSv', is_active: true, created_by: 'د. أحمد', created_at: '2026-01-15', updated_at: '2026-03-01',
    steps: [
      { id: 'step_2_1', order: 1, name: 'مسح موضعي', description: 'مسح أولي', duration_minutes: 1, contrast: false, instructions: 'وضع المريض مستلقياً', images_required: '2 صور' },
      { id: 'step_2_2', order: 2, name: 'مسح بدون صبغة', description: 'مسح أولي قبل الصبغة', duration_minutes: 5, contrast: false, instructions: 'من أعلى الحجاب الحاجز إلى الارتفاق العاني', images_required: '60-80 صورة' },
      { id: 'step_2_3', order: 3, name: 'حقن الصبغة', description: 'حقن الصبغة الوريدية', duration_minutes: 1, contrast: true, contrast_volume: '100 mL', contrast_rate: '3 mL/s', instructions: 'حقن تلقائي بمضخة', images_required: '—' },
      { id: 'step_2_4', order: 4, name: 'مسح شرياني', description: 'مسح في الطور الشرياني', duration_minutes: 5, contrast: true, instructions: 'تأخير 25-30 ثانية بعد الحقن', images_required: '60-80 صورة' },
      { id: 'step_2_5', order: 5, name: 'مسح وريدي', description: 'مسح في الطور الوريدي', duration_minutes: 5, contrast: true, instructions: 'تأخير 60-70 ثانية بعد الحقن', images_required: '60-80 صورة' },
      { id: 'step_2_6', order: 6, name: 'إعادة البناء', description: 'إعادة بناء الصور', duration_minutes: 3, contrast: false, instructions: 'نوافذ متعددة', images_required: 'جميع الصور' }
    ]
  },
  {
    id: 'prot_003', name: 'MRI الرأس مع صبغة', code: 'MRI_HEAD_C', modality: 'MR',
    body_part: 'الرأس', description: 'تصوير بالرنين المغناطيسي للرأس مع حقن صبغة',
    preparation: 'إزالة المعادن', contraindications: 'جهاز تنظيم ضربات القلب، زراعة القوقعة',
    contrast_default: true, contrast_type: 'Gadolinium-based', contrast_max_dose: '0.1 mmol/kg',
    radiation_dose: '0 mSv', is_active: true, created_by: 'د. سارة', created_at: '2026-02-10', updated_at: '2026-03-15',
    steps: [
      { id: 'step_3_1', order: 1, name: 'مسح محلي (Localizer)', description: 'تحديد الموضع', duration_minutes: 1, contrast: false, instructions: 'وضع المريض مستلقياً', images_required: '3 مستويات' },
      { id: 'step_3_2', order: 2, name: 'T1 Axial', description: 'T1 محوري', duration_minutes: 3, contrast: false, instructions: 'مسح مقطعي T1', images_required: '20-25 صورة' },
      { id: 'step_3_3', order: 3, name: 'T2 Axial', description: 'T2 محوري', duration_minutes: 3, contrast: false, instructions: 'مسح مقطعي T2', images_required: '20-25 صورة' },
      { id: 'step_3_4', order: 4, name: 'FLAIR', description: 'FLAIR محوري', duration_minutes: 3, contrast: false, instructions: 'مسح FLAIR', images_required: '20-25 صورة' },
      { id: 'step_3_5', order: 5, name: 'DWI', description: 'DWI مع ADC', duration_minutes: 2, contrast: false, instructions: 'مسح الانتشار', images_required: '20-25 صورة' },
      { id: 'step_3_6', order: 6, name: 'T1 +C Axial', description: 'T1 محوري بعد الصبغة', duration_minutes: 3, contrast: true, contrast_volume: 'حسب الوزن', instructions: 'بعد حقن الجادولينيوم', images_required: '20-25 صورة' }
    ]
  }
]

export function Protocols() {
  const [protocols] = useState<Protocol[]>(PROTOCOLS)
  const [selectedProtocol, setSelectedProtocol] = useState<Protocol | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [modalityFilter, setModalityFilter] = useState<string>('all')

  const filteredProtocols = protocols.filter(p => {
    if (modalityFilter !== 'all' && p.modality !== modalityFilter) return false
    if (searchQuery && !p.name.includes(searchQuery) && !p.code.includes(searchQuery)) return false
    return true
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>بروتوكولات الفحص</h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-tertiary)' }}>إدارة بروتوكولات فحوصات الأشعة</p>
        </div>
        <button className="btn btn-primary">+ بروتوكول جديد</button>
      </div>

      {/* Filters */}
      <div className="card" style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <input
          className="input"
          placeholder="بحث..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          style={{ flex: 1 }}
        />
        <select className="select" value={modalityFilter} onChange={e => setModalityFilter(e.target.value)} style={{ width: 120 }}>
          <option value="all">الكل</option>
          <option value="CT">CT</option>
          <option value="MR">MR</option>
          <option value="US">US</option>
        </select>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, alignItems: 'start' }}>
        {/* Protocols list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {filteredProtocols.map(protocol => (
            <div
              key={protocol.id}
              className="card"
              style={{
                cursor: 'pointer',
                borderColor: selectedProtocol?.id === protocol.id ? 'var(--accent-primary)' : undefined
              }}
              onClick={() => setSelectedProtocol(protocol)}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <span className={`badge ${protocol.modality === 'CT' ? 'badge-primary' : protocol.modality === 'MR' ? 'badge-secondary' : 'badge-info'}`}>
                  {protocol.modality}
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                  {protocol.code}
                </span>
              </div>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: 4 }}>{protocol.name}</h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{protocol.description}</p>
              <div style={{ display: 'flex', gap: 12, marginTop: 8, fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
                <span>{protocol.steps.length} خطوات</span>
                <span>جرعة: {protocol.radiation_dose}</span>
                <span style={{ color: protocol.is_active ? 'var(--text-success)' : 'var(--text-danger)' }}>
                  {protocol.is_active ? 'نشط' : 'غير نشط'}
                </span>
              </div>
            </div>
          ))}
          {filteredProtocols.length === 0 && (
            <div className="card empty-state">
              <p>لا توجد بروتوكولات</p>
            </div>
          )}
        </div>

        {/* Protocol details */}
        {selectedProtocol ? (
          <div className="card">
            <div className="card-header">
              <h3 className="card-title" style={{ fontSize: '1rem' }}>{selectedProtocol.name}</h3>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn btn-sm btn-primary">✏️ تعديل</button>
                <button className="btn btn-sm btn-secondary">📋 نسخ</button>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div className="grid grid-2">
                <div>
                  <label className="input-label">الكود</label>
                  <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>{selectedProtocol.code}</p>
                </div>
                <div>
                  <label className="input-label">الجهاز</label>
                  <span className="badge badge-primary">{selectedProtocol.modality}</span>
                </div>
                <div>
                  <label className="input-label">الجزء التشريحي</label>
                  <p>{selectedProtocol.body_part}</p>
                </div>
                <div>
                  <label className="input-label">الجرعة الإشعاعية</label>
                  <p>{selectedProtocol.radiation_dose}</p>
                </div>
              </div>

              <div>
                <label className="input-label">التحضير</label>
                <p style={{ fontSize: '0.85rem' }}>{selectedProtocol.preparation}</p>
              </div>

              <div>
                <label className="input-label">موانع الاستعمال</label>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-danger)' }}>{selectedProtocol.contraindications}</p>
              </div>

              {selectedProtocol.contrast_default && (
                <div className="grid grid-2" style={{ padding: 12, backgroundColor: 'rgba(245,158,11,0.1)', borderRadius: 8 }}>
                  <div>
                    <label className="input-label">نوع الصبغة</label>
                    <p>{selectedProtocol.contrast_type}</p>
                  </div>
                  <div>
                    <label className="input-label">الجرعة القصوى</label>
                    <p>{selectedProtocol.contrast_max_dose}</p>
                  </div>
                </div>
              )}

              <div>
                <label className="input-label">خطوات الفحص</label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 8 }}>
                  {selectedProtocol.steps.map(step => (
                    <div key={step.id} style={{
                      padding: 12,
                      backgroundColor: step.contrast ? 'rgba(245,158,11,0.1)' : 'var(--bg-tertiary)',
                      borderRadius: 8,
                      borderInlineStart: `3px solid ${step.contrast ? 'var(--accent-warning)' : 'var(--accent-primary)'}`
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                        <span style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          width: 24,
                          height: 24,
                          borderRadius: '50%',
                          backgroundColor: 'var(--accent-primary)',
                          color: 'white',
                          fontSize: '0.75rem',
                          fontWeight: 700
                        }}>
                          {step.order}
                        </span>
                        <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{step.name}</span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
                          ⏱ {step.duration_minutes} د
                        </span>
                        {step.contrast && (
                          <span className="badge badge-warning" style={{ fontSize: '0.65rem' }}>صبغة</span>
                        )}
                      </div>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{step.description}</p>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginTop: 4 }}>
                        {step.instructions} — {step.images_required}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="card empty-state">
            <div className="empty-state-icon">📋</div>
            <p>اختر بروتوكولاً لعرض التفاصيل</p>
          </div>
        )}
      </div>
    </div>
  )
}
