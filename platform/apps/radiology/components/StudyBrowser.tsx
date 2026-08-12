import { useState } from 'react'
import type { DicomStudy, StudySeries } from '@services/dicom'

type StudyBrowserProps = {
  studies: DicomStudy[]
  selectedStudyUid?: string
  selectedSeriesUid?: string
  onStudySelect: (study: DicomStudy) => void
  onSeriesSelect: (study: DicomStudy, series: StudySeries) => void
  loading?: boolean
}

export function StudyBrowser({
  studies,
  selectedStudyUid,
  selectedSeriesUid,
  onStudySelect,
  onSeriesSelect,
  loading = false
}: StudyBrowserProps) {
  const [expandedStudies, setExpandedStudies] = useState<Set<string>>(new Set(
    selectedStudyUid ? [selectedStudyUid] : []
  ))

  const toggleStudy = (studyUid: string) => {
    setExpandedStudies(prev => {
      const next = new Set(prev)
      if (next.has(studyUid)) next.delete(studyUid)
      else next.add(studyUid)
      return next
    })
  }

  if (loading) {
    return (
      <div className="card" style={{ minHeight: 200 }}>
        {[1, 2, 3].map(i => (
          <div key={i} style={{ padding: '12px', borderBottom: '1px solid var(--border-primary)' }}>
            <div className="skeleton" style={{ height: 16, width: '60%', marginBottom: 8 }} />
            <div className="skeleton" style={{ height: 12, width: '40%' }} />
          </div>
        ))}
      </div>
    )
  }

  if (!studies.length) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
        <div style={{ fontSize: '2rem', marginBottom: '0.5rem', opacity: 0.5 }}>📋</div>
        <p style={{ color: 'var(--text-tertiary)' }}>لا توجد دراسات متاحة</p>
      </div>
    )
  }

  const getModalityColor = (modality: string) => {
    const colors: Record<string, string> = {
      CT: '#3b82f6', MR: '#8b5cf6', US: '#22c55e', XA: '#ef4444',
      CR: '#f59e0b', DX: '#f59e0b', MG: '#ec4899', NM: '#06b6d4', PT: '#14b8a6'
    }
    return colors[modality] || '#94a3b8'
  }

  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      <div style={{
        padding: '12px 16px',
        borderBottom: '1px solid var(--border-primary)',
        backgroundColor: 'var(--bg-secondary)',
        fontSize: '0.875rem',
        fontWeight: 600,
        color: 'var(--text-secondary)'
      }}>
        الدراسات ({studies.length})
      </div>

      <div style={{ maxHeight: 400, overflowY: 'auto' }}>
        {studies.map(study => (
          <div key={study.study_uid}>
            <div
              onClick={() => {
                toggleStudy(study.study_uid)
                onStudySelect(study)
              }}
              style={{
                padding: '12px 16px',
                cursor: 'pointer',
                borderBottom: '1px solid var(--border-primary)',
                backgroundColor: selectedStudyUid === study.study_uid ? 'var(--accent-primary-light)' : undefined,
                transition: 'background-color 150ms'
              }}
              onMouseEnter={e => { e.currentTarget.style.backgroundColor = 'var(--bg-hover)' }}
              onMouseLeave={e => {
                e.currentTarget.style.backgroundColor =
                  selectedStudyUid === study.study_uid ? 'var(--accent-primary-light)' : ''
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <span style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '2px 6px',
                  borderRadius: 4,
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  color: 'white',
                  backgroundColor: getModalityColor(study.modality),
                  minWidth: 28
                }}>
                  {study.modality}
                </span>
                <span style={{ fontSize: '0.875rem', fontWeight: 500, flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {study.study_description || 'بدون وصف'}
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
                  {study.study_date}
                </span>
              </div>
              <div style={{ display: 'flex', gap: 16, fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
                <span>{study.patient_name}</span>
                <span>{study.number_of_series} سلسلة</span>
                <span>{study.number_of_instances} صورة</span>
              </div>
            </div>

            {expandedStudies.has(study.study_uid) && study.series?.length > 0 && (
              <div style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                {study.series.map(series => (
                  <div
                    key={series.series_uid}
                    onClick={() => onSeriesSelect(study, series)}
                    style={{
                      padding: '8px 16px 8px 32px',
                      cursor: 'pointer',
                      borderBottom: '1px solid var(--border-primary)',
                      backgroundColor: selectedSeriesUid === series.series_uid ? 'var(--bg-active)' : undefined,
                      fontSize: '0.8rem'
                    }}
                    onMouseEnter={e => { e.currentTarget.style.backgroundColor = 'var(--bg-hover)' }}
                    onMouseLeave={e => {
                      e.currentTarget.style.backgroundColor =
                        selectedSeriesUid === series.series_uid ? 'var(--bg-active)' : ''
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        padding: '1px 4px',
                        borderRadius: 3,
                        fontSize: '0.65rem',
                        fontWeight: 700,
                        color: 'white',
                        backgroundColor: getModalityColor(series.modality)
                      }}>
                        {series.modality}
                      </span>
                      <span style={{ flex: 1 }}>{series.series_description || `سلسلة ${series.series_number}`}</span>
                      <span style={{ color: 'var(--text-tertiary)', fontSize: '0.7rem' }}>
                        {series.number_of_instances} صورة
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
