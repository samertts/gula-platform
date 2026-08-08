import { useState, useMemo } from 'react'

type CalendarEvent = {
  id: string
  title: string
  start: Date
  end: Date
  modality: string
  status: string
  patient: string
  room: string
}

type ScheduleCalendarProps = {
  events: CalendarEvent[]
  currentDate: Date
  onDateChange: (date: Date) => void
  onEventClick: (event: CalendarEvent) => void
  onSlotClick?: (date: Date, time: string) => void
  loading?: boolean
  view?: 'day' | 'week'
  onViewChange?: (view: 'day' | 'week') => void
}

const HOURS = Array.from({ length: 13 }, (_, i) => i + 7)

const STATUS_COLORS: Record<string, string> = {
  scheduled: '#3b82f6',
  confirmed: '#8b5cf6',
  arrived: '#f59e0b',
  in_progress: '#ef4444',
  completed: '#22c55e',
  missed: '#94a3b8',
  cancelled: '#64748b'
}

export function ScheduleCalendar({
  events,
  currentDate,
  onDateChange,
  onEventClick,
  onSlotClick,
  loading = false,
  view = 'day',
  onViewChange
}: ScheduleCalendarProps) {
  const days = useMemo(() => {
    if (view === 'day') return [currentDate]
    const start = new Date(currentDate)
    start.setDate(start.getDate() - start.getDay())
    return Array.from({ length: 7 }, (_, i) => {
      const d = new Date(start)
      d.setDate(d.getDate() + i)
      return d
    })
  }, [currentDate, view])

  const getEventsForDay = (date: Date) => {
    return events.filter(e =>
      e.start.getFullYear() === date.getFullYear() &&
      e.start.getMonth() === date.getMonth() &&
      e.start.getDate() === date.getDate()
    )
  }

  const navigateDate = (direction: -1 | 1) => {
    const newDate = new Date(currentDate)
    newDate.setDate(newDate.getDate() + direction * (view === 'week' ? 7 : 1))
    onDateChange(newDate)
  }

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('ar-IQ', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('ar-IQ', { hour: '2-digit', minute: '2-digit', hour12: true })
  }

  const formatDateShort = (date: Date) => {
    return date.toLocaleDateString('ar-IQ', { weekday: 'short', day: 'numeric' })
  }

  if (loading) {
    return (
      <div className="card">
        <div className="skeleton" style={{ height: 40, marginBottom: 16 }} />
        <div className="skeleton" style={{ height: 400 }} />
      </div>
    )
  }

  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 16px',
        borderBottom: '1px solid var(--border-primary)',
        backgroundColor: 'var(--bg-secondary)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button className="btn btn-sm btn-ghost" onClick={() => navigateDate(-1)}>‹</button>
          <span style={{ fontWeight: 600, fontSize: '0.95rem', minWidth: 200, textAlign: 'center' }}>
            {formatDate(currentDate)}
          </span>
          <button className="btn btn-sm btn-ghost" onClick={() => navigateDate(1)}>›</button>
          <button className="btn btn-sm btn-secondary" onClick={() => onDateChange(new Date())}>اليوم</button>
        </div>

        {onViewChange && (
          <div style={{ display: 'flex', gap: 4 }}>
            <button
              className={`btn btn-sm ${view === 'day' ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => onViewChange('day')}
            >
              يوم
            </button>
            <button
              className={`btn btn-sm ${view === 'week' ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => onViewChange('week')}
            >
              أسبوع
            </button>
          </div>
        )}
      </div>

      {/* Day headers (week view) */}
      {view === 'week' && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: '60px repeat(7, 1fr)',
          borderBottom: '1px solid var(--border-primary)'
        }}>
          <div style={{ padding: 8, fontSize: '0.7rem', color: 'var(--text-tertiary)' }}></div>
          {days.map((day, i) => (
            <div key={i} style={{
              padding: '4px 8px',
              fontSize: '0.75rem',
              fontWeight: day.toDateString() === new Date().toDateString() ? 700 : 400,
              color: day.toDateString() === new Date().toDateString() ? 'var(--accent-primary)' : 'var(--text-secondary)',
              textAlign: 'center',
              backgroundColor: day.toDateString() === new Date().toDateString() ? 'var(--accent-primary-light)' : undefined
            }}>
              {formatDateShort(day)}
            </div>
          ))}
        </div>
      )}

      {/* Time grid */}
      <div style={{ overflowY: 'auto', maxHeight: 500 }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: view === 'week' ? '60px repeat(7, 1fr)' : '60px 1fr'
        }}>
          {HOURS.map(hour => (
            <>
              {/* Time label */}
              <div key={`time-${hour}`} style={{
                padding: '4px',
                fontSize: '0.7rem',
                color: 'var(--text-tertiary)',
                textAlign: 'center',
                borderBottom: '1px solid var(--border-primary)',
                borderInlineEnd: '1px solid var(--border-primary)',
                alignSelf: 'start',
                position: 'sticky',
                start: 0
              }}>
                {hour.toString().padStart(2, '0')}:00
              </div>

              {/* Columns */}
              {days.map(day => {
                const cellKey = `${day.toISOString()}-${hour}`
                const dayEvents = getEventsForDay(day).filter(e =>
                  e.start.getHours() === hour
                )

                return (
                  <div
                    key={cellKey}
                    onClick={() => onSlotClick?.(day, `${hour.toString().padStart(2, '0')}:00`)}
                    style={{
                      minHeight: 60,
                      borderBottom: '1px solid var(--border-primary)',
                      borderInlineEnd: '1px solid var(--border-primary)',
                      padding: 2,
                      cursor: onSlotClick ? 'pointer' : 'default',
                      position: 'relative',
                      backgroundColor: day.toDateString() === new Date().toDateString() && new Date().getHours() === hour
                        ? 'rgba(59,130,246,0.05)' : undefined
                    }}
                  >
                    {dayEvents.map(event => (
                      <div
                        key={event.id}
                        onClick={e => { e.stopPropagation(); onEventClick(event) }}
                        style={{
                          padding: '2px 6px',
                          marginBottom: 2,
                          borderRadius: 4,
                          fontSize: '0.7rem',
                          cursor: 'pointer',
                          backgroundColor: STATUS_COLORS[event.status] || '#3b82f6',
                          color: 'white',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}
                        title={`${event.patient} - ${event.title}`}
                      >
                        {formatTime(event.start)} {event.patient}
                      </div>
                    ))}
                  </div>
                )
              })}
            </>
          ))}
        </div>
      </div>

      {/* Stats summary */}
      <div style={{
        display: 'flex',
        gap: 16,
        padding: '8px 16px',
        borderTop: '1px solid var(--border-primary)',
        backgroundColor: 'var(--bg-secondary)',
        fontSize: '0.75rem'
      }}>
        <span style={{ color: 'var(--text-tertiary)' }}>
          المجموع: <strong style={{ color: 'var(--text-primary)' }}>{events.length}</strong>
        </span>
        {Object.entries(STATUS_COLORS).map(([status, color]) => {
          const count = events.filter(e => e.status === status).length
          if (count === 0) return null
          return (
            <span key={status} style={{ color: 'var(--text-tertiary)' }}>
              <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', backgroundColor: color, marginInlineEnd: 4 }} />
              {status === 'scheduled' ? 'مجدول' :
               status === 'confirmed' ? 'مؤكد' :
               status === 'arrived' ? 'وصل' :
               status === 'in_progress' ? 'قيد الإجراء' :
               status === 'completed' ? 'مكتمل' :
               status === 'missed' ? 'متغيب' : 'ملغي'}: {count}
            </span>
          )
        })}
      </div>
    </div>
  )
}
