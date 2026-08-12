import { GulaClient } from '../client';
import {
  SuggestRequest, RejectRequest, ChatRequest, ChatResponse,
  InteractionIn, InteractionOut, FeedbackIn, UnresolvedIn,
  ListResponse, PaginationParams,
} from '../types';

export class AIAPI {
  constructor(private client: GulaClient) {}

  async analyze(data: { results: { test_name: string; value?: number; value_text?: string }[] }): Promise<{ interpretations: string[]; critical_flags: string[] }> {
    return this.client.post('/ai/analyze', data);
  }

  async predict(data: { model: string; features: Record<string, unknown> }): Promise<{ prediction: unknown; confidence: number }> {
    return this.client.post('/ai/predict', data);
  }

  async diagnose(data: { symptoms: string; patient_context?: string }): Promise<{ diagnosis: string; confidence: number }> {
    return this.client.post('/ai/diagnose', data);
  }

  async recommend(data: { patient_id: number; test_codes?: string[] }): Promise<{ recommendations: string[] }> {
    return this.client.post('/ai/recommend', data);
  }

  async models(params?: PaginationParams): Promise<ListResponse<{ id: string; name: string; version: string; status: string }>> {
    return this.client.get('/ai/models', params as Record<string, unknown>);
  }

  async train(data: { model_name: string; dataset?: string }): Promise<void> {
    return this.client.post('/ai/train', data);
  }

  async interpretation(resultId: number): Promise<{ interpretation: string; confidence: number }> {
    return this.client.get(`/ai/interpretation/${resultId}`);
  }

  async validateResults(data: { result_ids: number[] }): Promise<{ valid: boolean[]; warnings: string[] }> {
    return this.client.post('/ai/validate-results', data);
  }

  async suggest(data: SuggestRequest): Promise<{ suggestion_id: string }> {
    return this.client.post<{ suggestion_id: string }>('/ai/suggest', data);
  }

  async rejectSuggestion(suggestionId: string, data: RejectRequest): Promise<void> {
    return this.client.post(`/ai/suggest/${suggestionId}/reject`, data);
  }

  async chat(data: ChatRequest): Promise<ChatResponse> {
    return this.client.post<ChatResponse>('/ai/chat', data);
  }

  // ── AI Telemetry ──
  async logInteraction(data: InteractionIn): Promise<InteractionOut> {
    return this.client.post<InteractionOut>('/api/ai/interactions', data);
  }

  async feedback(data: FeedbackIn): Promise<void> {
    return this.client.post('/api/ai/feedback', data);
  }

  async unresolved(data: UnresolvedIn): Promise<void> {
    return this.client.post('/api/ai/unresolved', data);
  }

  async telemetry(params?: PaginationParams): Promise<ListResponse<InteractionOut>> {
    return this.client.get('/ai/telemetry', params as Record<string, unknown>);
  }

  async telemetryStats(): Promise<Record<string, unknown>> {
    return this.client.get('/ai/telemetry/stats');
  }

  async telemetryModels(params?: PaginationParams): Promise<ListResponse<{ model: string; interactions: number }>> {
    return this.client.get('/ai/telemetry/models', params as Record<string, unknown>);
  }
}
