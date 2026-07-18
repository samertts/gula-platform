import { api, type PaginatedResponse } from './api'
import type { Modality, StudyStatus } from './dicom'

export type WorklistStatus = 'scheduled' | 'arrived' | 'started' | 'completed' | 'cancelled'

export type WorklistItem = {
  id: string
  accession_number: string
  patient_id: string
  patient_name: string
  patient_birth_date: string
  patient_sex: 'M' | 'F' | 'O'
  patient_age: string
  modality: Modality
  study_description: string
  procedure_code: string
  procedure_description: string
  requesting_physician: string
  requesting_department: string
  scheduled_date: string
  scheduled_time: string
  scheduled_station: string
  scheduled_aet: string
  status: WorklistStatus
  priority: 'routine' | 'urgent' | 'stat'
  duration_minutes: number
  contrast_required: boolean
  contrast_details?: string
  notes?: string
  arrival_time?: string
  start_time?: string
  completion_time?: string
  performed_by?: string
  created_at: string
  updated_at: string
}

export type WorklistFilter = {
  date_from?: string
  date_to?: string
  modality?: Modality
  status?: WorklistStatus
  station?: string
  patient_name?: string
  priority?: string
}

class WorklistService {
  async getWorklist(filter: WorklistFilter = {}): Promise<PaginatedResponse<WorklistItem>> {
    return api.get<PaginatedResponse<WorklistItem>>('/radiology/worklist', filter as Record<string, string | number | boolean | undefined>)
  }

  async getWorklistItem(id: string): Promise<WorklistItem> {
    return api.get<WorklistItem>(`/radiology/worklist/${id}`)
  }

  async updateWorklistStatus(id: string, status: WorklistStatus, data?: Partial<WorklistItem>): Promise<WorklistItem> {
    return api.patch<WorklistItem>(`/radiology/worklist/${id}`, { status, ...data })
  }

  async markArrived(id: string, arrivalTime?: string): Promise<WorklistItem> {
    return this.updateWorklistStatus(id, 'arrived', {
      arrival_time: arrivalTime || new Date().toISOString()
    })
  }

  async markStarted(id: string): Promise<WorklistItem> {
    return this.updateWorklistStatus(id, 'started', {
      start_time: new Date().toISOString()
    })
  }

  async markCompleted(id: string, performedBy: string): Promise<WorklistItem> {
    return this.updateWorklistStatus(id, 'completed', {
      completion_time: new Date().toISOString(),
      performed_by: performedBy
    })
  }

  async cancelWorklistItem(id: string, reason?: string): Promise<WorklistItem> {
    return this.updateWorklistStatus(id, 'cancelled', {
      notes: reason ? `Cancelled: ${reason}` : 'Cancelled'
    })
  }

  async getModalityWorklist(modality: Modality, station: string, date?: string): Promise<WorklistItem[]> {
    return api.get<WorklistItem[]>(`/radiology/worklist/modality/${modality}`, {
      station,
      date: date || new Date().toISOString().split('T')[0]
    })
  }

  async createWorklistItem(item: Omit<WorklistItem, 'id' | 'created_at' | 'updated_at'>): Promise<WorklistItem> {
    return api.post<WorklistItem>('/radiology/worklist', item)
  }

  async getStats(): Promise<{
    scheduled: number
    in_progress: number
    completed_today: number
    cancelled: number
    avg_wait_time_minutes: number
  }> {
    return api.get('/radiology/worklist/stats') as Promise<{
      scheduled: number
      in_progress: number
      completed_today: number
      cancelled: number
      avg_wait_time_minutes: number
    }>
  }
}

export const worklistService = new WorklistService()
