import { api, type PaginatedResponse } from './api'

export type Modality = 'CT' | 'MR' | 'US' | 'XA' | 'CR' | 'DX' | 'MG' | 'NM' | 'PT' | 'OT'

export type StudyStatus = 'scheduled' | 'in_progress' | 'completed' | 'verified' | 'reported'

export type StudySeries = {
  series_uid: string
  series_number: number
  series_description: string
  modality: Modality
  number_of_instances: number
  body_part: string
  laterality: 'L' | 'R' | 'U'
  series_date: string
  series_time: string
  institution: string
  station_name: string
}

export type DicomStudy = {
  study_uid: string
  accession_number: string
  patient_id: string
  patient_name: string
  patient_birth_date: string
  patient_sex: 'M' | 'F' | 'O'
  study_date: string
  study_time: string
  study_description: string
  referring_physician: string
  reading_physician: string
  modality: Modality
  status: StudyStatus
  number_of_series: number
  number_of_instances: number
  institution: string
  department: string
  series: StudySeries[]
  has_ai_annotations: boolean
  created_at: string
  updated_at: string
}

export type QidoParams = {
  patient_id?: string
  patient_name?: string
  accession_number?: string
  study_date_from?: string
  study_date_to?: string
  modality?: Modality
  study_description?: string
  limit?: number
  offset?: number
}

class DicomService {
  private wadoUrl: string
  private qidoUrl: string
  private stowUrl: string

  constructor() {
    const base = import.meta.env.VITE_DICOM_URL || '/dicom'
    this.wadoUrl = `${base}/wado-rs`
    this.qidoUrl = `${base}/qido-rs`
    this.stowUrl = `${base}/stow-rs`
  }

  async searchStudies(params: QidoParams): Promise<PaginatedResponse<DicomStudy>> {
    return api.get<PaginatedResponse<DicomStudy>>('/radiology/studies', params as Record<string, string | number | boolean | undefined>)
  }

  async getStudy(studyUid: string): Promise<DicomStudy> {
    return api.get<DicomStudy>(`/radiology/studies/${studyUid}`)
  }

  async getSeries(studyUid: string): Promise<StudySeries[]> {
    return api.get<StudySeries[]>(`/radiology/studies/${studyUid}/series`)
  }

  getWadoUri(studyUid: string, seriesUid: string, instanceUid: string): string {
    return `${this.wadoUrl}/studies/${studyUid}/series/${seriesUid}/instances/${instanceUid}`
  }

  getWadoFramesUri(studyUid: string, seriesUid: string, instanceUid: string, frameNumbers: number[]): string {
    const frames = frameNumbers.join(',')
    return `${this.wadoUrl}/studies/${studyUid}/series/${seriesUid}/instances/${instanceUid}/frames/${frames}`
  }

  getThumbnailUri(studyUid: string, seriesUid: string, instanceUid: string): string {
    return `${this.wadoUrl}/studies/${studyUid}/series/${seriesUid}/instances/${instanceUid}/thumbnail`
  }

  async retrieveInstance(studyUid: string, seriesUid: string, instanceUid: string): Promise<ArrayBuffer> {
    const response = await fetch(this.getWadoUri(studyUid, seriesUid, instanceUid), {
      headers: {
        'Accept': 'application/dicom'
      }
    })
    if (!response.ok) throw new Error(`Failed to retrieve DICOM instance: ${response.statusText}`)
    return response.arrayBuffer()
  }

  async storeInstances(studyUid: string, dicomFiles: ArrayBuffer[]): Promise<{ status: string; study_uid: string }> {
    const formData = new FormData()
    dicomFiles.forEach((file, index) => {
      formData.append(`instance_${index}`, new Blob([file], { type: 'application/dicom' }))
    })
    return api.upload<{ status: string; study_uid: string }>(`/radiology/studies/${studyUid}/instances`, formData)
  }

  async deleteStudy(studyUid: string): Promise<void> {
    return api.delete(`/radiology/studies/${studyUid}`)
  }

  async updateStudy(studyUid: string, data: Partial<DicomStudy>): Promise<DicomStudy> {
    return api.patch<DicomStudy>(`/radiology/studies/${studyUid}`, data)
  }

  async getStudyMetadata(studyUid: string): Promise<Record<string, unknown>> {
    return api.get<Record<string, unknown>>(`/radiology/studies/${studyUid}/metadata`)
  }

  async getSeriesMetadata(studyUid: string, seriesUid: string): Promise<Record<string, unknown>> {
    return api.get<Record<string, unknown>>(`/radiology/studies/${studyUid}/series/${seriesUid}/metadata`)
  }
}

export const dicomService = new DicomService()
