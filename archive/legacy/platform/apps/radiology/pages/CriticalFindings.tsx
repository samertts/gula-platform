import { useState, useEffect, useCallback } from 'react'
import { reportingService, type CriticalFinding, type CriticalFindingSeverity } from '@services/reporting'

export function CriticalFindings() {
  const [findings, setFindings] = useState<CriticalFinding[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'pending' | 'all' | 'acknowledged'>('pending')
  const [selectedFinding, setSelectedFinding] = useState<CriticalFinding | null>(null)

  const fetchFindings = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await reportingService.getPendingCriticalFindings()
      setFindings(Array.isArray(res) ? res : [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'فشل تحميل النتائج الحرجة')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchFindings()
    const interval = setInterval(fetchFindings, 30000)
    return () => clearInterval(interval)
  }, [fetchFindings])

  const handleAcknowledge = useCallback(async (finding: CriticalFinding) => {
    try {
      await reportingService.acknowledgeCriticalFinding(finding.report_id, finding.id, 'current_user')
      setFindings(prev => prev.filter(f => f.id !== finding.id))
    } catch (err) {
      console.error('Failed to acknowledge:', err)
    }
  }, [])

  const getSeverityConfig = (severity: CriticalFindingSeverity) => {
    switch (severity) {
      case 'critical': return { label: 'حرج', className: 'badge-danger', icon: '🔴' }
      case 'urgent': return { label: 'عاجل', className: 'badge-warning', icon: '🟡' }
      case 'significant': return { label: 'هام', className: 'badge-info', icon: '🔵' }
    }
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div className="skeleton" style={{ height: 40, width: 300 }} />
        <div className="skeleton" style={{ height: 200 }} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">⚠️</div>
        <p style={{ color: 'var(--text-danger)' }}>{error}</p>
        <button className="btn btn-primary mt-md" onClick={fetchFindings}>إعادة</button>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>
            النتائج الحرجة
            {findings.length > 0 && (
              <span className="badge badge-danger" style={{ marginInlineStart: 8, fontSize: '0.9rem' }}>
                {findings.length}
              </span>
            )}
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-tertiary)' }}>
            إدارة النتائج الحرجة والعاجلة والتواصل مع الأطباء
          </p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={fetchFindings}>↻ تحديث</button>
      </div>

      {/* Alert banner */}
      {findings.length > 0 && (
        <div style={{
          padding: 16,
          backgroundColor: 'rgba(239,68,68,0.1)',
          border: '1px solid var(--accent-danger)',
          borderRadius: 12,
          display: 'flex',
          alignItems: 'center',
          gap: 12
        }}>
          <span style={{ fontSize: '2rem' }}>🚨</span>
          <div>
            <p style={{ fontWeight: 700, color: 'var(--text-danger)', fontSize: '1rem' }}>
              يوجد {findings.length} نتيجة حرجة في انتظار الإقرار
            </p>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              يرجى التواصل مع الطبيب المعالج وتأكيد الاستلام
            </p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="tabs">
        <button className={`tab ${activeTab === 'pending' ? 'active' : ''}`} onClick={() => setActiveTab('pending')}>
          معلقة {findings.length > 0 && `(${findings.length})`}
        </button>
        <button className={`tab ${activeTab === 'all' ? 'active' : ''}`} onClick={() => setActiveTab('all')}>الكل</button>
        <button className={`tab ${activeTab === 'acknowledged' ? 'active' : ''}`} onClick={() => setActiveTab('acknowledged')}>مؤكدة</button>
      </div>

      {/* Findings list */}
      {findings.length === 0 ? (
        <div className="card empty-state">
          <div style={{ fontSize: '3rem', marginBottom: 12 }}>✅</div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: 8, color: 'var(--text-success)' }}>
            لا توجد نتائج حرجة معلقة
          </h3>
          <p style={{ color: 'var(--text-tertiary)' }}>جميع النتائج الحرجة تم التعامل معها</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {findings.map(finding => {
            const severity = getSeverityConfig(finding.severity)
            return (
              <div
                key={finding.id}
                className="card"
                style={{
                  borderInlineStart: `4px solid ${
                    finding.severity === 'critical' ? 'var(--accent-danger)' :
                    finding.severity === 'urgent' ? 'var(--accent-warning)' :
                    'var(--accent-info)'
                  }`,
                  cursor: 'pointer'
                }}
                onClick={() => setSelectedFinding(finding)}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{ fontSize: '1.5rem' }}>{severity?.icon}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <span className={`badge ${severity?.className}`}>{severity?.label}</span>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        إلى: {finding.communicated_to}
                      </span>
                      {!finding.acknowledged && (
                        <span className="badge badge-danger" style={{ fontSize: '0.65rem' }}>
                          غير مؤكد
                        </span>
                      )}
                    </div>
                    <p style={{ fontSize: '0.9rem', fontWeight: 500 }}>{finding.finding}</p>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginTop: 4 }}>
                      <span>طريقة التواصل: {finding.communication_method}</span>
                      <span style={{ marginInlineStart: 12 }}>التوقيت: {finding.communication_time}</span>
                      <span style={{ marginInlineStart: 12 }}>{finding.created_at}</span>
                    </div>
                  </div>
                  {!finding.acknowledged && (
                    <button
                      className="btn btn-primary"
                      onClick={e => { e.stopPropagation(); handleAcknowledge(finding) }}
                    >
                      ✓ تأكيد الاستلام
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Detail modal */}
      {selectedFinding && (
        <div className="modal-overlay" onClick={() => setSelectedFinding(null)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 500 }}>
            <div className="modal-header">
              <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>تفاصيل النتيجة الحرجة</h2>
              <button className="btn btn-ghost btn-sm" onClick={() => setSelectedFinding(null)}>✕</button>
            </div>
            <div className="modal-body">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div style={{
                  padding: 12,
                  backgroundColor: selectedFinding.severity === 'critical' ? 'rgba(239,68,68,0.1)' : 'rgba(245,158,11,0.1)',
                  borderRadius: 8
                }}>
                  <span className={`badge ${
                    selectedFinding.severity === 'critical' ? 'badge-danger' :
                    selectedFinding.severity === 'urgent' ? 'badge-warning' : 'badge-info'
                  }`} style={{ fontSize: '0.9rem', marginBottom: 8 }}>
                    {selectedFinding.severity === 'critical' ? 'حرج' :
                     selectedFinding.severity === 'urgent' ? 'عاجل' : 'هام'}
                  </span>
                  <p style={{ fontSize: '1rem', marginTop: 8 }}>{selectedFinding.finding}</p>
                </div>

                <div className="grid grid-2">
                  <div>
                    <label className="input-label">تم التواصل مع</label>
                    <p>{selectedFinding.communicated_to}</p>
                  </div>
                  <div>
                    <label className="input-label">طريقة التواصل</label>
                    <p>{selectedFinding.communication_method}</p>
                  </div>
                  <div>
                    <label className="input-label">وقت التواصل</label>
                    <p>{selectedFinding.communication_time}</p>
                  </div>
                  <div>
                    <label className="input-label">تاريخ الإبلاغ</label>
                    <p>{selectedFinding.created_at}</p>
                  </div>
                </div>

                <div>
                  <label className="input-label">حالة الإقرار</label>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    {selectedFinding.acknowledged ? (
                      <span className="badge badge-success">تم التأكيد</span>
                    ) : (
                      <span className="badge badge-danger">في انتظار التأكيد</span>
                    )}
                    {selectedFinding.acknowledged_by && (
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>
                        بواسطة: {selectedFinding.acknowledged_by} في {selectedFinding.acknowledged_at}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              {!selectedFinding.acknowledged && (
                <button className="btn btn-primary" onClick={() => { handleAcknowledge(selectedFinding); setSelectedFinding(null) }}>
                  ✓ تأكيد الاستلام
                </button>
              )}
              <button className="btn btn-secondary" onClick={() => setSelectedFinding(null)}>إغلاق</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
