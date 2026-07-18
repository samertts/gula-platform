import { useState, useCallback, useEffect } from 'react'
import type { RadiologyReport, ReportFinding, ReportTemplate, RadsScore } from '@services/reporting'

const RADS_SCORES: { value: RadsScore; label: string; system: string }[] = [
  { value: 'NONE', label: 'لا يوجد', system: '-' },
  { value: 'RADS-1', label: 'RADS 1 - سلبي', system: 'RADS' },
  { value: 'RADS-2', label: 'RADS 2 - حميد', system: 'RADS' },
  { value: 'RADS-3', label: 'RADS 3 - محتمل حميد', system: 'RADS' },
  { value: 'RADS-4', label: 'RADS 4 - مشبوه', system: 'RADS' },
  { value: 'RADS-5', label: 'RADS 5 - خبيث', system: 'RADS' },
  { value: 'BI-RADS-0', label: 'BI-RADS 0 - غير مكتمل', system: 'BI-RADS' },
  { value: 'BI-RADS-1', label: 'BI-RADS 1 - سلبي', system: 'BI-RADS' },
  { value: 'BI-RADS-2', label: 'BI-RADS 2 - حميد', system: 'BI-RADS' },
  { value: 'BI-RADS-3', label: 'BI-RADS 3 - محتمل حميد', system: 'BI-RADS' },
  { value: 'BI-RADS-4', label: 'BI-RADS 4 - مشبوه', system: 'BI-RADS' },
  { value: 'BI-RADS-5', label: 'BI-RADS 5 - خبيث', system: 'BI-RADS' },
  { value: 'BI-RADS-6', label: 'BI-RADS 6 - خبيث مثبت', system: 'BI-RADS' },
  { value: 'PI-RADS-1', label: 'PI-RADS 1 - منخفض جداً', system: 'PI-RADS' },
  { value: 'PI-RADS-2', label: 'PI-RADS 2 - منخفض', system: 'PI-RADS' },
  { value: 'PI-RADS-3', label: 'PI-RADS 3 - متوسط', system: 'PI-RADS' },
  { value: 'PI-RADS-4', label: 'PI-RADS 4 - مرتفع', system: 'PI-RADS' },
  { value: 'PI-RADS-5', label: 'PI-RADS 5 - مرتفع جداً', system: 'PI-RADS' },
  { value: 'LI-RADS-1', label: 'LI-RADS 1 - حميد قطعاً', system: 'LI-RADS' },
  { value: 'LI-RADS-2', label: 'LI-RADS 2 - محتمل حميد', system: 'LI-RADS' },
  { value: 'LI-RADS-3', label: 'LI-RADS 3 - غير محدد', system: 'LI-RADS' },
  { value: 'LI-RADS-4', label: 'LI-RADS 4 - محتمل خبيث', system: 'LI-RADS' },
  { value: 'LI-RADS-5', label: 'LI-RADS 5 - خبيث قطعاً', system: 'LI-RADS' },
  { value: 'TI-RADS-1', label: 'TI-RADS 1 - حميد', system: 'TI-RADS' },
  { value: 'TI-RADS-2', label: 'TI-RADS 2 - غير مشبوه', system: 'TI-RADS' },
  { value: 'TI-RADS-3', label: 'TI-RADS 3 - مشبوه خفيف', system: 'TI-RADS' },
  { value: 'TI-RADS-4', label: 'TI-RADS 4 - مشبوه متوسط', system: 'TI-RADS' },
  { value: 'TI-RADS-5', label: 'TI-RADS 5 - مشبوه عالي', system: 'TI-RADS' }
]

type ReportEditorProps = {
  report: Partial<RadiologyReport>
  templates?: ReportTemplate[]
  readOnly?: boolean
  onChange: (field: string, value: unknown) => void
  onSave: () => void
  onSubmit: () => void
  onTemplateApply: (template: ReportTemplate) => void
}

export function ReportEditor({
  report,
  templates = [],
  readOnly = false,
  onChange,
  onSave,
  onSubmit,
  onTemplateApply
}: ReportEditorProps) {
  const [newFinding, setNewFinding] = useState<Partial<ReportFinding>>({
    type: 'normal',
    description: '',
    location: '',
    laterality: 'N/A',
    severity: 'mild',
    is_key_finding: false
  })
  const [showFindingForm, setShowFindingForm] = useState(false)
  const [showRadsSelector, setShowRadsSelector] = useState(false)

  const addFinding = useCallback(() => {
    if (!newFinding.description) return
    const finding: ReportFinding = {
      id: `finding_${Date.now()}`,
      ...newFinding as ReportFinding
    }
    const findings = [...(report.findings || []), finding]
    onChange('findings', findings)
    setNewFinding({ type: 'normal', description: '', location: '', laterality: 'N/A', severity: 'mild', is_key_finding: false })
    setShowFindingForm(false)
  }, [newFinding, report.findings, onChange])

  const removeFinding = useCallback((id: string) => {
    onChange('findings', (report.findings || []).filter(f => f.id !== id))
  }, [report.findings, onChange])

  const getRadsSystemScores = (system: string) =>
    RADS_SCORES.filter(s => s.system === system)

  if (readOnly) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">تقرير الأشعة</h3>
          <span className={`badge ${
            report.report_status === 'final' ? 'badge-success' :
            report.report_status === 'draft' ? 'badge-neutral' :
            report.report_status === 'amended' ? 'badge-warning' : 'badge-info'
          }`}>
            {report.report_status === 'final' ? 'نهائي' :
             report.report_status === 'draft' ? 'مسودة' :
             report.report_status === 'preliminary' ? 'أولي' :
             report.report_status === 'amended' ? 'معدل' : 'ملغي'}
          </span>
        </div>

        <div style={{ display: 'grid', gap: 16 }}>
          <div>
            <div className="input-label">التاريخ السريري</div>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-primary)' }}>{report.clinical_history || '—'}</div>
          </div>
          <div>
            <div className="input-label">التقنية</div>
            <p style={{ fontSize: '0.875rem' }}>{report.technique || '—'}</p>
          </div>
          <div>
            <div className="input-label">المقارنة</div>
            <p style={{ fontSize: '0.875rem' }}>{report.comparison || '—'}</p>
          </div>
          <div>
            <div className="input-label">النتائج</div>
            {(report.findings || []).length === 0 ? (
              <p style={{ fontSize: '0.875rem', color: 'var(--text-tertiary)' }}>لا توجد نتائج</p>
            ) : (
              (report.findings || []).map((finding, i) => (
                <div key={finding.id} style={{
                  padding: 8,
                  marginBottom: 8,
                  backgroundColor: finding.is_key_finding ? 'rgba(245,158,11,0.1)' : 'var(--bg-tertiary)',
                  borderRadius: 8,
                  borderInlineStart: `3px solid ${finding.type === 'critical' ? 'var(--accent-danger)' : finding.type === 'abnormal' ? 'var(--accent-warning)' : 'var(--accent-success)'}`
                }}>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    {i + 1}. {finding.location} {finding.laterality !== 'N/A' && `(${finding.laterality === 'L' ? 'أيسر' : finding.laterality === 'R' ? 'أيمن' : 'ثنائي'})`}
                    {finding.rads_score && finding.rads_score !== 'NONE' && (
                      <span className={`badge badge-info`} style={{ marginInlineStart: 8 }}>
                        {finding.rads_score}
                      </span>
                    )}
                  </div>
                  <p style={{ fontSize: '0.875rem', marginTop: 4 }}>{finding.description}</p>
                </div>
              ))
            )}
          </div>
          <div>
            <div className="input-label">الانطباع</div>
            <p style={{ fontSize: '0.875rem' }}>{report.impression || '—'}</p>
          </div>
          <div>
            <div className="input-label">الاستنتاج</div>
            <p style={{ fontSize: '0.875rem' }}>{report.conclusion || '—'}</p>
          </div>
          {report.rads_score && report.rads_score !== 'NONE' && (
            <div>
              <div className="input-label">نتيجة RADS</div>
              <span className="badge badge-primary" style={{ fontSize: '0.875rem' }}>
                {RADS_SCORES.find(s => s.value === report.rads_score)?.label || report.rads_score}
              </span>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">تحرير التقرير</h3>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary btn-sm" onClick={onSave}>💾 حفظ</button>
          <button className="btn btn-primary btn-sm" onClick={onSubmit}>✓ إرسال</button>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {/* Template selector */}
        {templates.length > 0 && (
          <div className="input-group">
            <label className="input-label">قوالب التقارير</label>
            <select
              className="select"
              onChange={e => {
                const tpl = templates.find(t => t.id === e.target.value)
                if (tpl) onTemplateApply(tpl)
              }}
              value=""
            >
              <option value="">اختر قالب...</option>
              {templates.map(t => (
                <option key={t.id} value={t.id}>{t.name} ({t.modality})</option>
              ))}
            </select>
          </div>
        )}

        <div className="input-group">
          <label className="input-label">التاريخ السريري</label>
          <textarea
            className="input"
            value={report.clinical_history || ''}
            onChange={e => onChange('clinical_history', e.target.value)}
            rows={2}
            placeholder="التاريخ السريري للمريض..."
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div className="input-group">
            <label className="input-label">التقنية</label>
            <textarea
              className="input"
              value={report.technique || ''}
              onChange={e => onChange('technique', e.target.value)}
              rows={2}
              placeholder="وصف التقنية المستخدمة..."
            />
          </div>
          <div className="input-group">
            <label className="input-label">المقارنة</label>
            <textarea
              className="input"
              value={report.comparison || ''}
              onChange={e => onChange('comparison', e.target.value)}
              rows={2}
              placeholder="دراسات سابقة للمقارنة..."
            />
          </div>
        </div>

        {/* Findings */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
            <label className="input-label" style={{ margin: 0 }}>النتائج</label>
            <button className="btn btn-secondary btn-sm" onClick={() => setShowFindingForm(!showFindingForm)}>
              + إضافة نتيجة
            </button>
          </div>

          {showFindingForm && (
            <div style={{
              padding: 12,
              marginBottom: 12,
              backgroundColor: 'var(--bg-tertiary)',
              borderRadius: 8,
              display: 'flex',
              flexDirection: 'column',
              gap: 8
            }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
                <div className="input-group">
                  <label className="input-label" style={{ fontSize: '0.75rem' }}>النوع</label>
                  <select
                    className="select"
                    value={newFinding.type}
                    onChange={e => setNewFinding(prev => ({ ...prev, type: e.target.value as ReportFinding['type'] }))}
                  >
                    <option value="normal">طبيعي</option>
                    <option value="abnormal">غير طبيعي</option>
                    <option value="critical">خطير</option>
                  </select>
                </div>
                <div className="input-group">
                  <label className="input-label" style={{ fontSize: '0.75rem' }}>الموقع</label>
                  <input
                    className="input"
                    value={newFinding.location || ''}
                    onChange={e => setNewFinding(prev => ({ ...prev, location: e.target.value }))}
                    placeholder="الموقع التشريحي"
                  />
                </div>
                <div className="input-group">
                  <label className="input-label" style={{ fontSize: '0.75rem' }}>الجهة</label>
                  <select
                    className="select"
                    value={newFinding.laterality}
                    onChange={e => setNewFinding(prev => ({ ...prev, laterality: e.target.value as ReportFinding['laterality'] }))}
                  >
                    <option value="N/A">غير محدد</option>
                    <option value="L">أيسر</option>
                    <option value="R">أيمن</option>
                    <option value="B">ثنائي</option>
                  </select>
                </div>
              </div>
              <div className="input-group">
                <label className="input-label" style={{ fontSize: '0.75rem' }}>الوصف</label>
                <textarea
                  className="input"
                  value={newFinding.description || ''}
                  onChange={e => setNewFinding(prev => ({ ...prev, description: e.target.value }))}
                  rows={2}
                  placeholder="وصف النتيجة..."
                />
              </div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.8rem', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={newFinding.is_key_finding || false}
                    onChange={e => setNewFinding(prev => ({ ...prev, is_key_finding: e.target.checked }))}
                  />
                  نتيجة رئيسية
                </label>
                <div style={{ flex: 1 }} />
                <button className="btn btn-primary btn-sm" onClick={addFinding}>إضافة</button>
                <button className="btn btn-ghost btn-sm" onClick={() => setShowFindingForm(false)}>إلغاء</button>
              </div>
            </div>
          )}

          {(report.findings || []).length === 0 ? (
            <p style={{ fontSize: '0.875rem', color: 'var(--text-tertiary)', padding: 16, textAlign: 'center' }}>
              لم تتم إضافة أي نتائج بعد
            </p>
          ) : (
            (report.findings || []).map((finding, i) => (
              <div key={finding.id} style={{
                padding: '8px 12px',
                marginBottom: 6,
                backgroundColor: finding.is_key_finding ? 'rgba(245,158,11,0.1)' : 'var(--bg-tertiary)',
                borderRadius: 8,
                borderInlineStart: `3px solid ${finding.type === 'critical' ? 'var(--accent-danger)' : finding.type === 'abnormal' ? 'var(--accent-warning)' : 'var(--accent-success)'}`,
                display: 'flex',
                alignItems: 'flex-start',
                gap: 8
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
                      {i + 1}. {finding.location}
                      {finding.laterality !== 'N/A' && ` (${finding.laterality === 'L' ? 'أيسر' : finding.laterality === 'R' ? 'أيمن' : 'ثنائي'})`}
                    </span>
                    {finding.is_key_finding && <span className="badge badge-warning" style={{ fontSize: '0.65rem' }}>⭐ رئيسي</span>}
                    {finding.rads_score && finding.rads_score !== 'NONE' && (
                      <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>{finding.rads_score}</span>
                    )}
                  </div>
                  <p style={{ fontSize: '0.85rem' }}>{finding.description}</p>
                </div>
                <button className="btn btn-ghost btn-sm" onClick={() => removeFinding(finding.id)} style={{ color: 'var(--text-danger)', flexShrink: 0 }}>
                  ✕
                </button>
              </div>
            ))
          )}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div className="input-group">
            <label className="input-label">الانطباع</label>
            <textarea
              className="input"
              value={report.impression || ''}
              onChange={e => onChange('impression', e.target.value)}
              rows={3}
              placeholder="الانطباع العام..."
            />
          </div>
          <div className="input-group">
            <label className="input-label">الاستنتاج</label>
            <textarea
              className="input"
              value={report.conclusion || ''}
              onChange={e => onChange('conclusion', e.target.value)}
              rows={3}
              placeholder="الاستنتاج النهائي..."
            />
          </div>
        </div>

        <div className="input-group">
          <label className="input-label">التوصيات</label>
          <textarea
            className="input"
            value={report.recommendation || ''}
            onChange={e => onChange('recommendation', e.target.value)}
            rows={2}
            placeholder="التوصيات..."
          />
        </div>

        {/* RADS Score */}
        <div className="input-group">
          <label className="input-label">نتيجة RADS</label>
          <div style={{ position: 'relative' }}>
            <button
              className="btn btn-secondary"
              onClick={() => setShowRadsSelector(!showRadsSelector)}
              style={{ width: '100%', justifyContent: 'space-between' }}
            >
              <span>{RADS_SCORES.find(s => s.value === report.rads_score)?.label || 'اختر نتيجة RADS'}</span>
              <span>▼</span>
            </button>
            {showRadsSelector && (
              <div style={{
                position: 'absolute',
                top: '100%',
                insetInlineStart: 0,
                insetInlineEnd: 0,
                backgroundColor: 'var(--bg-card)',
                border: '1px solid var(--border-primary)',
                borderRadius: 8,
                boxShadow: 'var(--shadow-lg)',
                zIndex: 20,
                maxHeight: 300,
                overflowY: 'auto',
                marginTop: 4
              }}>
                <div
                  onClick={() => { onChange('rads_score', 'NONE'); setShowRadsSelector(false) }}
                  style={{ padding: '8px 12px', cursor: 'pointer', borderBottom: '1px solid var(--border-primary)', fontSize: '0.8rem' }}
                  onMouseEnter={e => { e.currentTarget.style.backgroundColor = 'var(--bg-hover)' }}
                  onMouseLeave={e => { e.currentTarget.style.backgroundColor = 'transparent' }}
                >
                  لا يوجد
                </div>
                {['RADS', 'BI-RADS', 'PI-RADS', 'LI-RADS', 'TI-RADS'].map(system => (
                  <div key={system}>
                    <div style={{ padding: '4px 12px', fontSize: '0.7rem', color: 'var(--text-tertiary)', fontWeight: 600, backgroundColor: 'var(--bg-tertiary)' }}>
                      {system}
                    </div>
                    {getRadsSystemScores(system).map(score => (
                      <div
                        key={score.value}
                        onClick={() => { onChange('rads_score', score.value); setShowRadsSelector(false) }}
                        style={{
                          padding: '6px 12px',
                          cursor: 'pointer',
                          fontSize: '0.8rem',
                          backgroundColor: report.rads_score === score.value ? 'var(--accent-primary-light)' : undefined
                        }}
                        onMouseEnter={e => { e.currentTarget.style.backgroundColor = 'var(--bg-hover)' }}
                        onMouseLeave={e => {
                          e.currentTarget.style.backgroundColor =
                            report.rads_score === score.value ? 'var(--accent-primary-light)' : undefined
                        }}
                      >
                        {score.label}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
