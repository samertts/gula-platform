import { api, type PaginatedResponse } from './api'
import type { WorklistItem } from './worklist'
import type { Modality } from './dicom'

export type AppointmentStatus = 'scheduled' | 'confirmed' | 'arrived' | 'in_progress' | 'completed' | 'missed' | 'cancelled'

export type Appointment = {
  id: string
  patient_id: string
  patient_name: string
  patient_phone: string
  study_description: string
  modality: Modality
  procedure_code: string
  procedure_description: string
  referring_physician: string
  referring_department: string
  scheduled_date: string
  scheduled_time: string
  duration_minutes: number
  room: string
  station: string
  status: AppointmentStatus
  notes: string
  contrast_required: boolean
  contrast_details: string
  notify_patient: boolean
  notification_sent: boolean
  worklist_item_id?: string
  created_by: string
  created_at: string
  updated_at: string
}

export type ScheduleSlot = {
  id: string
  date: string
  start_time: string
  end_time: string
  room: string
  station: string
  modality: Modality
  available: boolean
  appointment_id?: string
}

export type ScheduleBlock = {
  id: string
  date: string
  start_time: string
  end_time: string
  reason: string
  room: string
  station: string
}

export type Room = {
  id: string
  name: string
  modality: Modality
  stations: string[]
  active: boolean
}

class SchedulingService {
  async getAppointments(params: {
    date_from?: string
    date_to?: string
    patient_id?: string
    modality?: Modality
    status?: AppointmentStatus
  } = {}): Promise<PaginatedResponse<Appointment>> {
    return api.get<PaginatedResponse<Appointment>>('/radiology/scheduling/appointments', params as Record<string, string | number | boolean | undefined>)
  }

  async getAppointment(id: string): Promise<Appointment> {
    return api.get<Appointment>(`/radiology/scheduling/appointments/${id}`)
  }

  async createAppointment(data: Omit<Appointment, 'id' | 'created_at' | 'updated_at'>): Promise<Appointment> {
    return api.post<Appointment>('/radiology/scheduling/appointments', data)
  }

  async updateAppointment(id: string, data: Partial<Appointment>): Promise<Appointment> {
    return api.patch<Appointment>(`/radiology/scheduling/appointments/${id}`, data)
  }

  async cancelAppointment(id: string, reason?: string): Promise<Appointment> {
    return api.post<Appointment>(`/radiology/scheduling/appointments/${id}/cancel`, { reason })
  }

  async confirmAppointment(id: string): Promise<Appointment> {
    return api.post<Appointment>(`/radiology/scheduling/appointments/${id}/confirm`)
  }

  async markNoShow(id: string): Promise<Appointment> {
    return api.post<Appointment>(`/radiology/scheduling/appointments/${id}/no-show`)
  }

  async convertToWorklist(id: string): Promise<WorklistItem> {
    return api.post<WorklistItem>(`/radiology/scheduling/appointments/${id}/convert-to-worklist`)
  }

  async getAvailableSlots(date: string, modality: Modality): Promise<ScheduleSlot[]> {
    return api.get<ScheduleSlot[]>('/radiology/scheduling/slots', { date, modality })
  }

  async createBlock(block: Omit<ScheduleBlock, 'id'>): Promise<ScheduleBlock> {
    return api.post<ScheduleBlock>('/radiology/scheduling/blocks', block)
  }

  async deleteBlock(id: string): Promise<void> {
    return api.delete(`/radiology/scheduling/blocks/${id}`)
  }

  async getRooms(): Promise<Room[]> {
    return api.get<Room[]>('/radiology/scheduling/rooms')
  }

  async getSchedule(date: string): Promise<Appointment[]> {
    return api.get<Appointment[]>('/radiology/scheduling/calendar', { date })
  }

  async sendReminder(appointmentId: string): Promise<void> {
    return api.post(`/radiology/scheduling/appointments/${appointmentId}/send-reminder`)
  }
}

export const schedulingService = new SchedulingService()
