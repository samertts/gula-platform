import React from 'react'

interface StockIndicatorProps {
  current: number
  reorderLevel: number
  maxLevel?: number
  showLabel?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export default function StockIndicator({
  current,
  reorderLevel,
  maxLevel,
  showLabel = true,
  size = 'md',
}: StockIndicatorProps) {
  const ratio = reorderLevel > 0 ? current / reorderLevel : 1

  let level: 'critical' | 'low' | 'adequate' | 'overstock'
  let color: string

  if (current <= 0) {
    level = 'critical'
    color = 'var(--accent-danger)'
  } else if (ratio <= 0.5) {
    level = 'critical'
    color = 'var(--accent-danger)'
  } else if (ratio <= 1) {
    level = 'low'
    color = 'var(--accent-warning)'
  } else if (maxLevel && current > maxLevel) {
    level = 'overstock'
    color = 'var(--accent-info)'
  } else {
    level = 'adequate'
    color = 'var(--accent-success)'
  }

  const barHeight = size === 'sm' ? 6 : size === 'lg' ? 12 : 8
  const barWidth = size === 'sm' ? 60 : size === 'lg' ? 120 : 80

  const fillPercent = Math.min(100, (current / Math.max(reorderLevel * 2, 1)) * 100)

  const labels: Record<string, string> = {
    critical: 'مخزون حرج',
    low: 'مخزون منخفض',
    adequate: 'مخزون كاف',
    overstock: 'مخزون زائد',
  }

  return (
    <div
      className="stock-indicator"
      style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
      role="img"
      aria-label={`مستوى المخزون: ${labels[level]}, الكمية: ${current}, حد إعادة الطلب: ${reorderLevel}`}
    >
      <div
        style={{
          width: barWidth,
          height: barHeight,
          background: 'var(--bg-tertiary)',
          borderRadius: '999px',
          overflow: 'hidden',
          flexShrink: 0,
        }}
      >
        <div
          style={{
            width: `${fillPercent}%`,
            height: '100%',
            background: color,
            borderRadius: '999px',
            transition: 'width 0.3s ease',
            minWidth: current > 0 ? '4px' : '0',
          }}
        />
      </div>
      {showLabel && (
        <span
          style={{
            fontSize: '0.75rem',
            color,
            fontWeight: 600,
            whiteSpace: 'nowrap',
          }}
        >
          {current} / {reorderLevel}
        </span>
      )}
    </div>
  )
}
