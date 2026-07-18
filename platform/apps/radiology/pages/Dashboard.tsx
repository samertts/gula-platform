import { useState, useEffect, useCallback } from 'react'
import { worklistService, type WorklistItem } from '@services/worklist'
import { schedulingService, type Appointment } from '@services/scheduling'
import { reportingService, type CriticalFinding } from '@services/reporting'

type DashboardStats = {
  total_today: number
  completed: number
  scheduled: number
  in_progress: number
  critical_findings: number
  avg_reporting_time: number
  modality_breakdown: Record<string, number>
  urgent_count: number
}

export function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    total_today: 0, completed: 0, scheduled: 0, in_progress: 0,
    critical_findings: 0, avg_reporting_time: 0, modality_breakdown: {},
    urgent_count: 0
  })
  const [recentWorklist, setRecentWorklist] = useState<WorklistItem[]>([])
  const [upcomingAppointments, setUpcomingAppointments] = useState<Appointment[]>([])
  const [pendingCriticalFindings, setPendingCriticalFindings] = useState<CriticalFinding[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadDashboard = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const today = new Date().toISOString().split('T')[0]

      const [worklistRes, appointmentsRes, criticalRes] = await Promise.all([
        worklistService.getWorklist({ date_from: today, date_to: today }),
        schedulingService.getAppointments({ date_from: today, date_to: today }),
        reportingService.getPendingCriticalFindings().catch(() => [])
      ])

      const items = worklistRes.items
      const apps = appointmentsRes.items

      const modalityBreakdown: Record<string, number> = {}
      items.forEach(item => {
        modalityBreakdown[item.modality] = (modalityBreakdown[item.modality] || 0) + 1
      })

      setStats({
        total_today: items.length + apps.length,
        completed: items.filter(i => i.status === 'completed').length,
        scheduled: items.filter(i => i.status === 'scheduled').length + apps.filter(a => a.status === 'scheduled' || a.status === 'confirmed').length,
        in_progress: items.filter(i => i.status === 'started' || i.status === 'arrived').length,
        critical_findings: criticalRes.length,
        avg_reporting_time: 28,
        modality_breakdown: modalityBreakdown,
        urgent_count: items.filter(i => i.priority === 'urgent' || i.priority === 'stat').length
      })
      setRecentWorklist(items.slice(0, 8))
      setUpcomingAppointments(apps.slice(0, 5))
      setPendingCriticalFindings(Array.isArray(criticalRes) ? criticalRes : [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'فشل تحميل البيانات')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadDashboard()
    const interval = setInterval(loadDashboard, 60000)
    return () => clearInterval(interval)
  }, [loadDashboard])

  const getModalityColor = (modality: string) => {
    const colors: Record<string, string> = {
      CT: '#3b82f6', MR: '#8b5cf6', US: '#22c55e', XA: '#ef4444',
      CR: '#f59e0b', DX: '#f59e0b', MG: '#ec4899', NM: '#06b6d4', PT: '#14b8a6'
    }
    return colors[modality] || '#94a3b8'
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div className="grid grid-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="card">
              <div className="skeleton" style={{ height: 16, width: '60%', marginBottom: 12 }} />
              <div className="skeleton" style={{ height: 32, width: '40%' }} />
            </div>
          ))}
        </div>
        <div className="card" style={{ height: 300 }}>
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
        <button className="btn btn-primary mt-md" onClick={loadDashboard}>إعادة المحاولة</button>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>لوحة التحكم</h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-tertiary)' }}>
            {new Date().toLocaleDateString('ar-IQ', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary btn-sm" onClick={loadDashboard}>↻ تحديث</button>
        </div>
      </div>

      {/* Stats cards */}
      <div className="grid grid-4">
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginBottom: 8 }}>إجمالي اليوم</div>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--accent-primary)' }}>{stats.total_today}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginTop: 4 }}>فحص</div>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginBottom: 8 }}>مكتمل</div>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--accent-success)' }}>{stats.completed}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginTop: 4 }}>
            {stats.total_today > 0 ? `${Math.round(stats.completed / stats.total_today * 100)}%` : '0%'}
          </div>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <div           style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginBottom: 8 }}>قيد الإجراء</div>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--accent-warning)' }}>{stats.in_progress}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginTop: 4 }}>
            {stats.urgent_count > 0 && <span className="badge badge-danger">عاجل: {stats.urgent_count}</span>}
          </div>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginBottom: 8 }}>نتائج حرجة</div>
          <div style={{
            fontSize: '2rem',
            fontWeight: 700,
            color: stats.critical_findings > 0 ? 'var(--accent-danger)' : 'var(--accent-success)'
          }}>
            {stats.critical_findings > 0 ? `🚨 ${stats.critical_findings}` : '0'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginTop: 4 }}>
            {stats.critical_findings > 0 ? 'بحاجة للمتابعة' : 'لا توجد'}
          </div>
        </div>
      </div>

      <div className="grid grid-2">
        {/* Recent Worklist */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div className="card-header" style={{ padding: '12px 16px', margin: 0 }}>
            <h3 className="card-title" style={{ fontSize: '0.95rem' }}>آخر الفحوصات</h3>
            <button className="btn btn-sm btn-ghost">عرض الكل →</button>
          </div>
          <div>
            {recentWorklist.length === 0 ? (
              <div className="empty-state" style={{ padding: '2rem' }}>
                <p style={{ fontSize: '0.85rem' }}>لا توجد فحوصات اليوم</p>
              </div>
            ) : (
              recentWorklist.map(item => (
                <div key={item.id} style={{
                  padding: '10px 16px',
                  borderBottom: '1px solid var(--border-primary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12
                }}>
                  <span style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '2px 6px',
                    borderRadius: 4,
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    color: 'white',
                    backgroundColor: getModalityColor(item.modality),
                    minWidth: 28
                  }}>
                    {item.modality}
                  </span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '0.85rem', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {item.patient_name}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
                      {item.procedure_description || item.study_description}
                    </div>
                  </div>
                  <span className={`badge ${
                    item.status === 'completed' ? 'badge-success' :
                    item.status === 'started' || item.status === 'arrived' ? 'badge-warning' :
                    item.status === 'scheduled' ? 'badge-info' : 'badge-neutral'
                  }`}>
                    {item.status === 'completed' ? 'مكتمل' :
                     item.status === 'started' ? 'قيد الإجراء' :
                     item.status === 'arrived' ? 'وصل' :
                     item.status === 'scheduled' ? 'مجدول' : 'ملغي'}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Pending critical findings */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div className="card-header" style={{ padding: '12px 16px', margin: 0 }}>
            <h3 className="card-title" style={{ fontSize: '0.95rem' }}>
              النتائج الحرجة المعلقة
              {pendingCriticalFindings.length > 0 && (
                <span className="badge badge-danger" style={{ marginInlineStart: 8 }}>
                  {pendingCriticalFindings.length}
                </span>
              )}
            </h3>
          </div>
          <div>
            {pendingCriticalFindings.length === 0 ? (
              <div className="empty-state" style={{ padding: '2rem' }}>
                <div style={{ fontSize: '2rem', marginBottom: 8 }}>✅</div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-success)' }}>لا توجد نتائج حرجة معلقة</p>
              </div>
            ) : (
              pendingCriticalFindings.map(finding => (
                <div key={finding.id} style={{
                  padding: '12px 16px',
                  borderBottom: '1px solid var(--border-primary)',
                  borderInlineStart: '3px solid var(--accent-danger)'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span className={`badge ${finding.severity === 'critical' ? 'badge-danger' : 'badge-warning'}`}>
                      {finding.severity === 'critical' ? 'حرج' : finding.severity === 'urgent' ? 'عاجل' : 'هام'}
                    </span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      إلى: {finding.communicated_to}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.85rem' }}>{finding.finding}</p>
                  {!finding.acknowledged && (
                    <div style={{ marginTop: 8 }}>
                      <button className="btn btn-sm btn-primary">تأكيد الاستلام</button>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Modality breakdown */}
      <div className="grid grid-2">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title" style={{ fontSize: '0.95rem' }}>توزيع الفحوصات حسب الجهاز</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {Object.entries(stats.modality_breakdown).length === 0 ? (
              <p style={{ fontSize: '0.85rem', color: 'var(--text-tertiary)', textAlign: 'center', padding: '1rem' }}>
                لا توجد بيانات
              </p>
            ) : (
              Object.entries(stats.modality_breakdown)
                .sort(([, a], [, b]) => b - a)
                .map(([modality, count]) => {
                  const total = Object.values(stats.modality_breakdown).reduce((a, b) => a + b, 0)
                  const pct = total > 0 ? (count / total) * 100 : 0
                  return (
                    <div key={modality} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        padding: '2px 6px',
                        borderRadius: 4,
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        color: 'white',
                        backgroundColor: getModalityColor(modality),
                        minWidth: 28
                      }}>
                        {modality}
                      </span>
                      <div style={{
                        flex: 1,
                        height: 20,
                        backgroundColor: 'var(--bg-tertiary)',
                        borderRadius: 4,
                        overflow: 'hidden',
                        position: 'relative'
                      }}>
                        <div style={{
                          width: `${pct}%`,
                          height: '100%',
                          backgroundColor: getModalityColor(modality),
                          borderRadius: 4,
                          transition: 'width 300ms ease'
                        }} />
                      </div>
                      <span style={{ fontSize: '0.8rem', fontWeight: 600, minWidth: 30, textAlign: 'end' }}>
                        {count}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', minWidth: 40, textAlign: 'end' }}>
                        {pct.toFixed(0)}%
                      </span>
                    </div>
                  )
                })
            )}
          </div>
        </div>

        {/* Upcoming appointments */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div className="card-header" style={{ padding: '12px 16px', margin: 0 }}>
            <h3 className="card-title" style={{ fontSize: '0.95rem' }}>المواعيد القادمة</h3>
          </div>
          <div>
            {upcomingAppointments.length === 0 ? (
              <div className="empty-state" style={{ padding: '2rem' }}>
                <p style={{ fontSize: '0.85rem' }}>لا توجد مواعيد قادمة</p>
              </div>
            ) : (
              upcomingAppointments.map(app => (
                <div key={app.id} style={{
                  padding: '10px 16px',
                  borderBottom: '1px solid var(--border-primary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12
                }}>
                  <div style={{ textAlign: 'center', minWidth: 48 }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)' }}>{app.scheduled_date}</div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-primary)' }}>{app.scheduled_time}</div>
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '0.85rem', fontWeight: 500 }}>{app.patient_name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
                      {app.procedure_description} — {app.room}
                    </div>
                  </div>
                  <span className={`badge ${
                    app.status === 'scheduled' ? 'badge-info' :
                    app.status === 'confirmed' ? 'badge-primary' : 'badge-neutral'
                  }`}>
                    {app.status === 'scheduled' ? 'مجدول' : app.status === 'confirmed' ? 'مؤكد' : app.status}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
