import { GulaClient } from '../client';
import {
  TestResultCreate, TestResultRead, TestResultBrief, TestResultForCitizen,
  TestResultValidateRequest, DeviceSubmission, DeviceSubmissionResponse,
  ListResponse, PaginationParams, ResultAmendment,
} from '../types';

export class ResultsAPI {
  constructor(private client: GulaClient) {}

  async list(params?: PaginationParams & { patient_id?: number; status?: string; is_critical?: boolean }): Promise<ListResponse<TestResultRead>> {
    return this.client.get<ListResponse<TestResultRead>>('/results', params as Record<string, unknown>);
  }

  async get(id: number): Promise<TestResultRead> {
    return this.client.get<TestResultRead>(`/results/${id}`);
  }

  async create(data: TestResultCreate): Promise<TestResultRead> {
    return this.client.post<TestResultRead>('/results', data);
  }

  async update(id: number, data: Partial<TestResultCreate>): Promise<TestResultRead> {
    return this.client.put<TestResultRead>(`/results/${id}`, data);
  }

  async delete(id: number): Promise<void> {
    return this.client.delete(`/results/${id}`);
  }

  async verify(id: number): Promise<TestResultRead> {
    return this.client.put<TestResultRead>(`/results/${id}/verify`);
  }

  async approve(id: number): Promise<TestResultRead> {
    return this.client.put<TestResultRead>(`/results/${id}/approve`);
  }

  async validate(id: number, data: { notes?: string; signature_hash?: string }): Promise<TestResultRead> {
    return this.client.put<TestResultRead>(`/results/${id}/validate`, data);
  }

  async bulkCreate(data: TestResultCreate[]): Promise<{ created: number }> {
    return this.client.post('/results/bulk', data);
  }

  async autoValidate(data: { lab_id: number }): Promise<{ validated: number }> {
    return this.client.post('/results/auto-validate', data);
  }

  async amend(id: number, data: { reason: string; value?: number; value_text?: string }): Promise<TestResultRead> {
    return this.client.post<TestResultRead>(`/results/${id}/amend`, data);
  }

  async getAmendments(id: number, params?: PaginationParams): Promise<ListResponse<ResultAmendment>> {
    return this.client.get<ListResponse<ResultAmendment>>(`/results/${id}/amendments`, params as Record<string, unknown>);
  }

  async stats(): Promise<Record<string, unknown>> {
    return this.client.get('/results/stats');
  }

  async print(id: number): Promise<void> {
    return this.client.post(`/results/${id}/print`);
  }

  async sendToPatient(data: { result_id: number; channel: 'whatsapp' | 'sms' }): Promise<void> {
    return this.client.post('/results/send-to-patient', data);
  }

  async timeline(id: number): Promise<{ status: string; timestamp: string; user: string }[]> {
    return this.client.get(`/results/${id}/timeline`);
  }

  async flagCritical(id: number): Promise<TestResultRead> {
    return this.client.post<TestResultRead>(`/results/${id}/flag-critical`);
  }

  async generateReport(id: number): Promise<{ report_url: string }> {
    return this.client.post(`/results/${id}/report`);
  }

  async listReports(params?: PaginationParams): Promise<ListResponse<{ id: number; name: string; url: string }>> {
    return this.client.get('/results/reports', params as Record<string, unknown>);
  }

  // ── Test Results (citizen-centric) ──
  async createTestResult(data: { health_id: string; test_name: string; test_code?: string; value?: number; value_text?: string; unit?: string; normal_range_low?: number; normal_range_high?: number; sample_type?: string; doctor_name?: string; order_id?: number }): Promise<TestResultRead> {
    return this.client.post<TestResultRead>('/test-results', data);
  }

  async getTestResult(id: number): Promise<TestResultRead> {
    return this.client.get<TestResultRead>(`/test-results/${id}`);
  }

  async listTestResults(params?: PaginationParams): Promise<ListResponse<TestResultBrief>> {
    return this.client.get<ListResponse<TestResultBrief>>('/test-results', params as Record<string, unknown>);
  }

  async getCitizenResults(healthId: string): Promise<TestResultForCitizen[]> {
    return this.client.get<TestResultForCitizen[]>(`/test-results/citizen/${healthId}`);
  }

  async validateTestResult(data: TestResultValidateRequest): Promise<{ warnings: string[] }> {
    return this.client.post('/test-results/validate', data);
  }

  async bulkApproveTestResults(data: { ids: number[] }): Promise<{ approved: number }> {
    return this.client.post('/test-results/bulk-approve', data);
  }

  async exportTestResultPdf(id: number): Promise<Blob> {
    return this.client.download(`/test-results/export-pdf/${id}`, `result-${id}.pdf`);
  }

  async importTestResultsCsv(file: File): Promise<{ imported: number }> {
    const fd = new FormData();
    fd.append('file', file);
    return this.client.upload('/test-results/import-csv', fd);
  }

  async deviceSubmit(data: DeviceSubmission): Promise<DeviceSubmissionResponse> {
    return this.client.post<DeviceSubmissionResponse>('/device/results', data);
  }

  async listDeviceResults(params?: PaginationParams): Promise<ListResponse<TestResultRead>> {
    return this.client.get<ListResponse<TestResultRead>>('/device-results', params as Record<string, unknown>);
  }
}
