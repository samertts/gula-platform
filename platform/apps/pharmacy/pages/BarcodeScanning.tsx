import React, { useState } from 'react'
import BarcodeVerification from '../components/BarcodeVerification'
import type { VerificationResult } from '../components/BarcodeVerification'

export default function BarcodeScanning() {
  const [activeTab, setActiveTab] = useState<'verify' | 'scan-inventory' | 'history'>('verify')
  const [showVerification, setShowVerification] = useState(false)
  const [recentScans, setRecentScans] = useState<{ time: string; result: VerificationResult; patientName?: string; drugName?: string }[]>([])

  function handleVerified(result: VerificationResult) {
    setRecentScans((prev) => [
      {
        time: new Date().toLocaleString('ar-IQ'),
        result,
        patientName: 'مريض عينة',
        drugName: 'محاكاة دواء',
      },
      ...prev.slice(0, 49),
    ])
    setShowVerification(false)
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">المسح بالباركود</h1>
          <p className="page-subtitle">التحقق بالباركود - الحقوق الخمسة</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowVerification(true)}>
          📷 بدء المسح
        </button>
      </div>

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'verify' ? 'active' : ''}`}
          onClick={() => setActiveTab('verify')}
        >
          ✅ التحقق من الصرف
        </button>
        <button
          className={`tab ${activeTab === 'scan-inventory' ? 'active' : ''}`}
          onClick={() => setActiveTab('scan-inventory')}
        >
          📦 مسح المخزون
        </button>
        <button
          className={`tab ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          📋 سجل المسح
        </button>
      </div>

      {activeTab === 'verify' && (
        <div className="grid-2" style={{ alignItems: 'start' }}>
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">التحقق من الصرف</h3>
            </div>
            <div className="form-group">
              <label className="form-label">رقم الوصفة</label>
              <input type="text" placeholder="أدخل رقم الوصفة..." />
            </div>
            <div className="form-group">
              <label className="form-label">معرف المريض</label>
              <input type="text" placeholder="أدخل رقم الملف..." />
            </div>
            <div className="form-group">
              <label className="form-label">الدواء</label>
              <input type="text" placeholder="اختر الدواء..." />
            </div>
            <button className="btn btn-primary btn-lg" style={{ width: '100%' }} onClick={() => setShowVerification(true)}>
              📷 مسح الباركود والتحقق
            </button>
          </div>

          <div className="card">
            <div className="card-header">
              <h3 className="card-title">الحقوق الخمسة للدواء</h3>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {[
                { right: 'المريض الصحيح', desc: 'تطابق الباركود مع هوية المريض', icon: '👤' },
                { right: 'الدواء الصحيح', desc: 'مطابقة الدواء مع الوصفة الطبية', icon: '💊' },
                { right: 'الجرعة الصحيحة', desc: 'الجرعة الموصوفة تطابق الجرعة المصروفة', icon: '⚖️' },
                { right: 'الطريق الصحيح', desc: 'طريق الإعطاء الصحيح (فموي، وريدي...)', icon: '🔄' },
                { right: 'الوقت الصحيح', desc: 'الوقت المناسب للإعطاء', icon: '⏰' },
              ].map((item) => (
                <div
                  key={item.right}
                  style={{
                    display: 'flex',
                    gap: '0.75rem',
                    padding: '0.75rem',
                    background: 'var(--bg-primary)',
                    borderRadius: 'var(--radius-md)',
                    alignItems: 'center',
                  }}
                >
                  <span style={{ fontSize: '1.5rem' }}>{item.icon}</span>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.875rem' }}>{item.right}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{item.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'scan-inventory' && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">مسح المخزون</h3>
          </div>
          <div className="empty-state">
            <div className="empty-icon">📦</div>
            <h3>مسح باركود المخزون</h3>
            <p>قم بتوجيه الماسح نحو باركود الصنف لتحديث المخزون</p>
          </div>
          <div style={{ maxWidth: '400px', margin: '0 auto' }}>
            <div className="form-group">
              <label className="form-label">باركود الصنف</label>
              <input type="text" placeholder="انتظار المسح..." autoFocus />
            </div>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button className="btn btn-primary">🔍 بحث</button>
              <button className="btn btn-secondary">📷 مسح</button>
            </div>
          </div>
          <div style={{ marginTop: '1.5rem' }}>
            <h4 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>آخر المسوحات:</h4>
            <div className="empty-state">
              <p style={{ fontSize: '0.8rem' }}>لم يتم مسح أي صنف بعد</p>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'history' && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">سجل المسح</h3>
            <span className="badge badge-info">{recentScans.length} عملية</span>
          </div>

          {recentScans.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📋</div>
              <h3>لا توجد عمليات مسح</h3>
              <p>سيتم عرض عمليات المسح هنا</p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table role="grid" aria-label="سجل المسح">
                <thead>
                  <tr>
                    <th>الوقت</th>
                    <th>المريض</th>
                    <th>الدواء</th>
                    <th>المريض ✓</th>
                    <th>الدواء ✓</th>
                    <th>الجرعة ✓</th>
                    <th>الطريق ✓</th>
                    <th>النتيجة</th>
                  </tr>
                </thead>
                <tbody>
                  {recentScans.map((scan, idx) => (
                    <tr key={idx}>
                      <td style={{ fontSize: '0.8rem' }}>{scan.time}</td>
                      <td>{scan.patientName}</td>
                      <td>{scan.drugName}</td>
                      <td style={{ textAlign: 'center' }}>{scan.result.patient_match ? '✅' : '❌'}</td>
                      <td style={{ textAlign: 'center' }}>{scan.result.drug_match ? '✅' : '❌'}</td>
                      <td style={{ textAlign: 'center' }}>{scan.result.dose_match ? '✅' : '❌'}</td>
                      <td style={{ textAlign: 'center' }}>{scan.result.route_match ? '✅' : '❌'}</td>
                      <td>
                        <span className={`badge ${scan.result.all_match ? 'badge-success' : 'badge-danger'}`}>
                          {scan.result.all_match ? 'مقبول' : 'مرفوض'}
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

      {showVerification && (
        <BarcodeVerification
          expectedPatient="مريض عينة"
          expectedDrug="محاكاة دواء"
          expectedDose="500mg"
          expectedRoute="PO"
          patientName="مريض عينة"
          drugName="محاكاة دواء"
          onVerified={handleVerified}
          onCancel={() => setShowVerification(false)}
        />
      )}
    </div>
  )
}
