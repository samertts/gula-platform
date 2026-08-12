import React, { useState } from 'react'

interface ReturnItem {
  id: string
  drug_name: string
  batch_number: string
  quantity: number
  reason: string
  type: 'return' | 'waste'
  condition?: string
  notes: string
  pharmacist: string
  witness: string
  date: string
  status: string
}

export default function Returns() {
  const [activeTab, setActiveTab] = useState<'new' | 'history'>('new')
  const [returnType, setReturnType] = useState<'return' | 'waste'>('return')
  const [showForm, setShowForm] = useState(false)
  const [returns, setReturns] = useState<ReturnItem[]>([])
  const [formData, setFormData] = useState({
    drug_code: '',
    drug_name: '',
    batch_number: '',
    quantity: 0,
    reason: '',
    condition: '',
    notes: '',
    pharmacist: 'د. أحمد السامرائي',
    witness: '',
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const newReturn: ReturnItem = {
      id: `ret-${Date.now()}`,
      drug_name: formData.drug_name,
      batch_number: formData.batch_number,
      quantity: formData.quantity,
      reason: formData.reason,
      type: returnType,
      condition: formData.condition,
      notes: formData.notes,
      pharmacist: formData.pharmacist,
      witness: formData.witness,
      date: new Date().toISOString(),
      status: 'pending',
    }
    setReturns((prev) => [newReturn, ...prev])
    setShowForm(false)
    setFormData({ drug_code: '', drug_name: '', batch_number: '', quantity: 0, reason: '', condition: '', notes: '', pharmacist: 'د. أحمد السامرائي', witness: '' })
  }

  const totalLossValue = returns
    .filter((r) => r.type === 'waste')
    .reduce((sum, r) => sum + r.quantity * 5000, 0)

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">مرتجعات وتوالف</h1>
          <p className="page-subtitle">إدارة مرتجعات المرضى والأدوية التالفة</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(true)}>
          + تسجيل جديد
        </button>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-icon" style={{ background: 'rgba(56,189,248,0.15)', color: '#38bdf8' }}>↩️</div>
          <div className="kpi-value">{returns.filter((r) => r.type === 'return').length}</div>
          <div className="kpi-label">المرتجعات</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{ background: 'rgba(239,68,68,0.15)', color: '#ef4444' }}>🗑️</div>
          <div className="kpi-value">{returns.filter((r) => r.type === 'waste').length}</div>
          <div className="kpi-label">التوالف</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{ background: 'rgba(245,158,11,0.15)', color: '#f59e0b' }}>💰</div>
          <div className="kpi-value">{totalLossValue.toLocaleString()} د.ع</div>
          <div className="kpi-label">قيمة التوالف</div>
        </div>
      </div>

      <div className="tabs">
        <button className={`tab ${activeTab === 'new' ? 'active' : ''}`} onClick={() => setActiveTab('new')}>
          📝 تسجيل جديد
        </button>
        <button className={`tab ${activeTab === 'history' ? 'active' : ''}`} onClick={() => setActiveTab('history')}>
          📋 السجل
        </button>
      </div>

      {activeTab === 'new' && (
        <div>
          {!showForm ? (
            <div className="grid-2">
              <div
                className="card"
                style={{ cursor: 'pointer', textAlign: 'center', padding: '2rem' }}
                onClick={() => { setReturnType('return'); setShowForm(true) }}
              >
                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>↩️</div>
                <h3 style={{ marginBottom: '0.5rem' }}>مرتجع من مريض</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                  أدوية تم إرجاعها من المرضى
                </p>
              </div>
              <div
                className="card"
                style={{ cursor: 'pointer', textAlign: 'center', padding: '2rem' }}
                onClick={() => { setReturnType('waste'); setShowForm(true) }}
              >
                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🗑️</div>
                <h3 style={{ marginBottom: '0.5rem' }}>تالف / هالك</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                  أدوية تالفة أو منتهية الصلاحية
                </p>
              </div>
            </div>
          ) : (
            <div className="card" style={{ maxWidth: '600px' }}>
              <div className="card-header">
                <h3 className="card-title">
                  {returnType === 'return' ? 'تسجيل مرتجع' : 'تسجيل تالف'}
                </h3>
                <span className={`badge ${returnType === 'return' ? 'badge-info' : 'badge-danger'}`}>
                  {returnType === 'return' ? 'مرتجع' : 'تالف'}
                </span>
              </div>
              <form onSubmit={handleSubmit}>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">اسم الدواء</label>
                    <input type="text" value={formData.drug_name} onChange={(e) => setFormData((p) => ({ ...p, drug_name: e.target.value }))} required />
                  </div>
                  <div className="form-group">
                    <label className="form-label">رقم الدفعة</label>
                    <input type="text" value={formData.batch_number} onChange={(e) => setFormData((p) => ({ ...p, batch_number: e.target.value }))} required />
                  </div>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">الكمية</label>
                    <input type="number" min={1} value={formData.quantity} onChange={(e) => setFormData((p) => ({ ...p, quantity: parseInt(e.target.value) || 0 }))} required />
                  </div>
                  <div className="form-group">
                    <label className="form-label">السبب</label>
                    <select value={formData.reason} onChange={(e) => setFormData((p) => ({ ...p, reason: e.target.value }))} required>
                      <option value="">اختر السبب...</option>
                      {returnType === 'return' ? (
                        <>
                          <option value="تغيير العلاج">تغيير العلاج</option>
                          <option value="توقف عن الاستخدام">توقف عن الاستخدام</option>
                          <option value="آثار جانبية">آثار جانبية</option>
                          <option value="وصفة خاطئة">وصفة خاطئة</option>
                          <option value="صرف زائد">صرف زائد</option>
                          <option value="وفاة المريض">وفاة المريض</option>
                        </>
                      ) : (
                        <>
                          <option value="انتهاء الصلاحية">انتهاء الصلاحية</option>
                          <option value="تلف في التخزين">تلف في التخزين</option>
                          <option value="كسر في العبوة">كسر في العبوة</option>
                          <option value="تغير اللون أو الرائحة">تغير اللون أو الرائحة</option>
                          <option value="سحب من السوق">سحب من السوق</option>
                        </>
                      )}
                    </select>
                  </div>
                </div>
                {returnType === 'return' && (
                  <div className="form-group">
                    <label className="form-label">حالة الدواء</label>
                    <select value={formData.condition} onChange={(e) => setFormData((p) => ({ ...p, condition: e.target.value }))}>
                      <option value="">اختر الحالة...</option>
                      <option value="مختوم">مختوم - لم يفتح</option>
                      <option value="مفتوح">مفتوح ولكن غير مستخدم</option>
                      <option value="مستخدم جزئياً">مستخدم جزئياً</option>
                      <option value="تالف">تالف</option>
                    </select>
                  </div>
                )}
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">الصيدلي</label>
                    <input type="text" value={formData.pharmacist} onChange={(e) => setFormData((p) => ({ ...p, pharmacist: e.target.value }))} required />
                  </div>
                  <div className="form-group">
                    <label className="form-label">الشاهد (مطلوب للتوالف)</label>
                    <input type="text" value={formData.witness} onChange={(e) => setFormData((p) => ({ ...p, witness: e.target.value }))} required={returnType === 'waste'} />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">ملاحظات</label>
                  <textarea value={formData.notes} onChange={(e) => setFormData((p) => ({ ...p, notes: e.target.value }))} rows={2} />
                </div>
                <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                  <button type="button" className="btn btn-secondary" onClick={() => setShowForm(false)}>إلغاء</button>
                  <button type="submit" className="btn btn-primary">تسجيل</button>
                </div>
              </form>
            </div>
          )}
        </div>
      )}

      {activeTab === 'history' && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">سجل المرتجعات والتوالف</h3>
            <span className="badge badge-info">{returns.length} عملية</span>
          </div>
          {returns.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📋</div>
              <h3>لا توجد عمليات مسجلة</h3>
              <p>سجل أول عملية مرتجع أو تالف</p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table role="grid" aria-label="سجل المرتجعات والتوالف">
                <thead>
                  <tr>
                    <th>التاريخ</th>
                    <th>النوع</th>
                    <th>الدواء</th>
                    <th>الدفعة</th>
                    <th>الكمية</th>
                    <th>السبب</th>
                    <th>الصيدلي</th>
                    <th>الشاهد</th>
                    <th>الحالة</th>
                  </tr>
                </thead>
                <tbody>
                  {returns.map((r) => (
                    <tr key={r.id}>
                      <td style={{ fontSize: '0.8rem' }}>{new Date(r.date).toLocaleString('ar-IQ')}</td>
                      <td>
                        <span className={`badge ${r.type === 'return' ? 'badge-info' : 'badge-danger'}`}>
                          {r.type === 'return' ? 'مرتجع' : 'تالف'}
                        </span>
                      </td>
                      <td style={{ fontWeight: 600 }}>{r.drug_name}</td>
                      <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{r.batch_number}</td>
                      <td style={{ fontWeight: 700 }}>{r.quantity}</td>
                      <td style={{ fontSize: '0.8rem' }}>{r.reason}</td>
                      <td style={{ fontSize: '0.8rem' }}>{r.pharmacist}</td>
                      <td style={{ fontSize: '0.8rem' }}>{r.witness || '-'}</td>
                      <td>
                        <span className={`badge ${r.status === 'completed' ? 'badge-success' : 'badge-warning'}`}>
                          {r.status === 'completed' ? 'مكتمل' : 'قيد الانتظار'}
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
    </div>
  )
}
