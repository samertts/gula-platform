import { useState } from 'react'

type QualityMetric = {
  id: string
  category: 'image_quality' | 'reporting' | 'safety' | 'timeliness' | 'patient_satisfaction'
  name: string
  description: string
  current: number
  target: number
  trend: 'up' | 'down' | 'stable'
  unit: string
  period: string
}

type QualityAudit = {
  id: string
  study_uid: string
  patient_name: string
  modality: string
  review_date: string
  reviewer: string
  image_quality_score: number
  report_quality_score: number
  technical_adequacy: 'adequate' | 'inadequate' | 'borderline'
  findings: string
  recommendations: string
  follow_up_required: boolean
}

type IncidentReport = {
  id: string
  date: string
  type: 'near_miss' | 'adverse_event' | 'device_malfunction' | 'protocol_deviation' | 'other'
  severity: 'low' | 'medium' | 'high' | 'critical'
  description: string
  patient_impact: string
  root_cause: string
  actions_taken: string
  status: 'open' | 'investigating' | 'resolved' | 'closed'
  reported_by: string
}

const METRICS: QualityMetric[] = [
  { id: 'm1', category: 'image_quality', name: 'جودة الصورة', description: 'نسبة الصور المقبولة تشخيصياً', current: 94.5, target: 95, trend: 'up', unit: '%', period: 'شهري' },
  { id: 'm2', category: 'reporting', name: 'وقت التقارير', description: 'متوسط وقت إصدار التقرير النهائي', current: 4.2, target: 6, trend: 'up', unit: 'ساعات', period: 'شهري' },
  { id: 'm3', category: 'safety', name: 'جرعة الإشعاع', description: 'نسبة الفحوصات ضمن حدود الجرعة الموصى بها', current: 98.2, target: 100, trend: 'stable', unit: '%', period: 'شهري' },
  { id: 'm4', category: 'timeliness', name: 'مواعيد الالتزام', description: 'نسبة المواعيد في الوقت المحدد', current: 87.3, target: 90, trend: 'down', unit: '%', period: 'شهري' },
  { id: 'm5', category: 'patient_satisfaction', name: 'رضا المرضى', description: 'متوسط تقييم رضا المرضى', current: 4.3, target: 4.5, trend: 'stable', unit: '/5', period: 'شهري' },
  { id: 'm6', category: 'reporting', name: 'إعادة العمل', description: 'نسبة الفحوصات المعاد إجراؤها', current: 2.1, target: 3, trend: 'down', unit: '%', period: 'شهري' }
]

const AUDITS: QualityAudit[] = [
  { id: 'audit_1', study_uid: '1.2.3.4.1', patient_name: 'أحمد محمد', modality: 'CT', review_date: '2026-07-15', reviewer: 'د. سارة علي', image_quality_score: 4, report_quality_score: 5, technical_adequacy: 'adequate', findings: 'جودة صورة ممتازة', recommendations: 'لا يوجد', follow_up_required: false },
  { id: 'audit_2', study_uid: '1.2.3.4.2', patient_name: 'فاطمة حسن', modality: 'MR', review_date: '2026-07-14', reviewer: 'د. خالد عمر', image_quality_score: 3, report_quality_score: 4, technical_adequacy: 'borderline', findings: 'حركة المريض أثرت على بعض الصور', recommendations: 'تكرار التسلسلات المتأثرة', follow_up_required: true }
]

const INCIDENTS: IncidentReport[] = [
  { id: 'inc_1', date: '2026-07-13', type: 'near_miss', severity: 'medium', description: 'تم تحديد هوية خاطئة للمريض قبل الفحص وتم التصحيح', patient_impact: 'لا يوجد تأثير', root_cause: 'عدم تطابق المعلومات عند التسجيل', actions_taken: 'تحديث إجراءات التحقق من الهوية', status: 'closed', reported_by: 'م. أحمد' },
  { id: 'inc_2', date: '2026-07-10', type: 'device_malfunction', severity: 'high', description: 'جهاز CT يظهر خطأ في أنبوب الأشعة', patient_impact: 'تأخير فحص مريض واحد', root_cause: 'تآكل الأنبوب', actions_taken: 'تم استبدال الأنبوب وجدولة الصيانة', status: 'resolved', reported_by: 'م. محمد' }
]

const CATEGORY_CONFIG: Record<string, { label: string; icon: string }> = {
  image_quality: { label: 'جودة الصورة', icon: '🖼️' },
  reporting: { label: 'التقارير', icon: '📝' },
  safety: { label: 'السلامة', icon: '🛡️' },
  timeliness: { label: 'الالتزام بالمواعيد', icon: '⏰' },
  patient_satisfaction: { label: 'رضا المرضى', icon: '😊' }
}

export function Quality() {
  const [activeTab, setActiveTab] = useState<'metrics' | 'audits' | 'incidents'>('metrics')
  const [metrics] = useState<QualityMetric[]>(METRICS)
  const [audits] = useState<QualityAudit[]>(AUDITS)
  const [incidents] = useState<IncidentReport[]>(INCIDENTS)
  const [selectedAudit, setSelectedAudit] = useState<QualityAudit | null>(null)

  const getTrendIcon = (trend: string, current: number, target: number) => {
    if (trend === 'up') return '🔼'
    if (trend === 'down') return '🔽'
    return '➡️'
  }

  const getMeetingTarget = (current: number, target: number) => current >= target

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>ضمان الجودة</h1>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-tertiary)' }}>مؤشرات الجودة ومراجعة الأداء في قسم الأشعة</p>
      </div>

      {/* Tabs */}
      <div className="tabs">
        <button className={`tab ${activeTab === 'metrics' ? 'active' : ''}`} onClick={() => setActiveTab('metrics')}>📊 المؤشرات</button>
        <button className={`tab ${activeTab === 'audits' ? 'active' : ''}`} onClick={() => setActiveTab('audits')}>🔍 المراجعات</button>
        <button className={`tab ${activeTab === 'incidents' ? 'active' : ''}`} onClick={() => setActiveTab('incidents')}>⚠️ الحوادث</button>
      </div>

      {activeTab === 'metrics' && (
        <>
          {/* Quality Score Overview */}
          <div className="card" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-tertiary)', marginBottom: 8 }}>مؤشر الجودة العام</div>
            <div style={{
              position: 'relative',
              width: 140,
              height: 140,
              margin: '0 auto'
            }}>
              <svg viewBox="0 0 36 36" style={{ width: 140, height: 140 }}>
                <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none" stroke="var(--bg-tertiary)" strokeWidth="3" />
                <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none" stroke="var(--accent-primary)" strokeWidth="3"
                  strokeDasharray={`${(metrics.filter(m => getMeetingTarget(m.current, m.target)).length / metrics.length) * 100}, 100`} />
                <text x="18" y="20" textAnchor="middle" fontSize="8" fill="var(--text-primary)" fontWeight="700">
                  {Math.round(metrics.filter(m => getMeetingTarget(m.current, m.target)).length / metrics.length * 100)}%
                </text>
              </svg>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: 8 }}>
              {metrics.filter(m => getMeetingTarget(m.current, m.target)).length} من {metrics.length} مؤشرات ضمن الهدف
            </div>
          </div>

          <div className="grid grid-2">
            {metrics.map(metric => (
              <div key={metric.id} className="card">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                  <div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
                      {CATEGORY_CONFIG[metric.category]?.icon} {CATEGORY_CONFIG[metric.category]?.label}
                    </span>
                    <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginTop: 4 }}>{metric.name}</h3>
                  </div>
                  <span style={{ fontSize: '1.5rem' }}>{getTrendIcon(metric.trend, metric.current, metric.target)}</span>
                </div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 12 }}>{metric.description}</p>
                <div style={{ display: 'flex', alignItems: 'flex-end', gap: 12 }}>
                  <div>
                    <span style={{
                      fontSize: '2rem',
                      fontWeight: 700,
                      color: getMeetingTarget(metric.current, metric.target) ? 'var(--accent-success)' : 'var(--accent-danger)'
                    }}>
                      {metric.current}
                    </span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginInlineStart: 4 }}>{metric.unit}</span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginBottom: 4 }}>
                    الهدف: {metric.target}{metric.unit}
                  </div>
                </div>
                <div style={{
                  width: '100%',
                  height: 8,
                  backgroundColor: 'var(--bg-tertiary)',
                  borderRadius: 4,
                  marginTop: 8,
                  overflow: 'hidden'
                }}>
                  <div style={{
                    width: `${Math.min(100, (metric.current / metric.target) * 100)}%`,
                    height: '100%',
                    backgroundColor: getMeetingTarget(metric.current, metric.target) ? 'var(--accent-success)' : 'var(--accent-warning)',
                    borderRadius: 4,
                    transition: 'width 500ms ease'
                  }} />
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {activeTab === 'audits' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button className="btn btn-primary">+ مراجعة جديدة</button>
          </div>
          <div className="card" style={{ padding: 0, overflow: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>التاريخ</th>
                  <th>المريض</th>
                  <th>الجهاز</th>
                  <th>جودة الصورة</th>
                  <th>جودة التقرير</th>
                  <th>الملاءمة</th>
                  <th>المراجع</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {audits.map(audit => (
                  <tr key={audit.id} style={{ cursor: 'pointer' }} onClick={() => setSelectedAudit(audit)}>
                    <td style={{ fontSize: '0.8rem' }}>{audit.review_date}</td>
                    <td style={{ fontWeight: 500, fontSize: '0.875rem' }}>{audit.patient_name}</td>
                    <td><span className="badge badge-primary">{audit.modality}</span></td>
                    <td>
                      <span style={{ display: 'flex', gap: 2 }}>
                        {[1, 2, 3, 4, 5].map(star => (
                          <span key={star} style={{ color: star <= audit.image_quality_score ? 'var(--accent-warning)' : 'var(--border-primary)' }}>
                            ★
                          </span>
                        ))}
                      </span>
                    </td>
                    <td>
                      <span style={{ display: 'flex', gap: 2 }}>
                        {[1, 2, 3, 4, 5].map(star => (
                          <span key={star} style={{ color: star <= audit.report_quality_score ? 'var(--accent-warning)' : 'var(--border-primary)' }}>
                            ★
                          </span>
                        ))}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${
                        audit.technical_adequacy === 'adequate' ? 'badge-success' :
                        audit.technical_adequacy === 'borderline' ? 'badge-warning' : 'badge-danger'
                      }`}>
                        {audit.technical_adequacy === 'adequate' ? 'ملائم' :
                         audit.technical_adequacy === 'borderline' ? 'حدودي' : 'غير ملائم'}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.8rem' }}>{audit.reviewer}</td>
                    <td><button className="btn btn-sm btn-ghost">👁</button></td>
                  </tr>
                ))}
                {audits.length === 0 && (
                  <tr><td colSpan={8} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-tertiary)' }}>لا توجد مراجعات</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {activeTab === 'incidents' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button className="btn btn-primary">+ بلاغ حادث</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {incidents.map(incident => (
              <div key={incident.id} className="card" style={{
                borderInlineStart: `4px solid ${
                  incident.severity === 'critical' ? 'var(--accent-danger)' :
                  incident.severity === 'high' ? 'var(--accent-danger)' :
                  incident.severity === 'medium' ? 'var(--accent-warning)' : 'var(--accent-info)'
                }`
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
                  <span className={`badge ${
                    incident.severity === 'critical' || incident.severity === 'high' ? 'badge-danger' :
                    incident.severity === 'medium' ? 'badge-warning' : 'badge-info'
                  }`}>
                    {incident.severity === 'critical' ? 'حرج' :
                     incident.severity === 'high' ? 'عالي' :
                     incident.severity === 'medium' ? 'متوسط' : 'منخفض'}
                  </span>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    {incident.type === 'near_miss' ? 'خطأ وشيك' :
                     incident.type === 'adverse_event' ? 'حدث عكسي' :
                     incident.type === 'device_malfunction' ? 'عطل جهاز' :
                     incident.type === 'protocol_deviation' ? 'انحراف بروتوكول' : 'آخر'}
                  </span>
                  <span className={`badge ${
                    incident.status === 'open' ? 'badge-danger' :
                    incident.status === 'investigating' ? 'badge-warning' :
                    incident.status === 'resolved' ? 'badge-info' : 'badge-success'
                  }`} style={{ marginInlineStart: 'auto' }}>
                    {incident.status === 'open' ? 'مفتوح' :
                     incident.status === 'investigating' ? 'قيد التحقيق' :
                     incident.status === 'resolved' ? 'تم الحل' : 'مغلق'}
                  </span>
                </div>
                <p style={{ fontWeight: 500, marginBottom: 4 }}>{incident.description}</p>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  {incident.date} — {incident.reported_by}
                </p>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Audit detail modal */}
      {selectedAudit && (
        <div className="modal-overlay" onClick={() => setSelectedAudit(null)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 500 }}>
            <div className="modal-header">
              <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>تفاصيل المراجعة</h2>
              <button className="btn btn-ghost btn-sm" onClick={() => setSelectedAudit(null)}>✕</button>
            </div>
            <div className="modal-body">
              <div style={{ display: 'grid', gap: 12 }}>
                <div>
                  <span className="badge badge-primary">{selectedAudit.modality}</span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div>
                    <label className="input-label">المريض</label>
                    <p>{selectedAudit.patient_name}</p>
                  </div>
                  <div>
                    <label className="input-label">المراجع</label>
                    <p>{selectedAudit.reviewer}</p>
                  </div>
                  <div>
                    <label className="input-label">جودة الصورة</label>
                    <p>{'★'.repeat(selectedAudit.image_quality_score)}{'☆'.repeat(5 - selectedAudit.image_quality_score)}</p>
                  </div>
                  <div>
                    <label className="input-label">جودة التقرير</label>
                    <p>{'★'.repeat(selectedAudit.report_quality_score)}{'☆'.repeat(5 - selectedAudit.report_quality_score)}</p>
                  </div>
                </div>
                <div>
                  <label className="input-label">الملاحظات</label>
                  <p>{selectedAudit.findings}</p>
                </div>
                <div>
                  <label className="input-label">التوصيات</label>
                  <p>{selectedAudit.recommendations}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
