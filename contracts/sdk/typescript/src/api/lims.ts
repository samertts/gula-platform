import { GulaClient } from '../client';
import {
  SpecimenRegisterRequest, SpecimenTransitionRequest,
  LimsOrderCreateRequest, LimsResultCreateRequest, ResultValidateRequest,
  IQCRunRequest, InstrumentCreateRequest, InstrumentResponse,
  MaintenanceRecordRequest, CalibrationRecordRequest,
  InventoryRequest, InventoryItem, ReportGenerateRequest,
  DeviceMessageRequest, ASTMResultResponse, QCProgram,
  ListResponse, PaginationParams,
} from '../types';

export class LIMSAPI {
  constructor(private client: GulaClient) {}

  // ── Specimens ──
  async registerSpecimen(data: SpecimenRegisterRequest): Promise<{ id: number; barcode: string }> {
    return this.client.post('/lims/specimens', data);
  }

  async transitionSpecimen(id: number, data: SpecimenTransitionRequest): Promise<void> {
    return this.client.post(`/lims/specimens/${id}/transition`, data);
  }

  // ── Orders ──
  async createLimsOrder(data: LimsOrderCreateRequest): Promise<{ id: number; accession_number: string }> {
    return this.client.post('/lims/orders', data);
  }

  // ── Results ──
  async createLimsResult(data: LimsResultCreateRequest): Promise<{ id: number }> {
    return this.client.post('/lims/results', data);
  }

  async validateLimsResult(id: number, data: ResultValidateRequest): Promise<void> {
    return this.client.post(`/lims/results/${id}/validate`, data);
  }

  // ── QC ──
  async createQCRun(data: IQCRunRequest): Promise<{ id: number }> {
    return this.client.post('/lims/qc/runs', data);
  }

  async listQCPrograms(params?: PaginationParams): Promise<ListResponse<QCProgram>> {
    return this.client.get('/lims/qc/programs', params as Record<string, unknown>);
  }

  // ── Instruments ──
  async createInstrument(data: InstrumentCreateRequest): Promise<InstrumentResponse> {
    return this.client.post<InstrumentResponse>('/lims/instruments', data);
  }

  async listInstruments(params?: PaginationParams): Promise<ListResponse<InstrumentResponse>> {
    return this.client.get<ListResponse<InstrumentResponse>>('/lims/instruments', params as Record<string, unknown>);
  }

  async getInstrument(id: number): Promise<InstrumentResponse> {
    return this.client.get<InstrumentResponse>(`/lims/instruments/${id}`);
  }

  async updateInstrument(id: number, data: Partial<InstrumentCreateRequest>): Promise<InstrumentResponse> {
    return this.client.put<InstrumentResponse>(`/lims/instruments/${id}`, data);
  }

  async addMaintenance(instrumentId: number, data: MaintenanceRecordRequest): Promise<void> {
    return this.client.post(`/lims/instruments/${instrumentId}/maintenance`, data);
  }

  async addCalibration(instrumentId: number, data: CalibrationRecordRequest): Promise<void> {
    return this.client.post(`/lims/instruments/${instrumentId}/calibrations`, data);
  }

  // ── Inventory ──
  async upsertInventory(data: InventoryRequest): Promise<InventoryItem> {
    return this.client.post<InventoryItem>('/lims/inventory', data);
  }

  async listInventory(params?: PaginationParams): Promise<ListResponse<InventoryItem>> {
    return this.client.get<ListResponse<InventoryItem>>('/lims/inventory', params as Record<string, unknown>);
  }

  async getInventoryItem(id: number): Promise<InventoryItem> {
    return this.client.get<InventoryItem>(`/lims/inventory/${id}`);
  }

  // ── Reports ──
  async generateReport(data: ReportGenerateRequest): Promise<{ report_url: string }> {
    return this.client.post('/lims/reports', data);
  }

  // ── Device Messages ──
  async submitDeviceMessage(data: DeviceMessageRequest): Promise<{ parsed: ASTMResultResponse[] }> {
    return this.client.post('/lims/devices/message', data);
  }
}
