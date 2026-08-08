import { useState, useCallback } from 'react'
import type { Modality } from '@services/dicom'

type OrderEntryData = {
  patient_id: string
  patient_name: string
  patient_birth_date: string
  patient_sex: 'M' | 'F' | 'O'
  patient_phone: string
  accession_number: string
  study_description: string
  procedure_code: string
  procedure_description: string
  modality: Modality
  body_part: string
  laterality: 'L' | 'R' | 'B' | 'N/A'
  priority: 'routine' | 'urgent' | 'stat'
  clinical_history: string
  requesting_physician: string
  requesting_department: string
  referring_physician_id: string
  diagnosis: string
  contrast_required: boolean
  contrast_details: string
  notes: string
  is_insured: boolean
  insurance_provider: string
}

type OrderEntryProps = {
  initialData?: Partial<OrderEntryData>
  onSubmit: (data: OrderEntryData) => void
  onCancel: () => void
  loading?: boolean
}

const MODALITIES: Modality[] = ['CT', 'MR', 'US', 'XA', 'CR', 'DX', 'MG', 'NM', 'PT']
const BODY_PARTS = [
  'الرأس', 'الرقبة', 'الصدر', 'البطن', 'الحوض', 'العمود الفقري',
  'الطرف العلوي', 'الطرف السفلي', 'المفاصل', 'الأوعية الدموية', 'الثدي', 'أخرى'
]
const PROCEDURES: Record<string, string[]> = {
  CT: ['CT الرأس', 'CT الصدر', 'CT البطن', 'CT الحوض', 'CT العمود الفقري', 'CT الأوعية', 'CT الطرف العلوي', 'CT الطرف السفلي'],
  MR: ['MRI الرأس', 'MRI الصدر', 'MRI البطن', 'MRI الحوض', 'MRI العمود الفقري', 'MRI المفصل', 'MRI الأوعية', 'MRI الطرف'],
  US: ['تلفزيون البطن', 'تلفزيون الحوض', 'تلفزيون الثدي', 'تلفزيون الغدة الدرقية', 'تلفزيون الأوعية', 'تلفزيون الطرف'],
  XA: ['تصوير الأوعية', 'قسطرة قلبية'],
  CR: ['صورة الصدر', 'صورة البطن', 'صورة الطرف', 'صورة العمود الفقري'],
  DX: ['صورة الصدر', 'صورة البطن', 'صورة الطرف', 'صورة العمود الفقري'],
  MG: [' mammogram', 'مموغرام الثدي', 'تصوير الثدي ثلاثي الأبعاد'],
  NM: ['مسح العظام', 'مسح القلب', 'مسح الغدة الدرقية', 'PET scan'],
  PT: ['PET/CT', 'PET/MRI']
}

const defaultData: OrderEntryData = {
  patient_id: '', patient_name: '', patient_birth_date: '', patient_sex: 'M',
  patient_phone: '', accession_number: '', study_description: '', procedure_code: '',
  procedure_description: '', modality: 'CT', body_part: '', laterality: 'N/A',
  priority: 'routine', clinical_history: '', requesting_physician: '',
  requesting_department: '', referring_physician_id: '', diagnosis: '',
  contrast_required: false, contrast_details: '', notes: '', is_insured: false,
  insurance_provider: ''
}

export function OrderEntry({ initialData, onSubmit, onCancel, loading = false }: OrderEntryProps) {
  const [form, setForm] = useState<OrderEntryData>({ ...defaultData, ...initialData })

  const handleChange = useCallback((field: keyof OrderEntryData, value: string | boolean) => {
    setForm(prev => ({ ...prev, [field]: value }))
  }, [])

  const handleModalityChange = useCallback((modality: Modality) => {
    setForm(prev => ({ ...prev, modality, procedure_code: '', procedure_description: '' }))
  }, [])

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(form)
  }, [form, onSubmit])

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">إدخال طلب فحص</h3>
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <fieldset style={{ border: '1px solid var(--border-primary)', borderRadius: 8, padding: 16 }}>
          <legend style={{ fontSize: '0.8rem', fontWeight: 600, padding: '0 8px', color: 'var(--text-secondary)' }}>
            بيانات المريض
          </legend>
          <div className="grid grid-2">
            <div className="input-group">
              <label className="input-label">اسم المريض *</label>
              <input className="input" value={form.patient_name} onChange={e => handleChange('patient_name', e.target.value)} required placeholder="الاسم الكامل" />
            </div>
            <div className="input-group">
              <label className="input-label">رقم المريض *</label>
              <input className="input" value={form.patient_id} onChange={e => handleChange('patient_id', e.target.value)} required placeholder="MRN" />
            </div>
            <div className="input-group">
              <label className="input-label">تاريخ الميلاد *</label>
              <input className="input" type="date" value={form.patient_birth_date} onChange={e => handleChange('patient_birth_date', e.target.value)} required />
            </div>
            <div className="input-group">
              <label className="input-label">الجنس *</label>
              <select className="select" value={form.patient_sex} onChange={e => handleChange('patient_sex', e.target.value)}>
                <option value="M">ذكر</option>
                <option value="F">أنثى</option>
                <option value="O">آخر</option>
              </select>
            </div>
            <div className="input-group">
              <label className="input-label">رقم الهاتف</label>
              <input className="input" type="tel" value={form.patient_phone} onChange={e => handleChange('patient_phone', e.target.value)} placeholder="رقم الجوال" />
            </div>
          </div>
        </fieldset>

        <fieldset style={{ border: '1px solid var(--border-primary)', borderRadius: 8, padding: 16 }}>
          <legend style={{ fontSize: '0.8rem', fontWeight: 600, padding: '0 8px', color: 'var(--text-secondary)' }}>
            بيانات الفحص
          </legend>
          <div className="grid grid-2">
            <div className="input-group">
              <label className="input-label">الجهاز (Modality) *</label>
              <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                {MODALITIES.map(m => (
                  <button
                    key={m}
                    type="button"
                    className={`btn btn-sm ${form.modality === m ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => handleModalityChange(m)}
                    style={{ padding: '4px 8px', minWidth: 36 }}
                  >
                    {m}
                  </button>
                ))}
              </div>
            </div>
            <div className="input-group">
              <label className="input-label">الفحص *</label>
              <select className="select" value={form.procedure_description} onChange={e => handleChange('procedure_description', e.target.value)} required>
                <option value="">اختر الفحص...</option>
                {(PROCEDURES[form.modality] || []).map(p => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
            <div className="input-group">
              <label className="input-label">الجزء التشريحي</label>
              <select className="select" value={form.body_part} onChange={e => handleChange('body_part', e.target.value)}>
                <option value="">اختر...</option>
                {BODY_PARTS.map(bp => (
                  <option key={bp} value={bp}>{bp}</option>
                ))}
              </select>
            </div>
            <div className="input-group">
              <label className="input-label">الجهة</label>
              <select className="select" value={form.laterality} onChange={e => handleChange('laterality', e.target.value)}>
                <option value="N/A">غير محدد</option>
                <option value="L">أيسر</option>
                <option value="R">أيمن</option>
                <option value="B">ثنائي</option>
              </select>
            </div>
            <div className="input-group">
              <label className="input-label">وصف الدراسة</label>
              <input className="input" value={form.study_description} onChange={e => handleChange('study_description', e.target.value)} placeholder="وصف مختصر" />
            </div>
            <div className="input-group">
              <label className="input-label">رقم الإحالة (Accession)</label>
              <input className="input" value={form.accession_number} onChange={e => handleChange('accession_number', e.target.value)} placeholder="Accession #" />
            </div>
          </div>
        </fieldset>

        <fieldset style={{ border: '1px solid var(--border-primary)', borderRadius: 8, padding: 16 }}>
          <legend style={{ fontSize: '0.8rem', fontWeight: 600, padding: '0 8px', color: 'var(--text-secondary)' }}>
            معلومات إضافية
          </legend>
          <div className="grid grid-2">
            <div className="input-group">
              <label className="input-label">الأولوية</label>
              <select className="select" value={form.priority} onChange={e => handleChange('priority', e.target.value)}>
                <option value="routine">روتيني</option>
                <option value="urgent">عاجل</option>
                <option value="stat">طوارئ</option>
              </select>
            </div>
            <div className="input-group">
              <label className="input-label">الطبيب المحول *</label>
              <input className="input" value={form.requesting_physician} onChange={e => handleChange('requesting_physician', e.target.value)} required placeholder="اسم الطبيب" />
            </div>
            <div className="input-group">
              <label className="input-label">القسم المحول</label>
              <input className="input" value={form.requesting_department} onChange={e => handleChange('requesting_department', e.target.value)} placeholder="القسم" />
            </div>
            <div className="input-group">
              <label className="input-label">التشخيص المبدئي</label>
              <input className="input" value={form.diagnosis} onChange={e => handleChange('diagnosis', e.target.value)} placeholder="التشخيص" />
            </div>
          </div>
          <div className="input-group mt-md">
            <label className="input-label">التاريخ السريري</label>
            <textarea className="input" value={form.clinical_history} onChange={e => handleChange('clinical_history', e.target.value)} rows={2} placeholder="ملخص التاريخ السريري..." />
          </div>
          <div className="flex items-center gap-md mt-md">
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
              <input type="checkbox" checked={form.contrast_required} onChange={e => handleChange('contrast_required', e.target.checked)} />
              <span style={{ fontSize: '0.875rem' }}>يتطلب صبغة</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
              <input type="checkbox" checked={form.is_insured} onChange={e => handleChange('is_insured', e.target.checked)} />
              <span style={{ fontSize: '0.875rem' }}>مؤمن</span>
            </label>
          </div>
          {form.contrast_required && (
            <div className="input-group mt-sm">
              <label className="input-label">تفاصيل الصبغة</label>
              <input className="input" value={form.contrast_details} onChange={e => handleChange('contrast_details', e.target.value)} placeholder="نوع وكمية الصبغة" />
            </div>
          )}
          <div className="input-group mt-md">
            <label className="input-label">ملاحظات</label>
            <textarea className="input" value={form.notes} onChange={e => handleChange('notes', e.target.value)} rows={2} placeholder="ملاحظات إضافية..." />
          </div>
        </fieldset>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          <button type="button" className="btn btn-secondary" onClick={onCancel}>إلغاء</button>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'جاري الإرسال...' : 'إرسال الطلب'}
          </button>
        </div>
      </form>
    </div>
  )
}
