import { apiGet, apiPost, apiPut } from './api'
import type { InventoryItem } from './inventory'

export interface Patient {
  id: string
  patient_id: string
  full_name: string
  date_of_birth: string
  gender: string
  national_id: string
  phone: string
  address: string
  allergies: string[]
  medical_conditions: string[]
  medications: string[]
}

export interface PrescriptionItem {
  id: string
  prescription_id: string
  drug_code: string
  drug_name: string
  dose: string
  dose_unit: string
  route: string
  frequency: string
  duration: string
  quantity: number
  refills_remaining: number
  instructions: string
  dispensed_quantity: number | null
  is_controlled: boolean
}

export interface Prescription {
  id: string
  prescription_number: string
  patient_id: string
  patient_name: string
  doctor_name: string
  doctor_license: string
  facility: string
  issue_date: string
  expiry_date: string
  status: string
  items: PrescriptionItem[]
  notes: string
  is_stat: boolean
  is_controlled: boolean
}

export interface DispensingRecord {
  id: string
  prescription_id: string
  patient_id: string
  patient_name: string
  pharmacist_name: string
  pharmacist_id: string
  items: {
    item_id: string
    drug_name: string
    quantity: number
    batch_number: string
    verified: boolean
  }[]
  status: string
  barcode_verified: boolean
  clinical_check: boolean
  notes: string
  dispensed_at: string
}

export interface DispenseRequest {
  prescription_id: string
  patient_id: string
  pharmacist_id: string
  items: {
    inventory_id: string
    quantity: number
    batch_number: string
  }[]
  notes?: string
}

export async function getPrescriptions(params?: {
  status?: string
  patient_id?: string
  page?: number
  page_size?: number
}) {
  const query = new URLSearchParams()
  if (params?.status) query.set('status', params.status)
  if (params?.patient_id) query.set('patient_id', params.patient_id)
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

export async function dispensePrescription(data: DispenseRequest) {
  return apiPost<DispensingRecord>('/pharmacy/dispensing', data)
}

export async function verifyDispensing(
  dispensingId: string,
  verification: {
    barcode_verified: boolean
    clinical_check: boolean
    pharmacist_signature: string
  },
) {
  return apiPut<DispensingRecord>(
    `/pharmacy/dispensing/${dispensingId}/verify`,
    verification,
  )
}

export async function getDispensingHistory(
  params?: {
    patient_id?: string
    date_from?: string
    date_to?: string
    page?: number
    page_size?: number
  },
) {
  const query = new URLSearchParams()
  if (params?.patient_id) query.set('patient_id', params.patient_id)
  if (params?.date_from) query.set('date_from', params.date_from)
  if (params?.date_to) query.set('date_to', params.date_to)
  if (params?.page) query.set('page', String(params.page))
  if (params?.page_size) query.set('page_size', String(params.page_size))
  const qs = query.toString()
  return apiGet<{ records: DispensingRecord[]; total: number }>(
    `/pharmacy/dispensing${qs ? `?${qs}` : ''}`,
  )
}

export async function searchPatients(query: string) {
  return apiGet<{ patients: Patient[] }>(`/pharmacy/patients/search?q=${encodeURIComponent(query)}`)
}

export async function getPatient(id: string) {
  return apiGet<Patient>(`/pharmacy/patients/${id}`)
}

export async function getPatientPrescriptions(patientId: string) {
  return apiGet<{ prescriptions: Prescription[] }>(
    `/pharmacy/patients/${patientId}/prescriptions`,
  )
}

export async function reverseDispensing(dispensingId: string, reason: string) {
  return apiPost(`/pharmacy/dispensing/${dispensingId}/reverse`, { reason })
}
