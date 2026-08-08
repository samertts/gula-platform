import { useState, useCallback } from 'react'

type ShareTarget = 'email' | 'link' | 'pacs' | 'cd' | 'portal'
type ShareStatus = 'pending' | 'sent' | 'failed' | 'expired'

type ShareRecord = {
  id: string
  study_uid: string
  patient_name: string
  study_description: string
  modality: string
  target_type: ShareTarget
  target_address: string
  status: ShareStatus
  shared_at: string
  expires_at?: string
  accessed_count: number
  notes: string
}

const SHARE_TARGET_CONFIG: Record<ShareTarget, { label: string; icon: string }> = {
  email: { label: 'بريد إلكتروني', icon: '📧' },
  link: { label: 'رابط آمن', icon: '🔗' },
  pacs: { label: 'PACS خارجي', icon: '🖥️' },
  cd: { label: 'CD/DVD', icon: '💿' },
  portal: { label: 'بوابة المريض', icon: '🚪' }
}

const SHARE_HISTORY: ShareRecord[] = [
  { id: 'share_1', study_uid: '1.2.3.4.1', patient_name: 'أحمد محمد', study_description: 'CT الصدر', modality: 'CT', target_type: 'email', target_address: 'dr.ahmed@hospital.com', status: 'sent', shared_at: '2026-07-15 10:30', expires_at: '2026-08-15', accessed_count: 3, notes: '' },
  { id: 'share_2', study_uid: '1.2.3.4.2', patient_name: 'سارة علي', study_description: 'MRI الرأس', modality: 'MR', target_type: 'link', target_address: 'https://share.gula.health/view/abc123', status: 'sent', shared_at: '2026-07-14 14:00', accessed_count: 1, notes: 'مشاركة مع طبيب الأعصاب' },
  { id: 'share_3', study_uid: '1.2.3.4.3', patient_name: 'خالد عمر', study_description: 'US البطن', modality: 'US', target_type: 'portal', target_address: 'patient@gula.health', status: 'pending', shared_at: '2026-07-16 09:00', accessed_count: 0, notes: '' }
]

export function ImageSharing() {
  const [shares, setShares] = useState<ShareRecord[]>(SHARE_HISTORY)
  const [showShareModal, setShowShareModal] = useState(false)
  const [activeTab, setActiveTab] = useState<'all' | 'sent' | 'pending' | 'expired'>('all')

  const filteredShares = shares.filter(s => {
    if (activeTab === 'all') return true
    return s.status === activeTab
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>مشاركة الصور</h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-tertiary)' }}>مشاركة وتوزيع صور الأشعة بشكل آمن</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowShareModal(true)}>
          + مشاركة جديدة
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-4">
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--accent-primary)' }}>{shares.length}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>إجمالي المشاركات</div>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--accent-success)' }}>{shares.filter(s => s.status === 'sent').length}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>مرسلة</div>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--accent-warning)' }}>{shares.filter(s => s.status === 'pending').length}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>قيد الإرسال</div>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--accent-danger)' }}>{shares.filter(s => s.status === 'expired').length}</div>
          <div           style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>منتهية الصلاحية</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        <button className={`tab ${activeTab === 'all' ? 'active' : ''}`} onClick={() => setActiveTab('all')}>الكل</button>
        <button className={`tab ${activeTab === 'sent' ? 'active' : ''}`} onClick={() => setActiveTab('sent')}>مرسلة</button>
        <button className={`tab ${activeTab === 'pending' ? 'active' : ''}`} onClick={() => setActiveTab('pending')}>قيد الإرسال</button>
        <button className={`tab ${activeTab === 'expired' ? 'active' : ''}`} onClick={() => setActiveTab('expired')}>منتهية</button>
      </div>

      {/* Share history table */}
      <div className="card" style={{ padding: 0, overflow: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>الحالة</th>
              <th>المريض</th>
              <th>الدراسة</th>
              <th>طريقة المشاركة</th>
              <th>الجهة المستقبلة</th>
              <th>تاريخ المشاركة</th>
              <th>الوصول</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {filteredShares.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-tertiary)' }}>
                  لا توجد مشاركات
                </td>
              </tr>
            ) : (
              filteredShares.map(share => (
                <tr key={share.id}>
                  <td>
                    <span className={`badge ${
                      share.status === 'sent' ? 'badge-success' :
                      share.status === 'pending' ? 'badge-warning' :
                      share.status === 'expired' ? 'badge-neutral' : 'badge-danger'
                    }`}>
                      {share.status === 'sent' ? 'مرسل' :
                       share.status === 'pending' ? 'قيد الإرسال' :
                       share.status === 'expired' ? 'منتهي' : 'فشل'}
                    </span>
                  </td>
                  <td style={{ fontWeight: 500, fontSize: '0.875rem' }}>{share.patient_name}</td>
                  <td style={{ fontSize: '0.8rem' }}>{share.study_description}</td>
                  <td>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      {SHARE_TARGET_CONFIG[share.target_type]?.icon}
                      {SHARE_TARGET_CONFIG[share.target_type]?.label}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.8rem', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {share.target_address}
                  </td>
                  <td style={{ fontSize: '0.8rem', whiteSpace: 'nowrap' }}>{share.shared_at}</td>
                  <td style={{ textAlign: 'center' }}>
                    <span className="badge badge-info">{share.accessed_count}</span>
                  </td>
                  <td>
                    <button className="btn btn-sm btn-ghost" title="عرض التفاصيل">
                      👁
                    </button>
                    {share.status === 'sent' && (
                      <button className="btn btn-sm btn-ghost" title="إلغاء المشاركة">
                        ✕
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Share modal */}
      {showShareModal && (
        <div className="modal-overlay" onClick={() => setShowShareModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 600 }}>
            <div className="modal-header">
              <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>مشاركة جديدة</h2>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowShareModal(false)}>✕</button>
            </div>
            <div className="modal-body">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div className="input-group">
                  <label className="input-label">الدراسة</label>
                  <select className="select">
                    <option value="">اختر دراسة...</option>
                    <option value="1">أحمد محمد — CT الصدر (2026-07-15)</option>
                    <option value="2">سارة علي — MRI الرأس (2026-07-14)</option>
                    <option value="3">خالد عمر — US البطن (2026-07-16)</option>
                  </select>
                </div>

                <div className="input-group">
                  <label className="input-label">طريقة المشاركة</label>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 8 }}>
                    {(Object.entries(SHARE_TARGET_CONFIG) as [ShareTarget, typeof SHARE_TARGET_CONFIG[ShareTarget]][]).map(([key, config]) => (
                      <button key={key} className="btn btn-secondary" style={{ flexDirection: 'column', gap: 4, padding: '12px 8px', fontSize: '0.75rem' }}>
                        <span style={{ fontSize: '1.5rem' }}>{config.icon}</span>
                        {config.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="input-group">
                  <label className="input-label">البريد الإلكتروني / الرابط</label>
                  <input className="input" placeholder="أدخل البريد الإلكتروني للمستلم" />
                </div>

                <div className="input-group">
                  <label className="input-label">صلاحية الرابط</label>
                  <select className="select">
                    <option value="24h">24 ساعة</option>
                    <option value="7d">7 أيام</option>
                    <option value="30d">30 يوماً</option>
                    <option value="never">بدون انتهاء</option>
                  </select>
                </div>

                <div className="input-group">
                  <label className="input-label">ملاحظات</label>
                  <textarea className="input" rows={2} placeholder="ملاحظات للمستلم..." />
                </div>

                <div className="flex gap-sm">
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: '0.85rem' }}>
                    <input type="checkbox" /> إدراج التقرير مع الصور
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: '0.85rem' }}>
                    <input type="checkbox" defaultChecked /> حماية بكلمة مرور
                  </label>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowShareModal(false)}>إلغاء</button>
              <button className="btn btn-primary">إرسال</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
