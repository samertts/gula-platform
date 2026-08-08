import { apiGet, apiPost } from './api'

export interface DrugInteraction {
  id: string
  drug_a: string
  drug_b: string
  drug_a_name: string
  drug_b_name: string
  severity: 'contraindicated' | 'severe' | 'moderate' | 'minor'
  mechanism: string
  effect: string
  recommendation: string
  evidence_level: string
  references: string[]
}

export interface DrugAllergy {
  id: string
  drug: string
  drug_name: string
  allergen: string
  reaction: string
  severity: string
}

export interface DrugFoodInteraction {
  id: string
  drug: string
  drug_name: string
  food: string
  effect: string
  recommendation: string
  severity: string
}

export interface InteractionCheckResult {
  interactions: DrugInteraction[]
  allergies: DrugAllergy[]
  food_interactions: DrugFoodInteraction[]
  duplicate_therapy: string[]
  risk_score: number
  summary: string
}

export interface DrugInfo {
  drug_code: string
  drug_name: string
  generic_name: string
  drug_class: string
  indications: string[]
  contraindications: string[]
  side_effects: string[]
  pregnancy_category: string
  metabolism: string
  half_life: string
  excretion: string
  monitoring: string[]
  patient_counseling: string[]
}

export async function checkInteractions(
  drugCodes: string[],
  patientId?: string,
  allergies?: string[],
) {
  return apiPost<InteractionCheckResult>('/pharmacy/interactions/check', {
    drug_codes: drugCodes,
    patient_id: patientId,
    allergies,
  })
}

export async function getDrugInfo(drugCode: string) {
  return apiGet<DrugInfo>(`/pharmacy/drugs/${drugCode}`)
}

export async function searchDrugs(query: string) {
  return apiGet<{ drugs: DrugInfo[] }>(
    `/pharmacy/drugs/search?q=${encodeURIComponent(query)}`,
  )
}

export async function getDrugInteractions(drugCode: string) {
  return apiGet<{ interactions: DrugInteraction[] }>(
    `/pharmacy/drugs/${drugCode}/interactions`,
  )
}

export async function getAllergies(patientId: string) {
  return apiGet<{ allergies: DrugAllergy[] }>(
    `/pharmacy/patients/${patientId}/allergies`,
  )
}

export async function addDrugAllergy(patientId: string, data: {
  drug_code: string
  allergen: string
  reaction: string
  severity: string
}) {
  return apiPost(`/pharmacy/patients/${patientId}/allergies`, data)
}
