import type { Tool } from './DICOMViewer'

type LayoutType = '1x1' | '1x2' | '2x1' | '2x2' | '3x3'

const tools: { id: Tool; label: string; icon: string }[] = [
  { id: 'wwwc', label: 'نافذة/مستوى', icon: '◐' },
  { id: 'pan', label: 'تحريك', icon: '✋' },
  { id: 'zoom', label: 'تكبير', icon: '🔍' },
  { id: 'magnify', label: 'عدسة', icon: '🔎' },
  { id: 'length', label: 'قياس طول', icon: '📏' },
  { id: 'angle', label: 'قياس زاوية', icon: '📐' },
  { id: 'elliptical', label: 'بيضاوي', icon: '⭕' },
  { id: 'rectangle', label: 'مستطيل', icon: '⬜' },
  { id: 'measure', label: 'قياس عام', icon: '📊' }
]

const layouts: { id: LayoutType; label: string }[] = [
  { id: '1x1', label: '1×1' },
  { id: '1x2', label: '1×2' },
  { id: '2x1', label: '2×1' },
  { id: '2x2', label: '2×2' },
  { id: '3x3', label: '3×3' }
]

type ImageToolbarProps = {
  activeTool: Tool
  onToolChange: (tool: Tool) => void
  layout: LayoutType
  onLayoutChange: (layout: LayoutType) => void
  onReset: () => void
  onInvert: () => void
  onRotate: () => void
  onFlipH: () => void
  onFlipV: () => void
  onScreenshot: () => void
  onFullScreen: () => void
  isFullScreen: boolean
  seriesCount: number
  currentSeries: number
  onSeriesChange?: (index: number) => void
}

export function ImageToolbar({
  activeTool,
  onToolChange,
  layout,
  onLayoutChange,
  onReset,
  onInvert,
  onRotate,
  onFlipH,
  onFlipV,
  onScreenshot,
  onFullScreen,
  isFullScreen,
  seriesCount,
  currentSeries,
  onSeriesChange
}: ImageToolbarProps) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '2px',
      padding: '4px 8px',
      backgroundColor: 'var(--bg-secondary)',
      borderBottom: '1px solid var(--border-primary)',
      height: 'var(--viewer-toolbar-height)',
      overflowX: 'auto',
      flexShrink: 0
    }}>
      {/* Tool buttons */}
      {tools.map(tool => (
        <button
          key={tool.id}
          className={`btn btn-sm ${activeTool === tool.id ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => onToolChange(tool.id)}
          title={tool.label}
          style={{ fontSize: '0.75rem', padding: '4px 6px', minWidth: '32px' }}
        >
          {tool.icon}
        </button>
      ))}

      <div className="divider" style={{ height: 24, margin: '0 8px' }} />

      {/* Layout selector */}
      {layouts.map(l => (
        <button
          key={l.id}
          className={`btn btn-sm ${layout === l.id ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => onLayoutChange(l.id)}
          title={l.label}
        >
          {l.label}
        </button>
      ))}

      <div className="divider" style={{ height: 24, margin: '0 8px' }} />

      {/* Image manipulation */}
      <button className="btn btn-sm btn-ghost" onClick={onInvert} title="عكس الألوان">
        ◑ عكس
      </button>
      <button className="btn btn-sm btn-ghost" onClick={onRotate} title="تدوير">
        ↻ تدوير
      </button>
      <button className="btn btn-sm btn-ghost" onClick={onFlipH} title="قلب أفقي">
        ↔ قلب
      </button>
      <button className="btn btn-sm btn-ghost" onClick={onFlipV} title="قلب عمودي">
        ↕ قلب
      </button>
      <button className="btn btn-sm btn-ghost" onClick={onReset} title="إعادة تعيين">
        ↩ إعادة
      </button>

      <div className="divider" style={{ height: 24, margin: '0 8px' }} />

      {/* Series navigation */}
      {seriesCount > 1 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.75rem' }}>
          <button
            className="btn btn-sm btn-ghost"
            onClick={() => onSeriesChange?.(Math.max(0, currentSeries - 1))}
            disabled={currentSeries === 0}
          >
            ‹
          </button>
          <span style={{ color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
            سلسلة {currentSeries + 1}/{seriesCount}
          </span>
          <button
            className="btn btn-sm btn-ghost"
            onClick={() => onSeriesChange?.(Math.min(seriesCount - 1, currentSeries + 1))}
            disabled={currentSeries === seriesCount - 1}
          >
            ›
          </button>
        </div>
      )}

      <div style={{ flex: 1 }} />

      {/* Actions */}
      <button className="btn btn-sm btn-ghost" onClick={onScreenshot} title="لقطة شاشة">
        📷
      </button>
      <button className="btn btn-sm btn-ghost" onClick={onFullScreen} title={isFullScreen ? 'خروج' : 'شاشة كاملة'}>
        {isFullScreen ? '⛶ خروج' : '⛶ كامل'}
      </button>
    </div>
  )
}
