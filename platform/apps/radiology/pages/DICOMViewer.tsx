import { useState, useCallback, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { dicomService, type DicomStudy, type StudySeries } from '@services/dicom'
import { DICOMViewer as DicomViewerComponent } from '@components/DICOMViewer'
import { ImageToolbar } from '@components/ImageToolbar'
import { StudyBrowser } from '@components/StudyBrowser'
import type { Tool } from '@components/DICOMViewer'

type LayoutType = '1x1' | '1x2' | '2x1' | '2x2' | '3x3'

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

          {selectedStudy && (
            <div
              role="status"
              style={{
                position: 'absolute',
                top: 8,
                insetInlineEnd: 8,
                zIndex: 10,
                maxWidth: 360,
                padding: '8px 12px',
                borderRadius: 4,
                backgroundColor: 'rgba(0,0,0,0.78)',
                color: 'rgba(255,255,255,0.9)',
                border: '1px solid rgba(255,255,255,0.2)',
                fontSize: 12,
                lineHeight: 1.5,
              }}
            >
              التحليل الآلي غير متاح لهذه الدراسة حالياً. لن تُعرض استنتاجات سريرية اصطناعية؛ استخدم التقرير المعتمد من الخلفية.
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
