import { useRef, useEffect, useState, useCallback } from 'react'

export type Tool = 'pan' | 'zoom' | 'wwwc' | 'magnify' | 'measure' | 'angle' | 'length' | 'elliptical' | 'rectangle'

export type LayoutType = '1x1' | '1x2' | '2x1' | '2x2' | '3x3'

type ViewportState = {
  centerX: number
  centerY: number
  zoom: number
  windowWidth: number
  windowCenter: number
  invert: boolean
  rotation: number
  flipH: boolean
  flipV: boolean
}

export type DicomViewerProps = {
  studyUid: string
  seriesUid?: string
  instanceUid?: string
  imageIds: string[]
  activeTool?: Tool
  layout?: LayoutType
  onMeasurementAdded?: (measurement: unknown) => void
  onImageRendered?: (index: number) => void
  onSeriesChange?: (seriesUid: string) => void
  className?: string
  showOverlays?: boolean
}

export function DICOMViewer({
  studyUid,
  imageIds,
  activeTool = 'wwwc',
  layout = '1x1',
  onMeasurementAdded,
  onImageRendered,
  className = '',
  showOverlays = true
}: DicomViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [loading, setLoading] = useState(true)
  const [currentImage, setCurrentImage] = useState(0)
  const [viewportState, setViewportState] = useState<ViewportState>({
    centerX: 0, centerY: 0, zoom: 1,
    windowWidth: 256, windowCenter: 128,
    invert: false, rotation: 0, flipH: false, flipV: false
  })

  const drawImage = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas || !imageIds.length) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const img = new Image()
    img.onload = () => {
      const container = containerRef.current
      if (!container) return

      canvas.width = container.clientWidth
      canvas.height = container.clientHeight

      ctx.clearRect(0, 0, canvas.width, canvas.height)
      ctx.save()

      const cx = canvas.width / 2
      const cy = canvas.height / 2
      ctx.translate(cx, cy)
      ctx.scale(viewportState.flipH ? -1 : 1, viewportState.flipV ? -1 : 1)
      ctx.rotate((viewportState.rotation * Math.PI) / 180)
      ctx.scale(viewportState.zoom, viewportState.zoom)

      const scale = Math.min(
        canvas.width / img.width,
        canvas.height / img.height
      )
      ctx.drawImage(img, -img.width / 2, -img.height / 2, img.width, img.height)

      ctx.restore()
      setLoading(false)
      onImageRendered?.(currentImage)
    }
    img.onerror = () => setLoading(false)
    img.src = imageIds[currentImage] || imageIds[0]
  }, [imageIds, currentImage, viewportState, onImageRendered])

  useEffect(() => {
    drawImage()
    const handleResize = () => drawImage()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [drawImage])

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault()
    const delta = e.deltaY > 0 ? 0.9 : 1.1
    setViewportState(prev => ({
      ...prev,
      zoom: Math.max(0.1, Math.min(50, prev.zoom * delta))
    }))
  }, [])

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button !== 0) return
    const startX = e.clientX
    const startY = e.clientY
    const startState = { ...viewportState }

    const handleMouseMove = (me: MouseEvent) => {
      const dx = me.clientX - startX
      const dy = me.clientY - startY

      if (activeTool === 'pan') {
        setViewportState(prev => ({
          ...prev,
          centerX: startState.centerX + dx / prev.zoom,
          centerY: startState.centerY + dy / prev.zoom
        }))
      } else if (activeTool === 'wwwc') {
        setViewportState(prev => ({
          ...prev,
          windowWidth: Math.max(1, startState.windowWidth + dx),
          windowCenter: startState.windowCenter + dy
        }))
      }
    }

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }, [activeTool, viewportState])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowLeft':
        setCurrentImage(prev => Math.max(0, prev - 1))
        break
      case 'ArrowRight':
        setCurrentImage(prev => Math.min(imageIds.length - 1, prev + 1))
        break
      case 'r':
        setViewportState(prev => ({ ...prev, rotation: (prev.rotation + 90) % 360 }))
        break
      case 'i':
        setViewportState(prev => ({ ...prev, invert: !prev.invert }))
        break
    }
  }, [imageIds.length])

  return (
    <div
      ref={containerRef}
      className={`dicom-viewer ${className}`}
      style={{
        position: 'relative',
        width: '100%',
        height: '100%',
        backgroundColor: '#000',
        overflow: 'hidden',
        cursor: activeTool === 'pan' ? 'grab' : activeTool === 'zoom' ? 'zoom-in' : 'default',
        outline: 'none'
      }}
      tabIndex={0}
      onWheel={handleWheel}
      onMouseDown={handleMouseDown}
      onKeyDown={handleKeyDown}
      role="img"
      aria-label="DICOM Image Viewer"
    >
      <canvas
        ref={canvasRef}
        style={{
          width: '100%',
          height: '100%',
          display: 'block'
        }}
      />

      {loading && (
        <div style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontSize: '0.875rem',
          backgroundColor: 'rgba(0,0,0,0.5)'
        }}>
          جاري تحميل الصورة...
        </div>
      )}

      {showOverlays && (
        <>
          <div style={{
            position: 'absolute',
            top: 8,
            insetInlineStart: 8,
            color: 'rgba(255,255,255,0.7)',
            fontSize: '0.75rem',
            fontFamily: 'monospace',
            pointerEvents: 'none',
            direction: 'ltr'
          }}>
            {currentImage + 1} / {imageIds.length}
          </div>

          <div style={{
            position: 'absolute',
            bottom: 8,
            insetInlineStart: 8,
            color: 'rgba(255,255,255,0.7)',
            fontSize: '0.7rem',
            fontFamily: 'monospace',
            pointerEvents: 'none',
            direction: 'ltr'
          }}>
            WW: {viewportState.windowWidth.toFixed(0)} WC: {viewportState.windowCenter.toFixed(0)}
            {' | '}Zoom: {viewportState.zoom.toFixed(2)}x
          </div>

          <div style={{
            position: 'absolute',
            bottom: 8,
            insetInlineEnd: 8,
            color: 'rgba(255,255,255,0.5)',
            fontSize: '0.65rem',
            fontFamily: 'monospace',
            pointerEvents: 'none',
            direction: 'ltr'
          }}>
            {studyUid.substring(0, 12)}...
          </div>
        </>
      )}
    </div>
  )
}
