import React, { useState } from 'react'

interface Intervention {
  id: string
  patient_name: string
  patient_id: string
  type: string
  drug: string
  issue: string
  recommendation: string
  pharmacist: string
  doctor: string
  status: string
  outcome: string
  date: string
}

export default function PharmaceuticalCare() {
  const [activeTab, setActiveTab] = useState<'interventions' | 'counseling' | 'monitoring'>('interventions')
  const [showForm, setShowForm] = useState(false)
  const [interventions, setInterventions] = useState<Intervention[]>([])
  const [formData, setFormData] = useState({
    patient_name: '',
    patient_id: '',
    type: '',
    drug: '',
    issue: '',
    recommendation: '',
    pharmacist: 'د. أحمد السامرائي',
    doctor: '',
    outcome: '',
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const intervention: Intervention = {
      id: `int-${Date.now()}`,
      ...formData,
      status: 'open',
      date: new Date().toISOString(),
    }
    setInterventions((prev) => [intervention, ...prev])
    setShowForm(false)
    setFormData({ patient_name: '', patient_id: '', type: '', drug: '', issue: '', recommendation: '', pharmacist: 'د. أحمد السامرائي', doctor: '', outcome: '' })
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">الرعاية الصيدلانية</h1>
          <p className="page-subtitle">التدخلات السريرية والإرشاد الدوائي</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(true)}>
          + تدخل سريري جديد
        </button>
      </div>

      <div className="tabs">
        <button className={`tab ${activeTab === 'interventions' ? 'active' : ''}`} onClick={() => setActiveTab('interventions')}>
          🩺 التدخلات السريرية
        </button>
        <button className={`tab ${activeTab === 'counseling' ? 'active' : ''}`} onClick={() => setActiveTab('counseling')}>
          💬 الإرشاد الدوائي
        </button>
        <button className={`tab ${activeTab === 'monitoring' ? 'active' : ''}`} onClick={() => setActiveTab('monitoring')}>
          📊 متابعة العلاج
        </button>
      </div>

      {activeTab === 'interventions' && (
        <div>
          <div className="kpi-grid">
            <div className="kpi-card">
              <div className="kpi-icon" style={{ background: 'rgba(59,130,246,0.15)', color: '#3b82f6' }}>🩺</div>
              <div className="kpi-value">{interventions.length}</div>
              <div className="kpi-label">إجمالي التدخلات</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-icon" style={{ background: 'rgba(34,197,94,0.15)', color: '#22c55e' }}>✅</div>
              <div className="kpi-value">{interventions.filter((i) => i.status === 'accepted').length}</div>
              <div className="kpi-label">مقبولة</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-icon" style={{ background: 'rgba(245,158,11,0.15)', color: '#f59e0b' }}>⏳</div>
              <div className="kpi-value">{interventions.filter((i) => i.status === 'open').length}</div>
              <div className="kpi-label">قيد الانتظار</div>
            </div>
          </div>

          {showForm && (
            <div className="card" style={{ maxWidth: '700px', marginBottom: '1rem' }}>
              <div className="card-header">
                <h3 className="card-title">تسجيل تدخل سريري</h3>
                <button className="btn btn-ghost btn-sm" onClick={() => setShowForm(false)}>✕</button>
              </div>
              <form onSubmit={handleSubmit}>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">اسم المريض</label>
                    <input type="text" value={formData.patient_name} onChange={(e) => setFormData((p) => ({ ...p, patient_name: e.target.value }))} required />
                  </div>
                  <div className="form-group">
                    <label className="form-label">رقم الملف</label>
                    <input type="text" value={formData.patient_id} onChange={(e) => setFormData((p) => ({ ...p, patient_id: e.target.value }))} />
                  </div>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">نوع التدخل</label>
                    <select value={formData.type} onChange={(e) => setFormData((p) => ({ ...p, type: e.target.value }))} required>
                      <option value="">اختر...</option>
                      <option value="تفاعل دوائي">تفاعل دوائي</option>
                      <option value="جرعة غير مناسبة">جرعة غير مناسبة</option>
                      <option value="دواء بديل">اقتراح دواء بديل</option>
                      <option value="حساسية دوائية">حساسية دوائية</option>
                      <option value="موانع استعمال">موانع استعمال</option>
                      <option value="تثقيف المريض">تثقيف المريض</option>
                      <option value="متابعة">متابعة علاجية</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">الدواء</label>
                    <input type="text" value={formData.drug} onChange={(e) => setFormData((p) => ({ ...p, drug: e.target.value }))} />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">المشكلة</label>
                  <textarea value={formData.issue} onChange={(e) => setFormData((p) => ({ ...p, issue: e.target.value }))} rows={2} required placeholder="وصف المشكلة..." />
                </div>
                <div className="form-group">
                  <label className="form-label">التوصية</label>
                  <textarea value={formData.recommendation} onChange={(e) => setFormData((p) => ({ ...p, recommendation: e.target.value }))} rows={2} required placeholder="التوصية العلاجية..." />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">الصيدلي</label>
                    <input type="text" value={formData.pharmacist} onChange={(e) => setFormData((p) => ({ ...p, pharmacist: e.target.value }))} required />
                  </div>
                  <div className="form-group">
                    <label className="form-label">الطبيب المعالج</label>
                    <input type="text" value={formData.doctor} onChange={(e) => setFormData((p) => ({ ...p, doctor: e.target.value }))} />
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                  <button type="button" className="btn btn-secondary" onClick={() => setShowForm(false)}>إلغاء</button>
                  <button type="submit" className="btn btn-primary">تسجيل التدخل</button>
                </div>
              </form>
            </div>
          )}

          <div className="card">
            {interventions.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">🩺</div>
                <h3>لا توجد تدخلات سريرية</h3>
                <p>سجل أول تدخل سريري لبدء متابعة الرعاية الصيدلانية</p>
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table role="grid" aria-label="التدخلات السريرية">
                  <thead>
                    <tr>
                      <th>التاريخ</th>
                      <th>المريض</th>
                      <th>النوع</th>
                      <th>الدواء</th>
                      <th>المشكلة</th>
                      <th>الصيدلي</th>
                      <th>الطبيب</th>
                      <th>الحالة</th>
                    </tr>
                  </thead>
                  <tbody>
                    {interventions.map((intv) => (
                      <tr key={intv.id}>
                        <td style={{ fontSize: '0.8rem' }}>{new Date(intv.date).toLocaleString('ar-IQ')}</td>
                        <td style={{ fontWeight: 600 }}>{intv.patient_name}</td>
                        <td>
                          <span className="badge badge-info">{intv.type}</span>
                        </td>
                        <td>{intv.drug}</td>
                        <td style={{ fontSize: '0.8rem', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis' }}>{intv.issue}</td>
                        <td style={{ fontSize: '0.8rem' }}>{intv.pharmacist}</td>
                        <td style={{ fontSize: '0.8rem' }}>{intv.doctor || '-'}</td>
                        <td>
                          <span className={`badge ${intv.status === 'accepted' ? 'badge-success' : intv.status === 'rejected' ? 'badge-danger' : 'badge-warning'}`}>
                            {intv.status === 'accepted' ? 'مقبول' : intv.status === 'rejected' ? 'مرفوض' : 'مفتوح'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'counseling' && (
        <div className="card">
          <div className="empty-state">
            <div className="empty-icon">💬</div>
            <h3>الإرشاد الدوائي</h3>
            <p>توثيق جلسات الإرشاد الدوائي للمرضى - قيد التطوير</p>
          </div>
        </div>
      )}

      {activeTab === 'monitoring' && (
        <div className="card">
          <div className="empty-state">
            <div className="empty-icon">📊</div>
            <h3>متابعة العلاج</h3>
            <p>متابعة فعالية العلاج والآثار الجانبية - قيد التطوير</p>
          </div>
        </div>
      )}
    </div>
  )
}
