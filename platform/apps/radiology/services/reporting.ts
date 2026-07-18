import { api, type PaginatedResponse } from './api'

export type RadsScore = 'RADS-1' | 'RADS-2' | 'RADS-3' | 'RADS-4' | 'RADS-5'
  | 'BI-RADS-0' | 'BI-RADS-1' | 'BI-RADS-2' | 'BI-RADS-3' | 'BI-RADS-4' | 'BI-RADS-5' | 'BI-RADS-6'
  | 'PI-RADS-1' | 'PI-RADS-2' | 'PI-RADS-3' | 'PI-RADS-4' | 'PI-RADS-5'
  | 'LI-RADS-1' | 'LI-RADS-2' | 'LI-RADS-3' | 'LI-RADS-4' | 'LI-RADS-5'
  | 'TI-RADS-1' | 'TI-RADS-2' | 'TI-RADS-3' | 'TI-RADS-4' | 'TI-RADS-5'
  | 'NONE'

export type ReportStatus = 'draft' | 'preliminary' | 'final' | 'amended' | 'cancelled'

export type CriticalFindingSeverity = 'critical' | 'urgent' | 'significant'

export type CriticalFinding = {
  id: string
  report_id: string
  finding: string
  severity: CriticalFindingSeverity
  communicated_to: string
  communication_method: string
  communication_time: string
  acknowledged: boolean
  acknowledged_at?: string
  acknowledged_by?: string
  created_at: string
}

export type ReportFinding = {
  id: string
  type: 'normal' | 'abnormal' | 'critical'
  description: string
  location: string
  laterality: 'L' | 'R' | 'B' | 'N/A'
  severity: 'mild' | 'moderate' | 'severe'
  measurement?: {
    value: number
    unit: string
    dimension: string
  }
  rads_score?: RadsScore
  is_key_finding: boolean
}

export type RadiologyReport = {
  id: string
  study_uid: string
  accession_number: string
  patient_id: string
  patient_name: string
  report_status: ReportStatus
  report_type: 'structured' | 'narrative' | 'template'
  clinical_history: string
  technique: string
  comparison: string
  findings: ReportFinding[]
  impression: string
  conclusion: string
  recommendation: string
  rads_score: RadsScore
  critical_findings: CriticalFinding[]
  reading_physician: string
  reading_physician_id: string
  verified_by?: string
  verified_at?: string
  transcribed_by?: string
  template_id?: string
  created_at: string
  updated_at: string
}

export type ReportTemplate = {
  id: string
  name: string
  description: string
  modality: string
  body_part: string
  content: {
    technique: string
    comparison: string
    findings_template: string
    impression: string
    conclusion: string
  }
  is_public: boolean
  created_by: string
  created_at: string
  updated_at: string
}

export type ReportFilter = {
  patient_id?: string
  study_uid?: string
  status?: ReportStatus
  reading_physician_id?: string
  date_from?: string
  date_to?: string
  rads_score?: RadsScore
  has_critical_findings?: boolean
}

class ReportingService {
  async getReports(filter: ReportFilter = {}): Promise<PaginatedResponse<RadiologyReport>> {
    return api.get<PaginatedResponse<RadiologyReport>>('/radiology/reports', filter as Record<string, string | number | boolean | undefined>)
  }

  async getReport(id: string): Promise<RadiologyReport> {
    return api.get<RadiologyReport>(`/radiology/reports/${id}`)
  }

  async getReportByStudy(studyUid: string): Promise<RadiologyReport | null> {
    try {
      return await api.get<RadiologyReport>(`/radiology/reports/study/${studyUid}`)
    } catch {
      return null
    }
  }

  async createReport(data: Partial<RadiologyReport>): Promise<RadiologyReport> {
    return api.post<RadiologyReport>('/radiology/reports', data)
  }

  async updateReport(id: string, data: Partial<RadiologyReport>): Promise<RadiologyReport> {
    return api.patch<RadiologyReport>(`/radiology/reports/${id}`, data)
  }

  async submitReport(id: string): Promise<RadiologyReport> {
    return api.post<RadiologyReport>(`/radiology/reports/${id}/submit`)
  }

  async verifyReport(id: string): Promise<RadiologyReport> {
    return api.post<RadiologyReport>(`/radiology/reports/${id}/verify`)
  }

  async amendReport(id: string, data: Partial<RadiologyReport>): Promise<RadiologyReport> {
    return api.post<RadiologyReport>(`/radiology/reports/${id}/amend`, data)
  }

  async deleteReport(id: string): Promise<void> {
    return api.delete(`/radiology/reports/${id}`)
  }

  async getTemplates(modality?: string): Promise<ReportTemplate[]> {
    return api.get<ReportTemplate[]>('/radiology/reports/templates', modality ? { modality } : undefined)
  }

  async getTemplate(id: string): Promise<ReportTemplate> {
    return api.get<ReportTemplate>(`/radiology/reports/templates/${id}`)
  }

  async createTemplate(data: Partial<ReportTemplate>): Promise<ReportTemplate> {
    return api.post<ReportTemplate>('/radiology/reports/templates', data)
  }

  async updateTemplate(id: string, data: Partial<ReportTemplate>): Promise<ReportTemplate> {
    return api.patch<ReportTemplate>(`/radiology/reports/templates/${id}`, data)
  }

  async deleteTemplate(id: string): Promise<void> {
    return api.delete(`/radiology/reports/templates/${id}`)
  }

  async addCriticalFinding(reportId: string, finding: Omit<CriticalFinding, 'id' | 'report_id' | 'created_at'>): Promise<CriticalFinding> {
    return api.post<CriticalFinding>(`/radiology/reports/${reportId}/critical-findings`, finding)
  }

  async acknowledgeCriticalFinding(reportId: string, findingId: string, acknowledgedBy: string): Promise<CriticalFinding> {
    return api.post<CriticalFinding>(`/radiology/reports/${reportId}/critical-findings/${findingId}/acknowledge`, {
      acknowledged_by: acknowledgedBy
    })
  }

  async getPendingCriticalFindings(): Promise<CriticalFinding[]> {
    return api.get<CriticalFinding[]>('/radiology/reports/critical-findings/pending')
  }
}

export const reportingService = new ReportingService()
