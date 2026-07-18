import { apiGet, apiPost, apiPut } from './api'

export interface Prescription {
  id: string
  prescription_number: string
  patient_id: string
  patient_name: string
  patient_dob: string
  doctor_name: string
  doctor_license: string
  facility: string
  issue_date: string
  expiry_date: string
  status: 'pending' | 'verified' | 'in_progress' | 'dispensed' | 'partially_dispensed' | 'cancelled' | 'expired'
  items: PrescriptionItem[]
  notes: string
  is_stat: boolean
  is_controlled: boolean
  clinical_notes: string
  pharmacist_notes: string
  created_at: string
  updated_at: string
}

export interface PrescriptionItem {
  id: string
  drug_code: string
  drug_name: string
  generic_name: string
  strength: string
  dosage_form: string
  dose: string
  dose_unit: string
  route: string
  frequency: string
  duration: string
  quantity: number
  quantity_dispensed: number
  refills: number
  refills_remaining: number
  instructions: string
  substitution_allowed: boolean
  is_controlled: boolean
  status: string
}

export interface PrescriptionCreate {
  patient_id: string
  doctor_name: string
  doctor_license: string
  facility: string
  items: {
    drug_code: string
    dose: string
    dose_unit: string
    route: string
    frequency: string
    duration: string
    quantity: number
    refills: number
    instructions: string
    substitution_allowed: boolean
  }[]
  notes?: string
  clinical_notes?: string
  is_stat?: boolean
}

export async function getPrescriptions(params?: {
  status?: string
  patient_id?: string
  date_from?: string
  date_to?: string
  page?: number
  page_size?: number
}) {
  const query = new URLSearchParams()
  if (params?.status) query.set('status', params.status)
  if (params?.patient_id) query.set('patient_id', params.patient_id)
  if (params?.date_from) query.set('date_from', params.date_from)
  if (params?.date_to) query.set('date_to', params.date_to)
  if (params?.page) query.set('page', String(params.page))
  if (params?.page_size) query.set('page_size', String(params.page_size))
  const qs = query.toString()
  return apiGet<{ prescriptions: Prescription[]; total: number }>(
    `/pharmacy/prescriptions${qs ? `?${qs}` : ''}`,
  )
}

export async function getPrescription(id: string) {
  return apiGet<Prescription>(`/pharmacy/prescriptions/${id}`)
}

export async function createPrescription(data: PrescriptionCreate) {
  return apiPost<Prescription>('/pharmacy/prescriptions', data)
}

export async function updatePrescriptionStatus(id: string, status: string) {
  return apiPut<Prescription>(`/pharmacy/prescriptions/${id}/status`, { status })
}

export async function cancelPrescription(id: string, reason: string) {
  return apiPut<Prescription>(`/pharmacy/prescriptions/${id}/cancel`, { reason })
}

export async function getPrescriptionsByPatient(patientId: string) {
  return apiGet<{ prescriptions: Prescription[] }>(
    `/pharmacy/patients/${patientId}/prescriptions`,
  )
}
