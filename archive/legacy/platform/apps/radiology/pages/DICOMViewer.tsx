import { useState, useCallback, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { dicomService, type DicomStudy, type StudySeries } from '@services/dicom'
import { DICOMViewer as DicomViewerComponent } from '@components/DICOMViewer'
import { ImageToolbar } from '@components/ImageToolbar'
import { StudyBrowser } from '@components/StudyBrowser'
import { AIAnnotation } from '@components/AIAnnotation'
import type { Tool } from '@components/DICOMViewer'

type LayoutType = '1x1' | '1x2' | '2x1' | '2x2' | '3x3'

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

export function DICOMViewerPage() {
  const [searchParams] = useSearchParams()
  const studyUidParam = searchParams.get('studyUid')
  const seriesUidParam = searchParams.get('seriesUid')

  const [studies, setStudies] = useState<DicomStudy[]>([])
  const [selectedStudy, setSelectedStudy] = useState<DicomStudy | null>(null)
  const [selectedSeries, setSelectedSeries] = useState<StudySeries | null>(null)
  const [imageIds, setImageIds] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [activeTool, setActiveTool] = useState<Tool>('wwwc')
  const [layout, setLayout] = useState<LayoutType>('1x1')
  const [showAI, setShowAI] = useState(false)
  const [aiLoading, setAiLoading] = useState(false)
  const [aiAnnotations, setAiAnnotations] = useState<Annotation[]>([])
  const [isFullScreen, setIsFullScreen] = useState(false)
  const [currentSeriesIndex, setCurrentSeriesIndex] = useState(0)
  const [showSeriesList, setShowSeriesList] = useState(true)

  const fetchStudies = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await dicomService.searchStudies({ limit: 20 })
      const items = res.items || []
      setStudies(items)

      if (studyUidParam) {
        const study = items.find(s => s.study_uid === studyUidParam)
        if (study) {
          setSelectedStudy(study)
          const series = study.series || []
          if (seriesUidParam) {
            const ser = series.find(s => s.series_uid === seriesUidParam)
            if (ser) {
              setSelectedSeries(ser)
              setCurrentSeriesIndex(series.indexOf(ser))
            }
          }
          if (series.length > 0 && !selectedSeries) {
            setSelectedSeries(series[0])
          }
        }
      } else if (items.length > 0) {
        setSelectedStudy(items[0])
        if (items[0].series?.length > 0) {
          setSelectedSeries(items[0].series[0])
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'فشل تحميل الدراسات')
    } finally {
      setLoading(false)
    }
  }, [studyUidParam, seriesUidParam])

  useEffect(() => {
    fetchStudies()
  }, [fetchStudies])

  useEffect(() => {
    if (selectedStudy && selectedSeries) {
      // Generate image IDs for the selected series
      const ids: string[] = []
      const instanceCount = selectedSeries.number_of_instances || 10
      for (let i = 1; i <= instanceCount; i++) {
        ids.push(dicomService.getWadoUri(
          selectedStudy.study_uid,
          selectedSeries.series_uid,
          `instance_${i}`
        ))
      }
      setImageIds(ids)
    }
  }, [selectedStudy, selectedSeries])

  const handleStudySelect = useCallback((study: DicomStudy) => {
    setSelectedStudy(study)
    if (study.series?.length > 0) {
      setSelectedSeries(study.series[0])
      setCurrentSeriesIndex(0)
    }
  }, [])

  const handleSeriesSelect = useCallback((study: DicomStudy, series: StudySeries) => {
    setSelectedStudy(study)
    setSelectedSeries(series)
    setCurrentSeriesIndex((study.series || []).indexOf(series))
  }, [])

  const handleToolChange = useCallback((tool: Tool) => {
    setActiveTool(tool)
  }, [])

  const handleLayoutChange = useCallback((newLayout: LayoutType) => {
    setLayout(newLayout)
  }, [])

  const handleReset = useCallback(() => {
    setActiveTool('wwwc')
  }, [])

  const handleInvert = useCallback(() => {
    // Invert handled by viewer internal state
  }, [])

  const handleRotate = useCallback(() => {
    // Rotate handled by viewer internal state
  }, [])

  const handleFlipH = useCallback(() => {
    // Flip handled by viewer internal state
  }, [])

  const handleFlipV = useCallback(() => {
    // Flip handled by viewer internal state
  }, [])

  const handleScreenshot = useCallback(() => {
    const viewer = document.querySelector('.dicom-viewer canvas') as HTMLCanvasElement
    if (viewer) {
      const link = document.createElement('a')
      link.download = `screenshot_${Date.now()}.png`
      link.href = viewer.toDataURL()
      link.click()
    }
  }, [])

  const handleFullScreen = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().then(() => setIsFullScreen(true))
    } else {
      document.exitFullscreen().then(() => setIsFullScreen(false))
    }
  }, [])

  const handleRunAI = useCallback(async () => {
    if (!selectedStudy) return
    setAiLoading(true)
    try {
      // Simulate AI detection
      await new Promise(resolve => setTimeout(resolve, 2000))
      const mockAnnotations: Annotation[] = [
        {
          id: 'ai_001', type: 'nodule', label: 'عقدة رئوية', confidence: 0.92,
          x: 0.3, y: 0.4, width: 0.05, height: 0.05, probability: 0.88,
          finding: 'عقدة صلبة في الفص العلوي الأيمن بقياس 8 مم', rads_relevant: true,
          suggested_rads: 'RADS-3'
        },
        {
          id: 'ai_002', type: 'calcification', label: 'تكلس', confidence: 0.78,
          x: 0.6, y: 0.3, width: 0.03, height: 0.03, probability: 0.72,
          finding: 'تكلسات وعائية في المنصف', rads_relevant: false
        }
      ]
      setAiAnnotations(mockAnnotations)
      setShowAI(true)
    } catch {
      console.error('AI analysis failed')
    } finally {
      setAiLoading(false)
    }
  }, [selectedStudy])

  const handleAcceptAnnotation = useCallback((id: string) => {
    setAiAnnotations(prev => prev.filter(a => a.id !== id))
  }, [])

  const handleRejectAnnotation = useCallback((id: string) => {
    setAiAnnotations(prev => prev.filter(a => a.id !== id))
  }, [])

  if (loading) {
    return (
      <div style={{ display: 'flex', gap: 16, height: '100%' }}>
        <div className="card" style={{ width: 300 }}>
          <div className="skeleton" style={{ height: 40, marginBottom: 16 }} />
          <div className="skeleton" style={{ height: 500 }} />
        </div>
        <div className="card" style={{ flex: 1 }}>
          <div className="skeleton" style={{ height: '100%' }} />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">⚠️</div>
        <p style={{ color: 'var(--text-danger)' }}>{error}</p>
        <button className="btn btn-primary mt-md" onClick={fetchStudies}>إعادة</button>
      </div>
    )
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      backgroundColor: '#000'
    }}>
      {/* Toolbar */}
      <ImageToolbar
        activeTool={activeTool}
        onToolChange={handleToolChange}
        layout={layout}
        onLayoutChange={handleLayoutChange}
        onReset={handleReset}
        onInvert={handleInvert}
        onRotate={handleRotate}
        onFlipH={handleFlipH}
        onFlipV={handleFlipV}
        onScreenshot={handleScreenshot}
        onFullScreen={handleFullScreen}
        isFullScreen={isFullScreen}
        seriesCount={selectedStudy?.series?.length || 0}
        currentSeries={currentSeriesIndex}
        onSeriesChange={(idx) => {
          const series = selectedStudy?.series
          if (series && series[idx]) {
            setSelectedSeries(series[idx])
            setCurrentSeriesIndex(idx)
          }
        }}
      />

      {/* Main content */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Study browser sidebar */}
        {showSeriesList && (
          <div style={{
            width: 280,
            overflowY: 'auto',
            borderInlineEnd: '1px solid rgba(255,255,255,0.1)',
            flexShrink: 0
          }}>
            <StudyBrowser
              studies={studies}
              selectedStudyUid={selectedStudy?.study_uid}
              selectedSeriesUid={selectedSeries?.series_uid}
              onStudySelect={handleStudySelect}
              onSeriesSelect={handleSeriesSelect}
            />
          </div>
        )}

        {/* Viewer */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative' }}>
          <DicomViewerComponent
            studyUid={selectedStudy?.study_uid || ''}
            imageIds={imageIds}
            activeTool={activeTool}
            layout={layout}
            className="flex-1"
          />

          {/* Only show AI if we have a study */}
          {selectedStudy && (
            <div style={{
              position: 'absolute',
              top: 8,
              insetInlineEnd: 8,
              zIndex: 10
            }}>
              <button
                className="btn btn-sm"
                style={{
                  backgroundColor: 'rgba(0,0,0,0.7)',
                  color: 'white',
                  border: '1px solid rgba(255,255,255,0.2)'
                }}
                onClick={handleRunAI}
                disabled={aiLoading}
              >
                {aiLoading ? '🤖 جاري التحليل...' : '🤖 تحليل بالذكاء الاصطناعي'}
              </button>
            </div>
          )}

          {/* AI annotations panel */}
          {showAI && (
            <div style={{
              position: 'absolute',
              top: 48,
              insetInlineEnd: 8,
              width: 300,
              maxHeight: 'calc(100% - 60px)',
              overflowY: 'auto',
              zIndex: 10
            }}>
              <AIAnnotation
                annotations={aiAnnotations}
                visible={showAI}
                onToggleVisibility={() => setShowAI(!showAI)}
                onAnnotationClick={(ann) => console.log('Annotation clicked:', ann)}
                onAcceptAnnotation={handleAcceptAnnotation}
                onRejectAnnotation={handleRejectAnnotation}
                loading={aiLoading}
              />
            </div>
          )}
        </div>
      </div>

      {/* Toggle sidebar button */}
      <button
        onClick={() => setShowSeriesList(!showSeriesList)}
        style={{
          position: 'fixed',
          top: '50%',
          insetInlineStart: showSeriesList ? 280 : 0,
          transform: 'translateY(-50%)',
          backgroundColor: 'rgba(0,0,0,0.6)',
          color: 'white',
          border: '1px solid rgba(255,255,255,0.2)',
          borderRadius: '0 4px 4px 0',
          padding: '8px 4px',
          cursor: 'pointer',
          zIndex: 20,
          transition: 'inset-inline-start 150ms'
        }}
      >
        {showSeriesList ? '◀' : '▶'}
      </button>
    </div>
  )
}
