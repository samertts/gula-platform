import { createApiClient } from '@gula/ui-platform';

const backend = createApiClient({
  baseUrl: import.meta.env.VITE_API_BASE_URL || 'https://api.gula.health/api/v1',
  clientName: 'citizen-guide-assistant',
  refreshPath: '/auth/refresh',
});

export interface GuideAssistantResponse {
  response: string;
  model: string;
}

export async function askGuideAssistant(prompt: string): Promise<GuideAssistantResponse> {
  const normalizedPrompt = prompt.trim();
  if (!normalizedPrompt) throw new Error('اكتب سؤالك أولاً.');
  return backend.request<GuideAssistantResponse>('/ai/fabric/chat', {
    method: 'POST',
    query: {
      prompt: normalizedPrompt,
      model: 'gpt-4o-mini',
      temperature: 0.2,
    },
  });
}
