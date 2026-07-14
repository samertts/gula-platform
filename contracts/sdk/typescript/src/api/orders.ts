import { GulaClient } from '../client';
import {
  CreateOrderRequest, OrderResponse, AnalyzeRequest, AnalyzeResponse,
  BatchOrderRequest, BatchOrderResponse, ListResponse, PaginationParams,
} from '../types';

export class OrdersAPI {
  constructor(private client: GulaClient) {}

  async create(data: CreateOrderRequest): Promise<OrderResponse> {
    return this.client.post<OrderResponse>('/orders', data);
  }

  async get(id: number): Promise<OrderResponse> {
    return this.client.get<OrderResponse>(`/orders/${id}`);
  }

  async list(params?: PaginationParams & { patient_id?: number; status?: string }): Promise<ListResponse<OrderResponse>> {
    return this.client.get<ListResponse<OrderResponse>>('/orders', params as Record<string, unknown>);
  }

  async cancel(id: number): Promise<OrderResponse> {
    return this.client.post<OrderResponse>(`/orders/${id}/cancel`);
  }

  async analyze(data: AnalyzeRequest): Promise<AnalyzeResponse> {
    return this.client.post<AnalyzeResponse>('/analyze', data);
  }

  async createBatch(data: BatchOrderRequest): Promise<BatchOrderResponse> {
    return this.client.post<BatchOrderResponse>('/batch/orders', data);
  }
}
