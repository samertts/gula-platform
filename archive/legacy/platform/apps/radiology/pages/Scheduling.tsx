import { useState, useEffect, useCallback } from 'react'
import { schedulingService, type Appointment, type AppointmentStatus, type Room } from '@services/scheduling'
import type { Modality } from '@services/dicom'
import { ScheduleCalendar } from '@components/ScheduleCalendar'

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

export function Scheduling() {
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [rooms, setRooms] = useState<Room[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentDate, setCurrentDate] = useState(new Date())
  const [view, setView] = useState<'day' | 'week'>('day')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null)
  const [modalityFilter, setModalityFilter] = useState<Modality | ''>('')

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const dateStr = currentDate.toISOString().split('T')[0]
      const weekEnd = new Date(currentDate)
      weekEnd.setDate(weekEnd.getDate() + 7)
      const weekEndStr = weekEnd.toISOString().split('T')[0]

      const params: Record<string, string> = {
        date_from: dateStr,
        date_to: view === 'week' ? weekEndStr : dateStr
      }
      if (modalityFilter) params.modality = modalityFilter

      const [appointmentsRes, roomsRes] = await Promise.all([
        schedulingService.getAppointments(params),
        schedulingService.getRooms().catch(() => [] as Room[])
      ])
      setAppointments(appointmentsRes.items)
      setRooms(Array.isArray(roomsRes) ? roomsRes : [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'فشل تحميل البيانات')
    } finally {
      setLoading(false)
    }
  }, [currentDate, view, modalityFilter])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const events: CalendarEvent[] = appointments.map(app => ({
    id: app.id,
    title: app.procedure_description,
    start: new Date(`${app.scheduled_date}T${app.scheduled_time}`),
    end: new Date(new Date(`${app.scheduled_date}T${app.scheduled_time}`).getTime() + (app.duration_minutes || 30) * 60000),
    modality: app.modality,
    status: app.status,
    patient: app.patient_name,
    room: app.room
  }))

  const handleEventClick = useCallback((event: CalendarEvent) => {
    const app = appointments.find(a => a.id === event.id)
    if (app) setSelectedAppointment(app)
  }, [appointments])

  const handleSlotClick = useCallback((date: Date, time: string) => {
    setCurrentDate(date)
    setShowCreateModal(true)
  }, [])

  const handleCreateAppointment = useCallback(async (data: Partial<Appointment>) => {
    try {
      await schedulingService.createAppointment(data as Appointment)
      setShowCreateModal(false)
      fetchData()
    } catch (err) {
      console.error('Failed to create appointment:', err)
    }
  }, [fetchData])

  const handleStatusChange = useCallback(async (id: string, status: AppointmentStatus) => {
    try {
      const updated = await schedulingService.updateAppointment(id, { status } as Partial<Appointment>)
      setAppointments(prev => prev.map(a => a.id === id ? updated : a))
    } catch (err) {
      console.error('Failed to update appointment:', err)
    }
  }, [])

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      scheduled: '#3b82f6', confirmed: '#8b5cf6', arrived: '#f59e0b',
      in_progress: '#ef4444', completed: '#22c55e', missed: '#94a3b8', cancelled: '#64748b'
    }
    return colors[status] || '#94a3b8'
  }

  const totalToday = appointments.length
  const completedToday = appointments.filter(a => a.status === 'completed').length
  const noShowToday = appointments.filter(a => a.status === 'missed').length

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>جدولة المواعيد</h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-tertiary)' }}>إدارة مواعيد فحوصات الأشعة</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
          + موعد جديد
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-4">
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--accent-primary)' }}>{totalToday}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>إجمالي المواعيد</div>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--accent-success)' }}>{completedToday}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>مكتمل</div>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--accent-warning)' }}>{totalToday - completedToday - noShowToday}</div>
          <div           style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>قيد الانتظار</div>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--accent-danger)' }}>{noShowToday}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>متغيب</div>
        </div>
      </div>

      {/* Modality filter */}
      <div style={{ display: 'flex', gap: 8 }}>
        <button
          className={`btn btn-sm ${modalityFilter === '' ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setModalityFilter('')}
        >
          الكل
        </button>
        {['CT', 'MR', 'US', 'XA', 'CR', 'DX', 'MG', 'NM', 'PT'].map(m => (
          <button
            key={m}
            className={`btn btn-sm ${modalityFilter === m ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setModalityFilter(m as Modality)}
          >
            {m}
          </button>
        ))}
      </div>

      {/* Calendar */}
      <ScheduleCalendar
        events={events}
        currentDate={currentDate}
        onDateChange={setCurrentDate}
        onEventClick={handleEventClick}
        onSlotClick={handleSlotClick}
        loading={loading}
        view={view}
        onViewChange={setView}
      />

      {error && (
        <div style={{ padding: 12, backgroundColor: 'rgba(239,68,68,0.1)', border: '1px solid var(--border-danger)', borderRadius: 8, color: 'var(--text-danger)', fontSize: '0.875rem' }}>
          {error}
          <button className="btn btn-sm btn-ghost" onClick={fetchData} style={{ marginInlineStart: 8 }}>إعادة</button>
        </div>
      )}

      {/* Create appointment modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 600 }}>
            <div className="modal-header">
              <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>موعد جديد</h2>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowCreateModal(false)}>✕</button>
            </div>
            <div className="modal-body">
              <CreateAppointmentForm
                defaultDate={currentDate.toISOString().split('T')[0]}
                rooms={rooms}
                onSubmit={handleCreateAppointment}
                onCancel={() => setShowCreateModal(false)}
              />
            </div>
          </div>
        </div>
      )}

      {/* Appointment detail modal */}
      {selectedAppointment && (
        <div className="modal-overlay" onClick={() => setSelectedAppointment(null)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 500 }}>
            <div className="modal-header">
              <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>تفاصيل الموعد</h2>
              <button className="btn btn-ghost btn-sm" onClick={() => setSelectedAppointment(null)}>✕</button>
            </div>
            <div className="modal-body">
              <div style={{ display: 'grid', gap: 16 }}>
                <div>
                  <label className="input-label">المريض</label>
                  <p style={{ fontSize: '1rem', fontWeight: 500 }}>{selectedAppointment.patient_name}</p>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div>
                    <label className="input-label">الفحص</label>
                    <p>{selectedAppointment.procedure_description}</p>
                  </div>
                  <div>
                    <label className="input-label">الجهاز</label>
                    <span className="badge badge-primary">{selectedAppointment.modality}</span>
                  </div>
                  <div>
                    <label className="input-label">التاريخ</label>
                    <p>{selectedAppointment.scheduled_date}</p>
                  </div>
                  <div>
                    <label className="input-label">الوقت</label>
                    <p>{selectedAppointment.scheduled_time}</p>
                  </div>
                  <div>
                    <label className="input-label">الغرفة</label>
                    <p>{selectedAppointment.room}</p>
                  </div>
                  <div>
                    <label className="input-label">المدة</label>
                    <p>{selectedAppointment.duration_minutes} دقيقة</p>
                  </div>
                </div>
                <div>
                  <label className="input-label">الحالة</label>
                  <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
                    {(['scheduled', 'confirmed', 'arrived', 'in_progress', 'completed', 'missed', 'cancelled'] as AppointmentStatus[]).map(status => (
                      <button
                        key={status}
                        className={`btn btn-sm ${selectedAppointment.status === status ? 'btn-primary' : 'btn-ghost'}`}
                        onClick={() => handleStatusChange(selectedAppointment.id, status)}
                        style={{ fontSize: '0.7rem' }}
                      >
                        {status === 'scheduled' ? 'مجدول' :
                         status === 'confirmed' ? 'مؤكد' :
                         status === 'arrived' ? 'وصل' :
                         status === 'in_progress' ? 'قيد الإجراء' :
                         status === 'completed' ? 'مكتمل' :
                         status === 'missed' ? 'متغيب' : 'ملغي'}
                      </button>
                    ))}
                  </div>
                </div>
                {selectedAppointment.notes && (
                  <div>
                    <label className="input-label">ملاحظات</label>
                    <p>{selectedAppointment.notes}</p>
                  </div>
                )}
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setSelectedAppointment(null)}>إغلاق</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function CreateAppointmentForm({
  defaultDate,
  rooms,
  onSubmit,
  onCancel
}: {
  defaultDate: string
  rooms: Room[]
  onSubmit: (data: Partial<Appointment>) => void
  onCancel: () => void
}) {
  const [form, setForm] = useState({
    patient_id: '',
    patient_name: '',
    patient_phone: '',
    study_description: '',
    modality: 'CT' as Modality,
    procedure_code: '',
    procedure_description: '',
    referring_physician: '',
    referring_department: '',
    scheduled_date: defaultDate,
    scheduled_time: '09:00',
    duration_minutes: 30,
    room: rooms[0]?.name || '',
    station: rooms[0]?.stations[0] || '',
    notes: '',
    contrast_required: false,
    contrast_details: '',
    notify_patient: true,
    created_by: ''
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(form as Partial<Appointment>)
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="grid grid-2">
        <div className="input-group">
          <label className="input-label">اسم المريض *</label>
          <input className="input" value={form.patient_name} onChange={e => setForm(p => ({ ...p, patient_name: e.target.value }))} required />
        </div>
        <div className="input-group">
          <label className="input-label">رقم المريض</label>
          <input className="input" value={form.patient_id} onChange={e => setForm(p => ({ ...p, patient_id: e.target.value }))} />
        </div>
        <div className="input-group">
          <label className="input-label">الفحص *</label>
          <input className="input" value={form.procedure_description} onChange={e => setForm(p => ({ ...p, procedure_description: e.target.value }))} required />
        </div>
        <div className="input-group">
          <label className="input-label">الجهاز</label>
          <select className="select" value={form.modality} onChange={e => setForm(p => ({ ...p, modality: e.target.value as Modality }))}>
            {['CT', 'MR', 'US', 'XA', 'CR', 'DX', 'MG', 'NM', 'PT'].map(m => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>
        <div className="input-group">
          <label className="input-label">التاريخ *</label>
          <input className="input" type="date" value={form.scheduled_date} onChange={e => setForm(p => ({ ...p, scheduled_date: e.target.value }))} required />
        </div>
        <div className="input-group">
          <label className="input-label">الوقت *</label>
          <input className="input" type="time" value={form.scheduled_time} onChange={e => setForm(p => ({ ...p, scheduled_time: e.target.value }))} required />
        </div>
        <div className="input-group">
          <label className="input-label">الغرفة</label>
          <select className="select" value={form.room} onChange={e => setForm(p => ({ ...p, room: e.target.value }))}>
            <option value="">اختر...</option>
            {rooms.map(r => (
              <option key={r.id} value={r.name}>{r.name}</option>
            ))}
          </select>
        </div>
        <div className="input-group">
          <label className="input-label">المدة (دقيقة)</label>
          <input className="input" type="number" min={5} max={120} value={form.duration_minutes} onChange={e => setForm(p => ({ ...p, duration_minutes: Number(e.target.value) }))} />
        </div>
      </div>
      <div className="input-group">
        <label className="input-label">الطبيب المحول</label>
        <input className="input" value={form.referring_physician} onChange={e => setForm(p => ({ ...p, referring_physician: e.target.value }))} />
      </div>
      <div className="input-group">
        <label className="input-label">ملاحظات</label>
        <textarea className="input" value={form.notes} onChange={e => setForm(p => ({ ...p, notes: e.target.value }))} rows={2} />
      </div>
      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
          <input type="checkbox" checked={form.contrast_required} onChange={e => setForm(p => ({ ...p, contrast_required: e.target.checked }))} />
          يتطلب صبغة
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
          <input type="checkbox" checked={form.notify_patient} onChange={e => setForm(p => ({ ...p, notify_patient: e.target.checked }))} />
          إرسال إشعار للمريض
        </label>
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
        <button type="button" className="btn btn-secondary" onClick={onCancel}>إلغاء</button>
        <button type="submit" className="btn btn-primary">حفظ</button>
      </div>
    </form>
  )
}
