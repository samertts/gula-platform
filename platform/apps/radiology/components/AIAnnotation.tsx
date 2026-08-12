import { useState, useCallback } from 'react'

type Annotation = {
  id: string
  type: 'nodule' | 'mass' | 'calcification' | 'fracture' | 'hemorrhage' | 'tumor' | 'other'
  label: string
  confidence: number
  x: number
  y: number
  width: number
  height: number
  probability: number
  finding: string
  rads_relevant: boolean
  suggested_rads?: string
}

type AIAnnotationProps = {
  annotations: Annotation[]
  visible: boolean
  onToggleVisibility: () => void
  onAnnotationClick: (annotation: Annotation) => void
  onAcceptAnnotation: (id: string) => void
  onRejectAnnotation: (id: string) => void
  loading?: boolean
}

const ANNOTATION_TYPE_CONFIG = {
  nodule: { label: 'عقدة', color: '#22c55e', icon: '●' },
  mass: { label: 'كتلة', color: '#f59e0b', icon: '◆' },
  calcification: { label: 'تكلس', color: '#3b82f6', icon: '✦' },
  fracture: { label: 'كسر', color: '#ef4444', icon: '⚡' },
  hemorrhage: { label: 'نزف', color: '#ef4444', icon: '⬤' },
  tumor: { label: 'ورم', color: '#8b5cf6', icon: '▲' },
  other: { label: 'آخر', color: '#06b6d4', icon: '◈' }
}

export function AIAnnotation({
  annotations,
  visible,
  onToggleVisibility,
  onAnnotationClick,
  onAcceptAnnotation,
  onRejectAnnotation,
  loading = false
}: AIAnnotationProps) {
  const [filterType, setFilterType] = useState<string>('all')
  const [minConfidence, setMinConfidence] = useState(0)

  const filteredAnnotations = annotations.filter(a => {
    if (filterType !== 'all' && a.type !== filterType) return false
    if (a.confidence < minConfidence) return false
    return true
  })

  const sortedAnnotations = [...filteredAnnotations].sort((a, b) => b.confidence - a.confidence)

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'var(--accent-success)'
    if (confidence >= 0.5) return 'var(--accent-warning)'
    return 'var(--accent-danger)'
  }

  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '10px 12px',
        borderBottom: '1px solid var(--border-primary)',
        backgroundColor: 'var(--bg-secondary)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: '1rem' }}>🤖</span>
          <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>الذكاء الاصطناعي</span>
          {loading && <span className="skeleton" style={{ width: 16, height: 16, borderRadius: '50%' }} />}
        </div>
        <button
          className={`btn btn-sm ${visible ? 'btn-primary' : 'btn-ghost'}`}
          onClick={onToggleVisibility}
          style={{ fontSize: '0.75rem' }}
        >
          {visible ? 'إخفاء' : 'إظهار'}
        </button>
      </div>

      {loading ? (
        <div style={{ padding: 16 }}>
          {[1, 2, 3].map(i => (
            <div key={i} className="skeleton" style={{ height: 40, marginBottom: 8, borderRadius: 6 }} />
          ))}
          <div style={{ textAlign: 'center', color: 'var(--text-tertiary)', fontSize: '0.8rem', marginTop: 8 }}>
            جاري تحليل الصور...
          </div>
        </div>
      ) : annotations.length === 0 ? (
        <div className="empty-state" style={{ padding: '1.5rem' }}>
          <div style={{ fontSize: '2rem', marginBottom: 8, opacity: 0.5 }}>🔍</div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-tertiary)' }}>
            لم يتم العثور على نتائج بواسطة الذكاء الاصطناعي
          </p>
        </div>
      ) : (
        <>
          {/* Filters */}
          <div style={{
            display: 'flex',
            gap: 8,
            padding: '8px 12px',
            borderBottom: '1px solid var(--border-primary)',
            backgroundColor: 'var(--bg-tertiary)'
          }}>
            <select
              className="select"
              value={filterType}
              onChange={e => setFilterType(e.target.value)}
              style={{ fontSize: '0.75rem', padding: '4px 8px' }}
            >
              <option value="all">جميع الأنواع</option>
              {Object.entries(ANNOTATION_TYPE_CONFIG).map(([key, config]) => (
                <option key={key} value={key}>{config.label}</option>
              ))}
            </select>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.75rem' }}>
              <span style={{ color: 'var(--text-tertiary)' }}>الثقة:</span>
              <input
                type="range"
                min={0}
                max={100}
                value={minConfidence * 100}
                onChange={e => setMinConfidence(Number(e.target.value) / 100)}
                style={{ width: 80 }}
              />
              <span style={{ color: 'var(--text-secondary)', minWidth: 30 }}>{Math.round(minConfidence * 100)}%</span>
            </div>
          </div>

          {/* Annotations list */}
          <div style={{ maxHeight: 300, overflowY: 'auto' }}>
            {sortedAnnotations.map(ann => {
              const typeConfig = ANNOTATION_TYPE_CONFIG[ann.type] || ANNOTATION_TYPE_CONFIG.other
              return (
                <div
                  key={ann.id}
                  onClick={() => onAnnotationClick(ann)}
                  style={{
                    padding: '8px 12px',
                    borderBottom: '1px solid var(--border-primary)',
                    cursor: 'pointer',
                    transition: 'background-color 150ms'
                  }}
                  onMouseEnter={e => { e.currentTarget.style.backgroundColor = 'var(--bg-hover)' }}
                  onMouseLeave={e => { e.currentTarget.style.backgroundColor = 'transparent' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span style={{ color: typeConfig.color, fontSize: '1.1rem' }}>{typeConfig.icon}</span>
                    <span style={{ fontSize: '0.85rem', fontWeight: 500, flex: 1 }}>{ann.label}</span>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                      padding: '2px 6px',
                      borderRadius: 4,
                      backgroundColor: getConfidenceColor(ann.confidence),
                      color: 'white',
                      fontSize: '0.7rem',
                      fontWeight: 600
                    }}>
                      {Math.round(ann.confidence * 100)}%
                    </div>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginBottom: 4 }}>
                    {ann.finding}
                  </div>
                  {ann.rads_relevant && ann.suggested_rads && (
                    <div style={{ fontSize: '0.7rem' }}>
                      <span className="badge badge-info">{ann.suggested_rads}</span>
                    </div>
                  )}
                  <div style={{ display: 'flex', gap: 4, marginTop: 6 }}>
                    <button
                      className="btn btn-sm btn-primary"
                      onClick={e => { e.stopPropagation(); onAcceptAnnotation(ann.id) }}
                      style={{ fontSize: '0.7rem', padding: '2px 8px' }}
                    >
                      ✓ قبول
                    </button>
                    <button
                      className="btn btn-sm btn-ghost"
                      onClick={e => { e.stopPropagation(); onRejectAnnotation(ann.id) }}
                      style={{ fontSize: '0.7rem', padding: '2px 8px', color: 'var(--text-danger)' }}
                    >
                      ✕ رفض
                    </button>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Summary */}
          <div style={{
            padding: '8px 12px',
            borderTop: '1px solid var(--border-primary)',
            backgroundColor: 'var(--bg-secondary)',
            fontSize: '0.75rem',
            display: 'flex',
            justifyContent: 'space-between',
            color: 'var(--text-tertiary)'
          }}>
            <span>المجموع: {annotations.length}</span>
            <span>معروض: {sortedAnnotations.length}</span>
            <span>متوسط الثقة: {Math.round(annotations.reduce((a, b) => a + b.confidence, 0) / annotations.length * 100)}%</span>
          </div>
        </>
      )}
    </div>
  )
}
