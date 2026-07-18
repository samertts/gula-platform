import { useState } from 'react'
import type { WorklistItem, WorklistStatus } from '@services/worklist'

const STATUS_CONFIG: Record<WorklistStatus, { label: string; className: string }> = {
  scheduled: { label: 'مجدول', className: 'badge-info' },
  arrived: { label: 'وصل', className: 'badge-primary' },
  started: { label: 'قيد الإجراء', className: 'badge-warning' },
  completed: { label: 'مكتمل', className: 'badge-success' },
  cancelled: { label: 'ملغي', className: 'badge-neutral' }
}

const PRIORITY_CONFIG = {
  stat: { label: 'طوارئ', className: 'badge-danger' },
  urgent: { label: 'عاجل', className: 'badge-warning' },
  routine: { label: 'روتيني', className: 'badge-info' }
}

type WorklistTableProps = {
  items: WorklistItem[]
  loading?: boolean
  selectedId?: string
  onSelect: (item: WorklistItem) => void
  onStatusChange: (id: string, status: WorklistStatus) => void
  emptyMessage?: string
}

export function WorklistTable({
  items,
  loading = false,
  selectedId,
  onSelect,
  onStatusChange,
  emptyMessage = 'لا توجد عناصر في قائمة العمل'
}: WorklistTableProps) {
  if (loading) {
    return (
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-primary)' }}>
          <div className="skeleton" style={{ height: 16, width: 200 }} />
        </div>
        {[1, 2, 3, 4, 5].map(i => (
          <div key={i} style={{ padding: '16px', borderBottom: '1px solid var(--border-primary)' }}>
            <div className="skeleton" style={{ height: 14, width: '40%', marginBottom: 8 }} />
            <div className="skeleton" style={{ height: 12, width: '60%' }} />
          </div>
        ))}
      </div>
    )
  }

  if (!items.length) {
    return (
      <div className="card empty-state">
        <div className="empty-state-icon">📋</div>
        <p>{emptyMessage}</p>
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

  const statusActions: WorklistStatus[] = ['scheduled', 'arrived', 'started', 'completed']

  return (
    <div className="card" style={{ padding: 0, overflow: 'auto' }}>
      <table className="data-table">
        <thead>
          <tr>
            <th>الحالة</th>
            <th>المريض</th>
            <th>الفحص</th>
            <th>الجهاز</th>
            <th>الموعد</th>
            <th>الطبيب المحول</th>
            <th>الأولوية</th>
            <th>إجراءات</th>
          </tr>
        </thead>
        <tbody>
          {items.map(item => (
            <tr
              key={item.id}
              className={selectedId === item.id ? 'selected' : ''}
              onClick={() => onSelect(item)}
              style={{ cursor: 'pointer' }}
            >
              <td>
                <span className={`badge ${STATUS_CONFIG[item.status]?.className || 'badge-neutral'}`}>
                  <span className="status-dot" style={{
                    backgroundColor: item.status === 'completed' ? 'var(--accent-success)' :
                      item.status === 'started' ? 'var(--accent-warning)' :
                      item.status === 'arrived' ? 'var(--accent-primary)' :
                      item.status === 'cancelled' ? 'var(--text-tertiary)' :
                      'var(--accent-info)',
                    marginInlineEnd: 6
                  }} />
                  {STATUS_CONFIG[item.status]?.label || item.status}
                </span>
              </td>
              <td>
                <div style={{ fontWeight: 500, fontSize: '0.875rem' }}>{item.patient_name}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
                  {item.patient_id} | {item.patient_age} | {item.patient_sex === 'M' ? 'ذكر' : item.patient_sex === 'F' ? 'أنثى' : 'آخر'}
                </div>
              </td>
              <td>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '1px 4px',
                    borderRadius: 3,
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    color: 'white',
                    backgroundColor: getModalityColor(item.modality),
                    minWidth: 22
                  }}>
                    {item.modality}
                  </span>
                  <span style={{ fontSize: '0.8rem' }}>{item.procedure_description || item.study_description}</span>
                </div>
              </td>
              <td style={{ fontSize: '0.8rem' }}>{item.scheduled_station}</td>
              <td style={{ fontSize: '0.8rem', whiteSpace: 'nowrap' }}>
                <div>{item.scheduled_date}</div>
                <div style={{ color: 'var(--text-tertiary)', fontSize: '0.75rem' }}>{item.scheduled_time}</div>
              </td>
              <td style={{ fontSize: '0.8rem' }}>{item.requesting_physician}</td>
              <td>
                <span className={`badge ${PRIORITY_CONFIG[item.priority]?.className || 'badge-neutral'}`}>
                  {PRIORITY_CONFIG[item.priority]?.label || item.priority}
                </span>
              </td>
              <td>
                <div style={{ display: 'flex', gap: 4 }}>
                  {statusActions.map(status => {
                    if (status === item.status ||
                      (status === 'scheduled' && item.status !== 'cancelled') ||
                      (status === 'arrived' && item.status !== 'scheduled') ||
                      (status === 'started' && item.status !== 'arrived') ||
                      (status === 'completed' && item.status !== 'started')) return null

                    const isNext =
                      (item.status === 'scheduled' && status === 'arrived') ||
                      (item.status === 'arrived' && status === 'started') ||
                      (item.status === 'started' && status === 'completed')

                    return (
                      <button
                        key={status}
                        className={`btn btn-sm ${isNext ? 'btn-primary' : 'btn-ghost'}`}
                        onClick={e => { e.stopPropagation(); onStatusChange(item.id, status) }}
                        title={STATUS_CONFIG[status].label}
                        style={{ fontSize: '0.7rem', padding: '2px 6px' }}
                      >
                        {STATUS_CONFIG[status].label}
                      </button>
                    )
                  })}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
