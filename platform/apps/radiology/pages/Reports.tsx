import { useState, useEffect, useCallback } from 'react'
import { reportingService, type RadiologyReport, type ReportStatus, type ReportTemplate, type ReportFinding, type RadsScore } from '@services/reporting'
import { dicomService, type DicomStudy } from '@services/dicom'
import { ReportEditor } from '@components/ReportEditor'

export function Reports() {
  const [reports, setReports] = useState<RadiologyReport[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'all' | 'draft' | 'final' | 'amended'>('all')
  const [selectedReport, setSelectedReport] = useState<RadiologyReport | null>(null)
  const [editingReport, setEditingReport] = useState<RadiologyReport | null>(null)
  const [templates, setTemplates] = useState<ReportTemplate[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [studies, setStudies] = useState<DicomStudy[]>([])
  const [showNewModal, setShowNewModal] = useState(false)
  const [selectedStudyUid, setSelectedStudyUid] = useState('')

  const fetchReports = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const filter: Record<string, string> = {}
      if (activeTab !== 'all') filter.status = activeTab
      if (searchQuery) filter.patient_name = searchQuery

      const res = await reportingService.getReports(filter)
      setReports(res.items)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'فشل تحميل التقارير')
    } finally {
      setLoading(false)
    }
  }, [activeTab, searchQuery])

  const fetchTemplates = useCallback(async () => {
    try {
      const res = await reportingService.getTemplates()
      setTemplates(Array.isArray(res) ? res : [])
    } catch {
      // Templates are optional
    }
  }, [])

  const fetchStudies = useCallback(async () => {
    try {
      const res = await dicomService.searchStudies({ limit: 50 })
      setStudies(res.items || [])
    } catch {
      // Studies are optional
    }
  }, [])

  useEffect(() => {
    fetchReports()
    fetchTemplates()
    fetchStudies()
  }, [fetchReports, fetchTemplates, fetchStudies])

  const handleCreateReport = useCallback(async () => {
    if (!selectedStudyUid) return
    try {
      const study = studies.find(s => s.study_uid === selectedStudyUid)
      const newReport = await reportingService.createReport({
        study_uid: selectedStudyUid,
        accession_number: study?.accession_number || '',
        patient_id: study?.patient_id || '',
        patient_name: study?.patient_name || '',
        report_status: 'draft',
        report_type: 'structured',
        reading_physician: '',
        findings: [],
        critical_findings: []
      } as Partial<RadiologyReport>)
      setEditingReport(newReport)
      setShowNewModal(false)
    } catch (err) {
      console.error('Failed to create report:', err)
    }
  }, [selectedStudyUid, studies])

  const handleSaveReport = useCallback(async () => {
    if (!editingReport?.id) return
    try {
      const updated = await reportingService.updateReport(editingReport.id, editingReport)
      setEditingReport(updated)
      setReports(prev => prev.map(r => r.id === updated.id ? updated : r))
    } catch (err) {
      console.error('Failed to save report:', err)
    }
  }, [editingReport])

  const handleSubmitReport = useCallback(async () => {
    if (!editingReport?.id) return
    try {
      const submitted = await reportingService.submitReport(editingReport.id)
      setEditingReport(submitted)
      setReports(prev => prev.map(r => r.id === submitted.id ? submitted : r))
    } catch (err) {
      console.error('Failed to submit report:', err)
    }
  }, [editingReport])

  const handleTemplateApply = useCallback((template: ReportTemplate) => {
    if (!editingReport) return
    setEditingReport(prev => prev ? {
      ...prev,
      technique: template.content.technique || prev.technique,
      comparison: template.content.comparison || prev.comparison,
      impression: template.content.impression || prev.impression,
      conclusion: template.content.conclusion || prev.conclusion
    } : prev)
  }, [editingReport])

  const handleReportFieldChange = useCallback((field: string, value: unknown) => {
    if (!editingReport) return
    setEditingReport(prev => prev ? { ...prev, [field]: value } : prev)
  }, [editingReport])

  const handleViewReport = useCallback(async (report: RadiologyReport) => {
    setSelectedReport(report)
  }, [])

  const handleEditReport = useCallback((report: RadiologyReport) => {
    setEditingReport(report)
    setSelectedReport(null)
  }, [])

  const getRadsScoreLabel = (score: RadsScore) => {
    if (!score || score === 'NONE') return null
    const labels: Record<string, string> = {
      'RADS-1': 'RADS 1', 'RADS-2': 'RADS 2', 'RADS-3': 'RADS 3', 'RADS-4': 'RADS 4', 'RADS-5': 'RADS 5',
      'BI-RADS-0': 'BI-RADS 0', 'BI-RADS-1': 'BI-RADS 1', 'BI-RADS-2': 'BI-RADS 2', 'BI-RADS-3': 'BI-RADS 3',
      'BI-RADS-4': 'BI-RADS 4', 'BI-RADS-5': 'BI-RADS 5', 'BI-RADS-6': 'BI-RADS 6',
      'PI-RADS-1': 'PI-RADS 1', 'PI-RADS-2': 'PI-RADS 2', 'PI-RADS-3': 'PI-RADS 3',
      'PI-RADS-4': 'PI-RADS 4', 'PI-RADS-5': 'PI-RADS 5'
    }
    return labels[score] || score
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>التقارير</h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-tertiary)' }}>كتابة وإدارة تقارير الأشعة</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowNewModal(true)}>
          + تقرير جديد
        </button>
      </div>

      {/* Search */}
      <div className="card" style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <input
          className="input"
          placeholder="بحث باسم المريض..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          style={{ flex: 1 }}
        />
        <button className="btn btn-ghost" onClick={() => setSearchQuery('')}>مسح</button>
      </div>

      {/* Tabs */}
      <div className="tabs">
        <button className={`tab ${activeTab === 'all' ? 'active' : ''}`} onClick={() => setActiveTab('all')}>الكل</button>
        <button className={`tab ${activeTab === 'draft' ? 'active' : ''}`} onClick={() => setActiveTab('draft')}>مسودة</button>
        <button className={`tab ${activeTab === 'final' ? 'active' : ''}`} onClick={() => setActiveTab('final')}>نهائي</button>
        <button className={`tab ${activeTab === 'amended' ? 'active' : ''}`} onClick={() => setActiveTab('amended')}>معدل</button>
      </div>

      {/* Reports list or editor */}
      {editingReport ? (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 16 }}>
          <ReportEditor
            report={editingReport}
            templates={templates}
            onChange={handleReportFieldChange}
            onSave={handleSaveReport}
            onSubmit={handleSubmitReport}
            onTemplateApply={handleTemplateApply}
          />
          <div className="card">
            <div className="card-header">
              <h3 className="card-title" style={{ fontSize: '0.9rem' }}>إجراءات</h3>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <button className="btn btn-primary" onClick={handleSaveReport} style={{ width: '100%' }}>
                💾 حفظ
              </button>
              <button className="btn btn-success" onClick={handleSubmitReport} style={{ width: '100%' }}>
                ✓ تقديم التقرير
              </button>
              <button className="btn btn-secondary" onClick={() => setEditingReport(null)} style={{ width: '100%' }}>
                رجوع
              </button>
            </div>
            <hr className="divider" />
            <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>
              <p>الحالة: <strong>{editingReport.report_status === 'draft' ? 'مسودة' : editingReport.report_status === 'final' ? 'نهائي' : editingReport.report_status}</strong></p>
              {editingReport.rads_score && editingReport.rads_score !== 'NONE' && (
                <p>RADS: <strong>{getRadsScoreLabel(editingReport.rads_score)}</strong></p>
              )}
              {editingReport.report_status === 'final' && editingReport.verified_by && (
                <p>تدقيق: {editingReport.verified_by}</p>
              )}
            </div>
          </div>
        </div>
      ) : loading ? (
        <div className="card" style={{ padding: 0 }}>
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="skeleton" style={{ height: 48, margin: 8 }} />
          ))}
        </div>
      ) : error ? (
        <div className="card empty-state">
          <div className="empty-state-icon">⚠️</div>
          <p style={{ color: 'var(--text-danger)' }}>{error}</p>
          <button className="btn btn-primary mt-md" onClick={fetchReports}>إعادة</button>
        </div>
      ) : reports.length === 0 ? (
        <div className="card empty-state">
          <div className="empty-state-icon">📝</div>
          <p>لا توجد تقارير</p>
          <button className="btn btn-primary mt-md" onClick={() => setShowNewModal(true)}>إنشاء تقرير</button>
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>الحالة</th>
                <th>المريض</th>
                <th>الفحص</th>
                <th>الطبيب القارئ</th>
                <th>RADS</th>
                <th>التاريخ</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {reports.map(report => (
                <tr key={report.id} style={{ cursor: 'pointer' }} onClick={() => handleViewReport(report)}>
                  <td>
                    <span className={`badge ${
                      report.report_status === 'final' ? 'badge-success' :
                      report.report_status === 'draft' ? 'badge-neutral' :
                      report.report_status === 'amended' ? 'badge-warning' : 'badge-danger'
                    }`}>
                      {report.report_status === 'final' ? 'نهائي' :
                       report.report_status === 'draft' ? 'مسودة' :
                       report.report_status === 'preliminary' ? 'أولي' :
                       report.report_status === 'amended' ? 'معدل' : 'ملغي'}
                    </span>
                  </td>
                  <td>
                    <div style={{ fontWeight: 500, fontSize: '0.875rem' }}>{report.patient_name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>{report.patient_id}</div>
                  </td>
                  <td style={{ fontSize: '0.85rem', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {report.impression || report.clinical_history || '—'}
                  </td>
                  <td style={{ fontSize: '0.8rem' }}>{report.reading_physician || '—'}</td>
                  <td>
                    {report.rads_score && report.rads_score !== 'NONE' ? (
                      <span className="badge badge-primary">{getRadsScoreLabel(report.rads_score)}</span>
                    ) : '—'}
                  </td>
                  <td style={{ fontSize: '0.8rem', whiteSpace: 'nowrap' }}>{report.created_at?.split('T')[0]}</td>
                  <td>
                    <div style={{ display: 'flex', gap: 4 }}>
                      <button className="btn btn-sm btn-ghost" onClick={e => { e.stopPropagation(); handleViewReport(report) }}>
                        👁
                      </button>
                      {report.report_status !== 'final' && (
                        <button className="btn btn-sm btn-ghost" onClick={e => { e.stopPropagation(); handleEditReport(report) }}>
                          ✏️
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* New report modal */}
      {showNewModal && (
        <div className="modal-overlay" onClick={() => setShowNewModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 500 }}>
            <div className="modal-header">
              <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>تقرير جديد</h2>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowNewModal(false)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="input-group">
                <label className="input-label">اختر الدراسة</label>
                <select className="select" value={selectedStudyUid} onChange={e => setSelectedStudyUid(e.target.value)}>
                  <option value="">اختر دراسة...</option>
                  {studies.map(s => (
                    <option key={s.study_uid} value={s.study_uid}>
                      {s.patient_name} — {s.study_description} ({s.modality}, {s.study_date})
                    </option>
                  ))}
                </select>
              </div>
              <div style={{ display: 'flex', gap: 8, marginTop: 16, justifyContent: 'flex-end' }}>
                <button className="btn btn-secondary" onClick={() => setShowNewModal(false)}>إلغاء</button>
                <button className="btn btn-primary" disabled={!selectedStudyUid} onClick={handleCreateReport}>
                  إنشاء
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* View report modal */}
      {selectedReport && (
        <div className="modal-overlay" onClick={() => setSelectedReport(null)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 800, maxHeight: '90vh' }}>
            <div className="modal-header">
              <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>عرض التقرير</h2>
              <button className="btn btn-ghost btn-sm" onClick={() => setSelectedReport(null)}>✕</button>
            </div>
            <div className="modal-body">
              <ReportEditor
                report={selectedReport}
                readOnly
                onChange={() => {}}
                onSave={() => {}}
                onSubmit={() => {}}
                onTemplateApply={() => {}}
              />
            </div>
            <div className="modal-footer">
              {selectedReport.report_status !== 'final' && (
                <button className="btn btn-primary" onClick={() => { handleEditReport(selectedReport); setSelectedReport(null) }}>
                  ✏️ تحرير
                </button>
              )}
              <button className="btn btn-secondary" onClick={() => setSelectedReport(null)}>إغلاق</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
